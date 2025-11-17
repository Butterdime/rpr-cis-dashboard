"""
Unit tests for OCR Extractor Module
"""

import unittest
import numpy as np
from modules.document_processor import OCRExtractor

class TestOCRExtractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = OCRExtractor()
        # Create a test image with some text-like pattern
        self.test_image = np.ones((500, 800, 3), dtype=np.uint8) * 255
        
    def test_extract_text_with_confidence(self):
        """Test OCR text extraction"""
        result = self.extractor.extract_text_with_confidence(self.test_image)
        self.assertIn('success', result)
        self.assertIn('extractions', result)
        self.assertIn('overall_confidence', result)
        
    def test_calibrate_confidence_scores(self):
        """Test confidence score calibration"""
        mock_results = [
            {'confidence': 80, 'text': 'test'},
            {'confidence': 90, 'text': 'data'}
        ]
        calibrated = self.extractor.calibrate_confidence_scores(mock_results, 95.0)
        self.assertEqual(len(calibrated), 2)
        self.assertIn('confidence_calibrated', calibrated[0])
        
    def test_extract_structured_data(self):
        """Test structured data extraction"""
        mock_extraction = {
            'extractions': [
                {'text': 'John Doe', 'confidence': 95},
                {'text': '123 Main St', 'confidence': 90},
                {'text': '3000', 'confidence': 85},
                {'text': '0412345678', 'confidence': 88},
                {'text': '123456789', 'confidence': 92}
            ]
        }
        result = self.extractor.extract_structured_data(self.test_image, mock_extraction)
        self.assertIn('fields', result)
        self.assertIn('raw_text', result)

if __name__ == '__main__':
    unittest.main()