"""
Intelligent role matching service for matching candidates to job roles.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import Role, UserProfile, RoleMatchHistory

logger = logging.getLogger(__name__)

class RoleMatchingService:
    """Service for intelligent role matching based on skills and experience."""
    
    # Experience level hierarchy for comparison
    EXPERIENCE_LEVELS = {
        "intern": 0,
        "junior": 1, 
        "mid": 2,
        "senior": 3,
        "lead": 4,
        "principal": 5
    }
    
    # Skill level hierarchy for comparison
    SKILL_LEVELS = {
        "beginner": 0,
        "junior": 1,
        "mid": 2, 
        "senior": 3,
        "expert": 4
    }
    
    @classmethod
    def calculate_role_match(cls, user_profile: UserProfile, role: Role) -> Dict[str, Any]:
        """Calculate comprehensive match score between user and role."""
        
        # Extract user data
        user_skills = user_profile.skills or {}
        user_level = user_profile.overall_experience_level or "junior"
        user_years = user_profile.total_years_experience or 0
        user_preferences = user_profile.preferred_experience_levels or []
        user_categories = user_profile.category_preferences or []
        
        # Extract role data
        role_skills = role.required_skills or {}
        role_level = role.required_experience_level or "mid"
        role_years_min = role.required_years_min or 0
        role_years_max = role.required_years_max or 50
        role_category = role.category
        
        # Calculate individual match components
        experience_match = cls._calculate_experience_match(
            user_level, user_years, user_preferences,
            role_level, role_years_min, role_years_max
        )
        
        skills_match = cls._calculate_skills_match(user_skills, role_skills)
        
        category_match = cls._calculate_category_match(user_categories, role_category)
        
        location_match = cls._calculate_location_match(user_profile, role)
        
        # Calculate weighted overall score
        overall_score = (
            experience_match["score"] * 0.35 +  # 35% experience match
            skills_match["score"] * 0.40 +      # 40% skills match  
            category_match["score"] * 0.15 +    # 15% category preference
            location_match["score"] * 0.10      # 10% location preference
        )
        
        # Determine recommendation level
        recommendation = cls._get_recommendation_level(
            overall_score, 
            skills_match["missing_required_skills"],
            experience_match["level_gap"]
        )
        
        # Generate explanatory reasons
        reasons = cls._generate_match_reasons(
            user_profile, role, experience_match, skills_match, 
            category_match, location_match
        )
        
        return {
            "overall_score": round(overall_score, 3),
            "recommendation": recommendation,
            "match_details": {
                "experience": experience_match,
                "skills": skills_match,
                "category": category_match,
                "location": location_match
            },
            "reasons": reasons,
            "calculated_at": datetime.utcnow().isoformat()
        }
    
    @classmethod
    def _calculate_experience_match(
        cls, 
        user_level: str, user_years: int, user_preferences: List[str],
        role_level: str, role_years_min: int, role_years_max: int
    ) -> Dict[str, Any]:
        """Calculate experience level and years match."""
        
        user_level_num = cls.EXPERIENCE_LEVELS.get(user_level, 1)
        role_level_num = cls.EXPERIENCE_LEVELS.get(role_level, 2)
        
        # Experience level match
        level_gap = user_level_num - role_level_num
        
        if level_gap == 0:
            level_score = 1.0  # Perfect match
        elif level_gap == 1:
            level_score = 0.8  # Slightly overqualified
        elif level_gap == -1:
            level_score = 0.7  # Slightly underqualified but possible
        elif level_gap >= 2:
            # Significantly overqualified - penalize more for bigger gaps
            level_score = max(0.2, 0.8 - (level_gap - 1) * 0.2)
        else:
            # Significantly underqualified
            level_score = max(0.1, 0.7 + level_gap * 0.2)
        
        # Years experience match
        years_score = 1.0
        if user_years < role_years_min:
            # Not enough experience
            years_shortage = role_years_min - user_years
            years_score = max(0.2, 1.0 - years_shortage * 0.1)
        elif user_years > role_years_max and role_years_max > 0:
            # Too much experience (overqualified)
            years_excess = user_years - role_years_max
            years_score = max(0.3, 1.0 - years_excess * 0.05)
        
        # User preference bonus
        preference_bonus = 0.0
        if user_preferences and role_level in user_preferences:
            preference_bonus = 0.1  # 10% bonus for preferred level
        
        # Combined experience score
        experience_score = (level_score * 0.7 + years_score * 0.3) + preference_bonus
        experience_score = min(1.0, experience_score)  # Cap at 1.0
        
        return {
            "score": experience_score,
            "level_gap": level_gap,
            "user_level": user_level,
            "role_level": role_level,
            "years_match": years_score,
            "preference_bonus": preference_bonus > 0
        }
    
    @classmethod
    def _calculate_skills_match(
        cls, user_skills: Dict[str, Any], role_skills: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate skills match with detailed breakdown."""
        
        if not role_skills:
            return {"score": 0.8, "missing_required_skills": [], "skill_matches": []}
        
        skill_matches = []
        missing_required_skills = []
        bonus_skills = []
        
        # Check each required skill
        for skill_name, skill_req in role_skills.items():
            skill_name_clean = skill_name.lower().strip()
            user_skill = user_skills.get(skill_name_clean, {})
            
            required = skill_req.get("required", False)
            req_level = skill_req.get("level", "mid")
            req_years = skill_req.get("years", 0)
            
            if not user_skill:
                # User doesn't have this skill
                if required:
                    missing_required_skills.append(skill_name)
                    skill_matches.append({
                        "skill": skill_name,
                        "score": 0.0,
                        "required": True,
                        "missing": True
                    })
                else:
                    skill_matches.append({
                        "skill": skill_name,
                        "score": 0.0,
                        "required": False,
                        "missing": True
                    })
                continue
            
            # User has this skill - compare levels
            user_level = user_skill.get("level", "beginner")
            user_years = user_skill.get("years", 0)
            confidence = user_skill.get("confidence", 0.8)
            
            user_level_num = cls.SKILL_LEVELS.get(user_level, 0)
            req_level_num = cls.SKILL_LEVELS.get(req_level, 2)
            
            # Calculate skill level match
            if user_level_num >= req_level_num:
                # User meets or exceeds skill level requirement
                level_match = 1.0
                if user_level_num > req_level_num:
                    # Bonus for exceeding (but not too much)
                    level_match = min(1.2, 1.0 + (user_level_num - req_level_num) * 0.1)
            else:
                # User below required level
                level_match = max(0.2, user_level_num / req_level_num)
            
            # Calculate years match
            years_match = 1.0
            if user_years < req_years:
                years_shortage = req_years - user_years
                years_match = max(0.3, 1.0 - years_shortage * 0.1)
            
            # Apply confidence factor
            skill_score = (level_match * 0.7 + years_match * 0.3) * confidence
            
            skill_matches.append({
                "skill": skill_name,
                "score": round(skill_score, 3),
                "required": required,
                "level_match": level_match,
                "years_match": years_match,
                "confidence": confidence,
                "user_level": user_level,
                "required_level": req_level
            })
        
        # Find bonus skills (user has skills not required by role)
        user_skill_names = set(user_skills.keys())
        role_skill_names = set(s.lower().strip() for s in role_skills.keys())
        bonus_skill_names = user_skill_names - role_skill_names
        
        for skill_name in bonus_skill_names:
            user_skill = user_skills[skill_name]
            if user_skill.get("level") in ["senior", "expert"]:
                bonus_skills.append({
                    "skill": skill_name,
                    "level": user_skill.get("level"),
                    "years": user_skill.get("years", 0)
                })
        
        # Calculate overall skills score
        if not skill_matches:
            skills_score = 0.5
        else:
            # Required skills must be weighted more heavily
            required_matches = [sm for sm in skill_matches if sm["required"]]
            optional_matches = [sm for sm in skill_matches if not sm["required"]]
            
            if required_matches:
                required_score = sum(sm["score"] for sm in required_matches) / len(required_matches)
                # Heavy penalty for missing required skills
                if missing_required_skills:
                    required_score *= (1.0 - len(missing_required_skills) * 0.4)
            else:
                required_score = 0.8  # No required skills defined
            
            optional_score = 0.8  # Default if no optional skills
            if optional_matches:
                optional_score = sum(sm["score"] for sm in optional_matches) / len(optional_matches)
            
            # Weighted combination (required skills are 80% of score)
            skills_score = required_score * 0.8 + optional_score * 0.2
            
            # Small bonus for additional relevant skills
            if bonus_skills:
                bonus_factor = min(0.1, len(bonus_skills) * 0.02)
                skills_score += bonus_factor
        
        skills_score = min(1.0, max(0.0, skills_score))
        
        return {
            "score": round(skills_score, 3),
            "missing_required_skills": missing_required_skills,
            "skill_matches": skill_matches,
            "bonus_skills": bonus_skills,
            "total_skills_evaluated": len(skill_matches)
        }
    
    @classmethod
    def _calculate_category_match(
        cls, user_categories: List[str], role_category: str
    ) -> Dict[str, Any]:
        """Calculate category preference match."""
        
        if not user_categories:
            # No preferences specified - neutral score
            return {"score": 0.7, "matches_preference": False}
        
        if role_category in user_categories:
            return {"score": 1.0, "matches_preference": True, "preferred_category": role_category}
        else:
            return {"score": 0.3, "matches_preference": False, "user_categories": user_categories}
    
    @classmethod
    def _calculate_location_match(
        cls, user_profile: UserProfile, role: Role
    ) -> Dict[str, Any]:
        """Calculate location preference match."""
        
        location_prefs = user_profile.location_preferences or {}
        
        if not location_prefs:
            # No location preferences - neutral score
            return {"score": 0.8, "note": "No location preferences specified"}
        
        preferred_countries = location_prefs.get("countries", [])
        remote_ok = location_prefs.get("remote_ok", False)
        
        # Check if role location matches preferences
        if role.country == "Remote" and remote_ok:
            return {"score": 1.0, "match_type": "remote_preferred"}
        
        if role.country in preferred_countries:
            return {"score": 1.0, "match_type": "country_match", "country": role.country}
        
        if remote_ok and role.city and "remote" in role.city.lower():
            return {"score": 0.9, "match_type": "remote_option"}
        
        # Location doesn't match preferences
        return {"score": 0.4, "match_type": "location_mismatch"}
    
    @classmethod
    def _get_recommendation_level(
        cls, overall_score: float, missing_required_skills: List[str], level_gap: int
    ) -> str:
        """Determine recommendation level based on match analysis."""
        
        if missing_required_skills:
            return "not_recommended"
        
        if overall_score >= 0.85:
            return "excellent_match"
        elif overall_score >= 0.70:
            return "good_match"
        elif overall_score >= 0.50:
            if level_gap >= 2:  # Significantly overqualified
                return "overqualified"
            elif level_gap <= -2:  # Significantly underqualified
                return "underqualified" 
            else:
                return "possible_match"
        else:
            return "poor_match"
    
    @classmethod
    def _generate_match_reasons(
        cls,
        user_profile: UserProfile,
        role: Role,
        experience_match: Dict[str, Any],
        skills_match: Dict[str, Any],
        category_match: Dict[str, Any],
        location_match: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable reasons for the match score."""
        
        reasons = []
        
        # Experience reasons
        level_gap = experience_match["level_gap"]
        if level_gap == 0:
            reasons.append(f"Perfect experience level match ({experience_match['user_level']} level)")
        elif level_gap == 1:
            reasons.append(f"Slightly overqualified but good fit ({experience_match['user_level']} for {experience_match['role_level']} role)")
        elif level_gap >= 2:
            reasons.append(f"Significantly overqualified ({experience_match['user_level']} for {experience_match['role_level']} role)")
        elif level_gap == -1:
            reasons.append(f"Could be a growth opportunity ({experience_match['user_level']} to {experience_match['role_level']})")
        else:
            reasons.append(f"May be underqualified ({experience_match['user_level']} for {experience_match['role_level']} role)")
        
        # Skills reasons
        if skills_match["missing_required_skills"]:
            missing_count = len(skills_match["missing_required_skills"])
            if missing_count == 1:
                reasons.append(f"Missing required skill: {skills_match['missing_required_skills'][0]}")
            else:
                reasons.append(f"Missing {missing_count} required skills")
        else:
            strong_skills = [sm for sm in skills_match["skill_matches"] if sm["score"] >= 0.8 and sm["required"]]
            if strong_skills:
                reasons.append(f"Strong match in {len(strong_skills)} key required skills")
        
        # Bonus skills
        if skills_match["bonus_skills"]:
            expert_bonus = [bs for bs in skills_match["bonus_skills"] if bs["level"] == "expert"]
            if expert_bonus:
                reasons.append(f"Expert level in additional skills: {', '.join(bs['skill'] for bs in expert_bonus[:2])}")
        
        # Category match
        if category_match["matches_preference"]:
            reasons.append(f"Matches career interest in {role.category}")
        elif not category_match["matches_preference"] and category_match["score"] < 0.5:
            reasons.append(f"Role category ({role.category}) not in preferred areas")
        
        # Location match
        if location_match["score"] >= 0.9:
            if location_match.get("match_type") == "remote_preferred":
                reasons.append("Remote role matches location preference")
            elif location_match.get("match_type") == "country_match":
                reasons.append(f"Location ({role.country}) matches preference")
        
        return reasons[:5]  # Limit to top 5 reasons
    
    @classmethod
    async def get_recommended_roles(
        cls, 
        db: Session, 
        user_email: str, 
        limit: int = 10,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Get recommended roles for a user with match scores."""
        
        # Get user profile
        user_profile = db.query(UserProfile).filter(UserProfile.email == user_email).first()
        if not user_profile:
            return []
        
        # Get all open roles
        roles = db.query(Role).filter(Role.status == "open").all()
        
        # Calculate match scores for all roles
        role_matches = []
        for role in roles:
            match_info = cls.calculate_role_match(user_profile, role)
            
            if match_info["overall_score"] >= min_score:
                role_matches.append({
                    "role": role,
                    "match_score": match_info["overall_score"],
                    "recommendation": match_info["recommendation"],
                    "match_details": match_info["match_details"],
                    "reasons": match_info["reasons"]
                })
        
        # Sort by match score (highest first)
        role_matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Store match history for analytics
        await cls._store_match_history(db, user_email, role_matches[:limit])
        
        return role_matches[:limit]
    
    @classmethod
    async def _store_match_history(
        cls, db: Session, user_email: str, matches: List[Dict[str, Any]]
    ):
        """Store role match history for analytics and tracking."""
        
        try:
            for match in matches:
                role = match["role"]
                
                # Check if we already have recent history for this user-role combination
                existing = db.query(RoleMatchHistory).filter(
                    RoleMatchHistory.user_email == user_email,
                    RoleMatchHistory.role_id == role.role_id
                ).first()
                
                if not existing:
                    # Create new match history entry
                    match_history = RoleMatchHistory(
                        user_email=user_email,
                        role_id=role.role_id,
                        match_score={
                            "overall_score": match["match_score"],
                            "recommendation": match["recommendation"],
                            "details": match["match_details"]
                        }
                    )
                    db.add(match_history)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to store match history: {e}")
            db.rollback()