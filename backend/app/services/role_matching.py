"""
Phase 2 three-factor role matching service for matching candidates to job roles.
Uses categories, experience level, and tags for intelligent matching.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import Role, UserProfile, RoleMatchHistory

logger = logging.getLogger(__name__)

class RoleMatchingService:
    """Service for Phase 2 three-factor role matching (categories + experience_level + tags)."""
    
    # Experience level hierarchy for ±1 level compatibility
    EXPERIENCE_LEVELS = ["intern", "junior", "mid", "senior", "lead", "principal"]
    
    # Category matching thresholds by business category
    CATEGORY_TAG_THRESHOLDS = {
        "technology": 0.35,           # Higher precision needed for technical roles
        "sales": 0.25,               # Broader skill transferability
        "marketing": 0.20,           # Creative skills vary widely
        "operations": 0.30,          # Process-focused
        "investment_management": 0.30, # Finance-specific skills
        "legal_compliance": 0.35,    # Specialized knowledge required
        "relationship_management": 0.25  # People skills transferable
    }
    
    @classmethod
    def calculate_role_match(cls, user_profile: UserProfile, role: Role) -> Dict[str, Any]:
        """Calculate Phase 2 three-factor match score between user and role."""
        
        # Extract Phase 2 user profile data
        user_categories = user_profile.categories or []
        user_experience_level = user_profile.experience_level or "junior"
        user_tags = user_profile.tags or []
        
        # Extract role data
        role_category = role.category
        role_experience_level = role.required_experience_level or "mid"
        role_tags = role.tags or []
        
        # 1. Category Matching (40% weight)
        category_match = cls._calculate_category_match(user_categories, role_category)
        
        # 2. Experience Level Compatibility (30% weight)
        experience_match = cls._calculate_experience_compatibility(
            user_experience_level, role_experience_level
        )
        
        # 3. Tag Matching (30% weight)
        tag_match = cls._calculate_tag_match(
            user_tags, role_tags, role_category
        )
        
        # Calculate weighted overall score
        overall_score = (
            category_match["score"] * 0.4 +    # 40% category match
            experience_match["score"] * 0.3 +  # 30% experience compatibility
            tag_match["score"] * 0.3           # 30% tag match
        )
        
        # Determine recommendation level
        recommendation = cls._get_recommendation_level(
            overall_score, 
            category_match["matches"],
            experience_match["compatible"],
            tag_match["threshold_met"]
        )
        
        # Generate explanatory reasons
        reasons = cls._generate_match_reasons(
            user_profile, role, category_match, experience_match, tag_match
        )
        
        return {
            "overall_score": round(overall_score, 3),
            "recommendation": recommendation,
            "match_details": {
                "category": category_match,
                "experience": experience_match,
                "tags": tag_match
            },
            "reasons": reasons,
            "calculated_at": datetime.utcnow().isoformat()
        }
    
    @classmethod
    def _calculate_category_match(cls, user_categories: List[str], role_category: str) -> Dict[str, Any]:
        """Calculate category match score with primary/secondary logic."""
        
        if not user_categories:
            return {"score": 0.0, "matches": False, "match_type": "no_categories"}
        
        if role_category in user_categories:
            # Check if it's primary or secondary category
            primary_match = user_categories[0] == role_category
            
            if primary_match:
                return {
                    "score": 1.0,
                    "matches": True,
                    "match_type": "primary_category",
                    "category": role_category
                }
            else:
                return {
                    "score": 0.8,
                    "matches": True,
                    "match_type": "secondary_category",
                    "category": role_category
                }
        else:
            return {
                "score": 0.0,
                "matches": False,
                "match_type": "no_category_overlap",
                "user_categories": user_categories,
                "role_category": role_category
            }
    
    @classmethod
    def _calculate_experience_compatibility(cls, user_level: str, role_level: str) -> Dict[str, Any]:
        """Calculate experience level compatibility with ±1 level flexibility."""
        
        try:
            user_index = cls.EXPERIENCE_LEVELS.index(user_level)
            role_index = cls.EXPERIENCE_LEVELS.index(role_level)
            
            level_gap = user_index - role_index
            compatible = abs(level_gap) <= 1  # ±1 level flexibility
            
            if level_gap == 0:
                score = 1.0  # Perfect match
                match_type = "exact_match"
            elif level_gap == 1:
                score = 0.9  # Slightly overqualified
                match_type = "slightly_overqualified"
            elif level_gap == -1:
                score = 0.8  # Growth opportunity
                match_type = "growth_opportunity"
            elif level_gap >= 2:
                score = 0.3  # Significantly overqualified
                match_type = "overqualified"
            else:  # level_gap <= -2
                score = 0.2  # Significantly underqualified
                match_type = "underqualified"
            
            return {
                "score": score,
                "compatible": compatible,
                "level_gap": level_gap,
                "user_level": user_level,
                "role_level": role_level,
                "match_type": match_type
            }
            
        except ValueError:
            # Invalid experience level
            return {
                "score": 0.5,
                "compatible": False,
                "level_gap": 0,
                "user_level": user_level,
                "role_level": role_level,
                "match_type": "invalid_level"
            }
    
    @classmethod
    def _calculate_tag_match(cls, user_tags: List[str], role_tags: List[str], role_category: str) -> Dict[str, Any]:
        """Calculate tag match with configurable threshold by category."""
        
        if not role_tags:
            return {
                "score": 0.8,
                "threshold_met": True,
                "exact_matches": [],
                "missing_tags": [],
                "match_percentage": 0.0,
                "threshold": 0.0
            }
        
        if not user_tags:
            return {
                "score": 0.0,
                "threshold_met": False,
                "exact_matches": [],
                "missing_tags": role_tags,
                "match_percentage": 0.0,
                "threshold": cls.CATEGORY_TAG_THRESHOLDS.get(role_category, 0.25)
            }
        
        # Convert to lowercase for case-insensitive matching
        user_tags_lower = [tag.lower().strip() for tag in user_tags]
        role_tags_lower = [tag.lower().strip() for tag in role_tags]
        
        # Find exact matches
        exact_matches = set(user_tags_lower) & set(role_tags_lower)
        match_percentage = len(exact_matches) / len(role_tags_lower)
        
        # Get category-specific threshold
        threshold = cls.CATEGORY_TAG_THRESHOLDS.get(role_category, 0.25)
        threshold_met = match_percentage >= threshold
        
        # Calculate score based on match percentage
        if match_percentage >= 0.7:
            score = 1.0  # Excellent match
        elif match_percentage >= 0.5:
            score = 0.8  # Good match
        elif match_percentage >= threshold:
            score = 0.6  # Meets threshold
        else:
            # Below threshold - scale score proportionally
            score = match_percentage / threshold * 0.5
        
        # Find missing tags
        missing_tags = [tag for tag in role_tags_lower if tag not in user_tags_lower]
        
        return {
            "score": round(score, 3),
            "threshold_met": threshold_met,
            "exact_matches": list(exact_matches),
            "missing_tags": missing_tags,
            "match_percentage": round(match_percentage, 3),
            "threshold": threshold,
            "user_tag_count": len(user_tags),
            "role_tag_count": len(role_tags)
        }
    
    @classmethod
    def _get_recommendation_level(
        cls, 
        overall_score: float, 
        category_match: bool, 
        experience_compatible: bool, 
        threshold_met: bool
    ) -> str:
        """Determine recommendation level based on Phase 2 match analysis."""
        
        # Strong requirements for good recommendations
        if not category_match:
            return "poor_match"  # Must have category overlap
        
        if overall_score >= 0.85 and experience_compatible and threshold_met:
            return "excellent_match"
        elif overall_score >= 0.70 and experience_compatible:
            return "good_match"
        elif overall_score >= 0.50:
            if experience_compatible:
                return "possible_match"
            else:
                return "experience_mismatch"
        else:
            return "poor_match"
    
    @classmethod
    def _generate_match_reasons(
        cls,
        user_profile: UserProfile,
        role: Role,
        category_match: Dict[str, Any],
        experience_match: Dict[str, Any],
        tag_match: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable reasons for the Phase 2 match score."""
        
        reasons = []
        
        # Category reasons
        if category_match["matches"]:
            if category_match["match_type"] == "primary_category":
                reasons.append(f"Perfect category match - {role.category} is your primary area")
            else:
                reasons.append(f"Good category match - {role.category} is in your background")
        else:
            reasons.append(f"Role category ({role.category}) doesn't match your background")
        
        # Experience level reasons
        match_type = experience_match["match_type"]
        if match_type == "exact_match":
            reasons.append(f"Perfect experience level match ({experience_match['user_level']})")
        elif match_type == "slightly_overqualified":
            reasons.append(f"Slightly overqualified but good fit ({experience_match['user_level']} for {experience_match['role_level']})")
        elif match_type == "growth_opportunity":
            reasons.append(f"Great growth opportunity ({experience_match['user_level']} to {experience_match['role_level']})")
        elif match_type == "overqualified":
            reasons.append(f"Significantly overqualified ({experience_match['user_level']} for {experience_match['role_level']})")
        elif match_type == "underqualified":
            reasons.append(f"May be underqualified ({experience_match['user_level']} for {experience_match['role_level']})")
        
        # Tag/skills reasons
        if tag_match["threshold_met"]:
            match_count = len(tag_match["exact_matches"])
            total_required = tag_match["role_tag_count"]
            if match_count >= total_required * 0.7:
                reasons.append(f"Excellent skills match - {match_count}/{total_required} required skills")
            else:
                reasons.append(f"Good skills match - {match_count}/{total_required} required skills")
        else:
            missing_count = len(tag_match["missing_tags"])
            if missing_count <= 3:
                reasons.append(f"Missing {missing_count} key skills: {', '.join(tag_match['missing_tags'][:3])}")
            else:
                reasons.append(f"Missing {missing_count} required skills")
        
        # Additional skills insight
        if tag_match["user_tag_count"] > tag_match["role_tag_count"]:
            extra_skills = tag_match["user_tag_count"] - len(tag_match["exact_matches"])
            if extra_skills > 5:
                reasons.append(f"Brings {extra_skills} additional relevant skills")
        
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