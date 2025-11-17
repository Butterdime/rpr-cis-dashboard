"""
Unit tests for Document Quality Assessment Module
"""

import unittest
import numpy as np
import cv2
import os
import tempfile
from modules.document_processor import DocumentQualityAssessor

class TestDocumentQualityAssessor(unittest.TestCase):
    
    def setUp(self):
        self.assessor = DocumentQualityAssessor()
        # Create a test image
        self.test_image = np.ones((1000, 1500, 3), dtype=np.uint8) * 255  # White image
        
    def test_assess_dpi(self):
        """Test DPI assessment"""
        result = self.assessor.assess_dpi(self.test_image)
        self.assertIn('dpi', result)
        self.assertIn('severity', result)
        self.assertIn('status', result)
        
    def test_assess_contrast(self):
        """Test contrast assessment"""
        result = self.assessor.assess_contrast(self.test_image)
        self.assertIn('contrast', result)
        self.assertIn('severity', result)
        self.assertTrue(0 <= result['contrast'] <= 100)
        
    def test_assess_rotation(self):
        """Test rotation assessment"""
        result = self.assessor.assess_rotation(self.test_image)
        self.assertIn('rotation', result)
        self.assertIn('severity', result)
        
    def test_assess_blur(self):
        """Test blur assessment"""
        result = self.assessor.assess_blur(self.test_image)
        self.assertIn('blur', result)
        self.assertIn('severity', result)
        self.assertIn('methods', result)
        
    def test_assess_brightness(self):
        """Test brightness assessment"""
        result = self.assessor.assess_brightness(self.test_image)
        self.assertIn('brightness', result)
        self.assertIn('severity', result)
        
    def test_get_quality_score(self):
        """Test quality score calculation"""
        mock_metrics = {
            'dpi': {'severity': 'GREEN'},
            'contrast': {'severity': 'GREEN'},
            'rotation': {'severity': 'GREEN'},
            'blur': {'severity': 'GREEN'},
            'brightness': {'severity': 'GREEN'}
        }
        score = self.assessor.get_quality_score(mock_metrics)
        self.assertTrue(0 <= score <= 100)
        
    def test_assess_document_quality_invalid_image(self):
        """Test quality assessment with invalid image"""
        result = self.assessor.assess_document_quality('nonexistent.jpg')
        self.assertFalse(result['success'])
        self.assertIn('error', result)

if __name__ == '__main__':
    unittest.main()