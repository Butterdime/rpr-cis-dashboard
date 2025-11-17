"""
Unit tests for Mismatch Detection and Risk Assessment Module
"""

import unittest
from modules.mismatch_detector import MismatchDetector, RiskAssessor

class TestMismatchDetector(unittest.TestCase):
    
    def setUp(self):
        self.detector = MismatchDetector()
        
    def test_fuzzy_match_exact(self):
        """Test exact fuzzy match"""
        similarity, is_match = self.detector.fuzzy_match("John Doe", "John Doe")
        self.assertEqual(similarity, 1.0)
        self.assertTrue(is_match)
        
    def test_fuzzy_match_similar(self):
        """Test similar fuzzy match"""
        similarity, is_match = self.detector.fuzzy_match("John Doe", "Jon Doe")
        self.assertGreater(similarity, 0.8)
        self.assertTrue(is_match)
        
    def test_fuzzy_match_different(self):
        """Test different fuzzy match"""
        similarity, is_match = self.detector.fuzzy_match("John Doe", "Jane Smith")
        self.assertLess(similarity, 0.5)
        self.assertFalse(is_match)
        
    def test_classify_mismatch_severity_green(self):
        """Test green mismatch severity"""
        result = self.detector.classify_mismatch_severity("name", "John", "John", 1.0)
        self.assertEqual(result['severity'], 'GREEN')
        
    def test_classify_mismatch_severity_yellow(self):
        """Test yellow mismatch severity"""
        result = self.detector.classify_mismatch_severity("name", "John", "Jon", 0.95)
        self.assertEqual(result['severity'], 'YELLOW')
        
    def test_classify_mismatch_severity_red(self):
        """Test red mismatch severity"""
        result = self.detector.classify_mismatch_severity("name", "John", "Jane", 0.3)
        self.assertEqual(result['severity'], 'RED')
        
    def test_detect_mismatches(self):
        """Test mismatch detection"""
        doc1 = {'name': 'John Doe', 'address': '123 Main St'}
        doc2 = {'name': 'Jon Doe', 'address': '123 Main St'}
        mismatches = self.detector.detect_mismatches(doc1, doc2)
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0]['field'], 'name')

class TestRiskAssessor(unittest.TestCase):
    
    def setUp(self):
        self.assessor = RiskAssessor()
        
    def test_count_severity_flags(self):
        """Test severity flag counting"""
        mismatches = [
            {'severity': 'RED'},
            {'severity': 'YELLOW'},
            {'severity': 'YELLOW'},
            {'severity': 'GREEN'}
        ]
        counts = self.assessor.count_severity_flags(mismatches)
        self.assertEqual(counts['RED'], 1)
        self.assertEqual(counts['YELLOW'], 2)
        self.assertEqual(counts['GREEN'], 1)
        
    def test_assess_risk_tier_low(self):
        """Test low risk tier assessment"""
        mismatches = [{'severity': 'GREEN'}]
        result = self.assessor.assess_risk_tier(mismatches, 85)
        self.assertEqual(result['tier'], 1)
        self.assertEqual(result['decision'], 'APPROVE')
        
    def test_assess_risk_tier_high(self):
        """Test high risk tier assessment"""
        mismatches = [
            {'severity': 'RED'},
            {'severity': 'RED'},
            {'severity': 'YELLOW'}
        ]
        result = self.assessor.assess_risk_tier(mismatches, 70)
        self.assertEqual(result['tier'], 3)
        self.assertEqual(result['decision'], 'REJECT')

if __name__ == '__main__':
    unittest.main()