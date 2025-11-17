"""
Unit tests for Dispute Management Module
"""

import unittest
from unittest.mock import Mock
from modules.dispute_manager import DisputeManager

class TestDisputeManager(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = Mock()
        self.manager = DisputeManager(self.mock_db)
        
    def test_create_dispute(self):
        """Test dispute creation"""
        self.mock_db.save_dispute = Mock()
        
        dispute = self.manager.create_dispute(
            "ver_123", "Documents don't match", ["doc1.jpg"]
        )
        
        self.assertIn('id', dispute)
        self.assertEqual(dispute['original_verification_id'], "ver_123")
        self.assertEqual(dispute['customer_reason'], "Documents don't match")
        self.assertEqual(dispute['status'], 'INTAKE')
        self.assertIn('audit_trail', dispute)
        
        self.mock_db.save_dispute.assert_called_once()
        
    def test_perform_dispute_triage(self):
        """Test dispute triage"""
        mock_dispute = {
            'id': 'disp_123',
            'additional_documents': ['doc1.jpg'],
            'status': 'INTAKE'
        }
        self.mock_db.get_dispute.return_value = mock_dispute
        self.mock_db.save_dispute = Mock()
        
        original_assessment = {'red_flags': 1, 'yellow_flags': 0, 'mismatches': []}
        triage = self.manager.perform_dispute_triage("disp_123", original_assessment)
        
        self.assertIn('root_causes', triage)
        self.assertIn('recommendation', triage)
        
        self.mock_db.save_dispute.assert_called_once()
        
    def test_resolve_dispute(self):
        """Test dispute resolution"""
        mock_dispute = {
            'id': 'disp_123',
            'status': 'RE_VERIFIED',
            'audit_trail': []
        }
        self.mock_db.get_dispute.return_value = mock_dispute
        self.mock_db.save_dispute = Mock()
        
        resolution = self.manager.resolve_dispute(
            "disp_123", "APPROVED", "Additional documentation verified"
        )
        
        self.assertEqual(resolution['final_decision'], "APPROVED")
        self.assertEqual(resolution['reason'], "Additional documentation verified")
        
        self.mock_db.save_dispute.assert_called_once()
        
    def test_generate_resolution_communication_approved(self):
        """Test resolution communication for approved dispute"""
        mock_dispute = {'customer_name': 'John Doe'}
        self.mock_db.get_dispute.return_value = mock_dispute
        
        letter = self.manager.generate_resolution_communication("disp_123")
        
        self.assertIn("APPROVED", letter)
        self.assertIn("John Doe", letter)
        
    def test_get_dispute_analytics(self):
        """Test dispute analytics"""
        mock_disputes = [
            {'status': 'RESOLVED', 'resolution': {'final_decision': 'APPROVED'}},
            {'status': 'RESOLVED', 'resolution': {'final_decision': 'REJECTED_UPHELD'}},
            {'status': 'INTAKE'}
        ]
        self.mock_db.get_all_disputes.return_value = mock_disputes
        
        analytics = self.manager.get_dispute_analytics()
        
        self.assertEqual(analytics['total_disputes'], 3)
        self.assertEqual(analytics['resolved_disputes'], 2)
        self.assertEqual(analytics['approved_on_appeal'], 1)

if __name__ == '__main__':
    unittest.main()