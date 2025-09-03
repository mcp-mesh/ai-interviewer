"""
Violation Detector - Content Safety & Behavioral Analysis

Detects behavioral violations in user responses including profanity, sexual content,
political discussions, and off-topic conversations to maintain professional interview environment.
"""

import logging
import re
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class ViolationDetector:
    """
    Detects and scores behavioral violations in user responses.
    """
    
    def __init__(self):
        """Initialize violation detector with keyword patterns."""
        self.logger = logging.getLogger(__name__)
        
        # Profanity keywords (sample - should be expanded)
        self.profanity_patterns = [
            r'\bf+u+c+k+\w*', r'\bs+h+i+t+\w*', r'\bd+a+m+n+\w*', 
            r'\bb+i+t+c+h+\w*', r'\ba+s+s+h+o+l+e+\w*', r'\bc+r+a+p+\w*'
        ]
        
        # Sexual content patterns
        self.sexual_patterns = [
            r'\bsex\w*', r'\bnaked\b', r'\bporn\w*', r'\bmasturbat\w*',
            r'\borgasm\w*', r'\berotic\w*', r'\bintimate\w*', r'\bsexy\b'
        ]
        
        # Political keywords
        self.political_patterns = [
            r'\btrump\b', r'\bbiden\b', r'\belection\w*', r'\bdemocrat\w*',
            r'\brepublican\w*', r'\bpolitics?\b', r'\bgovernment\b', r'\bvoting?\b',
            r'\bcampaign\w*', r'\bconservative\w*', r'\bliberal\w*'
        ]
        
        # Off-topic indicators (non-technical/job-related)
        self.off_topic_patterns = [
            r'\bweather\b', r'\bsports?\b', r'\bmovies?\b', r'\bmusic\b',
            r'\bfood\b', r'\bholidays?\b', r'\bvacation\w*', r'\bweekend\w*',
            r'\bparty\w*', r'\bdating\b', r'\brelationship\w*', r'\bfamily\b'
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = {
            'profanity': [re.compile(pattern, re.IGNORECASE) for pattern in self.profanity_patterns],
            'sexual': [re.compile(pattern, re.IGNORECASE) for pattern in self.sexual_patterns],
            'political': [re.compile(pattern, re.IGNORECASE) for pattern in self.political_patterns],
            'off_topic': [re.compile(pattern, re.IGNORECASE) for pattern in self.off_topic_patterns]
        }
    
    def detect_violations(self, text: str, job_description: str = "") -> Dict[str, Any]:
        """
        Detect behavioral violations in text content.
        
        Args:
            text: User input text to analyze
            job_description: Job description for relevance checking
            
        Returns:
            Dictionary with violation counts and details
        """
        try:
            if not text or not text.strip():
                return self._empty_violation_result()
            
            text_clean = text.lower().strip()
            violations = {
                'profanity': 0,
                'sexual': 0, 
                'political': 0,
                'off_topic': 0,
                'total': 0,
                'flags': {},
                'matches': {}
            }
            
            # Check each violation category
            for category, patterns in self.compiled_patterns.items():
                matches = []
                for pattern in patterns:
                    found_matches = pattern.findall(text_clean)
                    if found_matches:
                        matches.extend(found_matches)
                
                if matches:
                    violations[category] = len(matches)
                    violations['matches'][category] = matches[:3]  # Store first 3 matches
                    violations['flags'][category] = {
                        'detected': True,
                        'count': len(matches),
                        'severity': self._calculate_severity(category, len(matches))
                    }
            
            # Calculate total violation score
            violations['total'] = (
                violations['profanity'] * 2 +    # Profanity weighted higher
                violations['sexual'] * 3 +       # Sexual content highest weight
                violations['political'] * 1 +    # Political lower weight
                violations['off_topic'] * 1      # Off-topic lowest weight
            )
            
            # Add context information
            violations['analysis'] = {
                'text_length': len(text),
                'word_count': len(text.split()),
                'violation_density': violations['total'] / max(len(text.split()), 1),
                'risk_level': self._calculate_risk_level(violations['total'])
            }
            
            if violations['total'] > 0:
                self.logger.warning(f"Violations detected: {violations['total']} total score")
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error detecting violations: {e}")
            return self._empty_violation_result()
    
    def _calculate_severity(self, category: str, count: int) -> str:
        """Calculate severity level for a violation category."""
        if count == 0:
            return "none"
        elif count == 1:
            return "low"
        elif count <= 3:
            return "medium" 
        else:
            return "high"
    
    def _calculate_risk_level(self, total_score: int) -> str:
        """Calculate overall risk level based on total violation score."""
        if total_score == 0:
            return "safe"
        elif total_score <= 2:
            return "low"
        elif total_score <= 5:
            return "medium"
        elif total_score <= 10:
            return "high"
        else:
            return "critical"
    
    def _empty_violation_result(self) -> Dict[str, Any]:
        """Return empty violation result structure."""
        return {
            'profanity': 0,
            'sexual': 0,
            'political': 0,
            'off_topic': 0,
            'total': 0,
            'flags': {},
            'matches': {},
            'analysis': {
                'text_length': 0,
                'word_count': 0,
                'violation_density': 0,
                'risk_level': 'safe'
            }
        }
    
    def is_termination_required(self, total_violations: int, threshold: int = 3) -> Tuple[bool, str]:
        """
        Determine if interview should be terminated due to violations.
        
        Args:
            total_violations: Accumulated violation score
            threshold: Maximum allowed violations
            
        Returns:
            Tuple of (should_terminate, reason)
        """
        if total_violations >= threshold:
            return True, f"Interview terminated due to behavioral violations (score: {total_violations}, threshold: {threshold})"
        return False, ""

# Global violation detector instance
violation_detector = ViolationDetector()