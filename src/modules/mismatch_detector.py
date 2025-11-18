"""
Mismatch Detection and Risk Assessment Module
"""

from difflib import SequenceMatcher
from typing import Dict, List, Tuple
import logging

class MismatchDetector:
    """
    Detects mismatches between document fields
    Classifies severity: GREEN/YELLOW/RED
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def fuzzy_match(self, str1: str, str2: str, threshold: float = 0.80) -> Tuple[float, bool]:
        """
        Fuzzy string matching using Levenshtein-like approach
        Returns: (similarity_score, is_match)
        """
        # Normalize strings
        str1_norm = str1.lower().strip()
        str2_norm = str2.lower().strip()
        
        # Exact match
        if str1_norm == str2_norm:
            return (1.0, True)
        
        # Fuzzy match using SequenceMatcher
        similarity = SequenceMatcher(None, str1_norm, str2_norm).ratio()
        
        # Changed from 0.85 to 0.80 to catch more variations
        is_match = similarity >= threshold  # threshold is now 0.80
        
        return (similarity, is_match)
    
    def classify_mismatch_severity(self, field_name: str, value1: str, value2: str, 
                                   similarity: float) -> Dict:
        """
        Classify mismatch severity as GREEN/YELLOW/RED
        Context-aware based on field type
        """
        
        # Field-specific thresholds
        field_thresholds = {
            'name': {'green': 1.0, 'yellow': 0.90},
            'date_of_birth': {'green': 1.0, 'yellow': 0.95},
            'address': {'green': 1.0, 'yellow': 0.85},
            'postcode': {'green': 1.0, 'yellow': 0.95},
            'abn': {'green': 1.0, 'yellow': 0.90},
            'acn': {'green': 1.0, 'yellow': 0.90}
        }
        
        thresholds = field_thresholds.get(field_name, {'green': 1.0, 'yellow': 0.85})
        
        if similarity >= thresholds['green']:
            severity = 'GREEN'
            message = f"{field_name}: Exact match"
        elif similarity >= thresholds['yellow']:
            severity = 'YELLOW'
            # Provide context
            if field_name == 'name' and abs(len(value1) - len(value2)) <= 2:
                message = f"{field_name}: Minor variation (e.g., Jon vs. John)"
            elif field_name == 'address' and similarity > 0.80:
                message = f"{field_name}: Possible address update or abbreviation"
            else:
                message = f"{field_name}: Minor discrepancy ({similarity:.0%} match)"
            severity = 'YELLOW'
        else:
            severity = 'RED'
            message = f"{field_name}: Significant mismatch ({similarity:.0%} match)"
        
        return {
            'field': field_name,
            'value1': value1,
            'value2': value2,
            'similarity': round(similarity, 3),
            'severity': severity,
            'message': message
        }
    
    def detect_mismatches(self, doc1_fields: Dict, doc2_fields: Dict) -> List[Dict]:
        """
        Detect and classify all mismatches between two documents
        Returns list of mismatches with severity
        """
        mismatches = []
        
        # Compare all fields
        for field_name in doc1_fields:
            if field_name not in doc2_fields:
                continue
            
            value1 = str(doc1_fields[field_name]) if doc1_fields[field_name] else ""
            value2 = str(doc2_fields[field_name]) if doc2_fields[field_name] else ""
            
            if value1 and value2:
                similarity, _ = self.fuzzy_match(value1, value2)
                
                if similarity < 1.0:  # Report any non-exact match as mismatch
                    mismatch = self.classify_mismatch_severity(
                        field_name, value1, value2, similarity
                    )
                    mismatches.append(mismatch)
        
        return mismatches


class RiskAssessor:
    """
    Assigns risk tier (1, 2, 3) based on mismatches and evidence
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mismatch_detector = MismatchDetector()
    
    def count_severity_flags(self, mismatches: List[Dict]) -> Dict:
        """Count GREEN/YELLOW/RED flags"""
        counts = {'GREEN': 0, 'YELLOW': 0, 'RED': 0}
        for mismatch in mismatches:
            counts[mismatch['severity']] += 1
        return counts
    
    def assess_risk_tier(self, mismatches: List[Dict], ocr_quality: int,
                        transaction_amount: float = 0, customer_segment: str = "general") -> Dict:
        """
        Assign risk tier (1, 2, or 3)
        
        Tier 1 (Low Risk): No RED flags; all key fields match; clear documents
        Tier 2 (Moderate Risk): 1-2 YELLOW flags; most fields match; some issues
        Tier 3 (High Risk): Multiple RED flags; pattern inconsistencies; suspicious
        """
        
        severity_counts = self.count_severity_flags(mismatches)
        red_count = severity_counts['RED']
        yellow_count = severity_counts['YELLOW']
        
        # Base tier assignment
        if red_count >= 2:
            tier = 3
            confidence = 0.95
            reasoning = f"Multiple RED flags ({red_count}): High fraud risk"
        elif red_count == 1:
            tier = 2
            confidence = 0.85
            reasoning = f"One RED flag: Requires review"
        elif yellow_count >= 3:
            tier = 3
            confidence = 0.80
            reasoning = f"Multiple YELLOW flags ({yellow_count}): Potential fraud pattern"
        elif yellow_count >= 1:
            tier = 2
            confidence = 0.75
            reasoning = f"{yellow_count} YELLOW flag(s): Moderate concern"
        else:
            tier = 1
            confidence = 0.98
            reasoning = "All fields match: Low risk"
        
        # Adjust for document quality
        if ocr_quality < 50:
            # Lower confidence if OCR quality poor
            confidence *= 0.8
            reasoning += " (low OCR quality reduces confidence)"
        
        # Adjust for vulnerable customer segments
        vulnerable_segments = ['domestic_violence', 'gender_diverse', 'refugee', 'homeless']
        if customer_segment in vulnerable_segments:
            # Use softer thresholds for vulnerable segments
            if tier == 3 and yellow_count > 0 and red_count == 0:
                tier = 2
                reasoning += " (vulnerable segment: softer thresholds applied)"
        
        # Transaction amount consideration
        if transaction_amount < 1000 and red_count == 0:
            # Low-value transactions get softer thresholds
            if tier == 2 and yellow_count <= 1:
                tier = 1
                reasoning += " (low-value transaction: reduced scrutiny)"
        
        return {
            'tier': tier,
            'confidence': round(confidence, 2),
            'reasoning': reasoning,
            'red_flags': red_count,
            'yellow_flags': yellow_count,
            'green_matches': severity_counts['GREEN'],
            'decision': 'APPROVE' if tier == 1 else ('ESCALATE' if tier == 2 else 'REJECT'),
            'mismatches': mismatches
        }