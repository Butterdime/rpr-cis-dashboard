"""
Configuration Module
"""

import os
from typing import Dict

class Config:
    """
    Application configuration
    """
    
    def __init__(self):
        self.database_path = os.path.join('data', 'database.db')
        self.upload_folder = os.path.join('data', 'documents')
        self.audit_folder = os.path.join('data', 'audit_trail')
        
        # Quality thresholds
        self.quality_thresholds = {
            'dpi': {'min': 100, 'target': 200},
            'contrast': {'min': 60, 'target': 75},
            'rotation': {'max': 5, 'target': 1},
            'blur': {'max': 40, 'target': 30},
            'brightness': {'min': 30, 'max': 225, 'target_min': 50, 'target_max': 200}
        }
        
        # Risk assessment thresholds
        self.risk_thresholds = {
            'tier1_max_yellow': 0,
            'tier2_max_red': 1,
            'tier3_min_red': 2,
            'tier3_min_yellow': 3
        }
        
        # OCR settings
        self.ocr_config = {
            'tesseract_cmd': '/usr/local/bin/tesseract',  # Update based on installation
            'confidence_threshold': 60
        }