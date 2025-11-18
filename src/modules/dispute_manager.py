"""
Dispute Management and Resolution Module
"""

from datetime import datetime, timezone
from typing import Dict, List
import uuid
import logging

class DisputeManager:
    """
    Handles customer disputes and appeals
    Supports full dispute workflow with re-verification
    """
    
    def __init__(self, database):
        self.logger = logging.getLogger(__name__)
        self.db = database
    
    def create_dispute(self, original_verification_id: str, customer_reason: str,
                       additional_docs: list = None) -> Dict:
        """
        Create new dispute record
        """
        dispute_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        dispute = {
            'id': dispute_id,
            'original_verification_id': original_verification_id,
            'customer_reason': customer_reason,
            'additional_documents': additional_docs or [],
            'created_at': timestamp,
            'status': 'INTAKE',
            'audit_trail': [
                {
                    'timestamp': timestamp,
                    'action': 'DISPUTE_CREATED',
                    'details': customer_reason
                }
            ]
        }
        
        # Store in database
        self.db.save_dispute(dispute)
        
        return dispute
    
    def perform_dispute_triage(self, dispute_id: str, original_risk_assessment: Dict) -> Dict:
        """
        Analyze dispute and determine path forward
        Root cause analysis
        """
        dispute = self.db.get_dispute(dispute_id)
        
        # Root cause analysis
        root_causes = []
        
        red_flags = original_risk_assessment.get('red_flags', 0)
        yellow_flags = original_risk_assessment.get('yellow_flags', 0)
        
        if red_flags > 0:
            root_causes.append("Multiple RED flags detected")
        if yellow_flags > 0:
            root_causes.append(f"{yellow_flags} YELLOW flag(s) detected")
        
        # Get original mismatches
        mismatches = original_risk_assessment.get('mismatches', [])
        specific_issues = [m['field'] for m in mismatches if m['severity'] != 'GREEN']
        
        triage = {
            'dispute_id': dispute_id,
            'root_causes': root_causes,
            'specific_issues': specific_issues,
            'recommendation': 'RE_VERIFY' if len(dispute.get('additional_documents', [])) > 0 else 'MANUAL_REVIEW',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Update dispute status
        dispute['status'] = 'TRIAGED'
        dispute['triage'] = triage
        self.db.save_dispute(dispute)
        
        return triage
    
    def perform_re_verification(self, dispute_id: str, extracted_data_doc1: Dict,
                                extracted_data_doc2: Dict, new_context: str = None) -> Dict:
        """
        Re-verify customer with additional context
        Re-assessment of risk tier
        """
        from mismatch_detector import MismatchDetector, RiskAssessor
        
        dispute = self.db.get_dispute(dispute_id)
        mismatch_detector = MismatchDetector()
        risk_assessor = RiskAssessor()
        
        # Re-detect mismatches with all available data
        mismatches = mismatch_detector.detect_mismatches(extracted_data_doc1, extracted_data_doc2)
        
        # Re-assess risk tier
        new_assessment = risk_assessor.assess_risk_tier(
            mismatches,
            ocr_quality=100,  # Assume good quality for re-verification
            customer_segment=dispute.get('customer_segment', 'general')
        )
        
        # Determine if decision changed
        original_decision = dispute.get('original_decision', 'UNKNOWN')
        new_decision = new_assessment['decision']
        decision_changed = (new_decision != original_decision)
        
        re_verification = {
            'dispute_id': dispute_id,
            'original_decision': original_decision,
            'new_decision': new_decision,
            'decision_changed': decision_changed,
            'new_risk_tier': new_assessment['tier'],
            'confidence': new_assessment['confidence'],
            'reasoning': new_assessment['reasoning'],
            'customer_context': new_context,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'mismatches': mismatches
        }
        
        # Update dispute
        dispute['status'] = 'RE_VERIFIED'
        dispute['re_verification'] = re_verification
        self.db.save_dispute(dispute)
        
        return re_verification
    
    def resolve_dispute(self, dispute_id: str, final_decision: str, reason: str) -> Dict:
        """
        Finalize dispute with clear resolution communication
        """
        dispute = self.db.get_dispute(dispute_id)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        resolution = {
            'dispute_id': dispute_id,
            'final_decision': final_decision,  # APPROVED, REJECTED_UPHELD, or APPROVED_OVERRIDE
            'reason': reason,
            'resolved_at': timestamp,
            'communication_sent': False
        }
        
        # Update dispute
        dispute['status'] = 'RESOLVED'
        dispute['resolution'] = resolution
        dispute['audit_trail'].append({
            'timestamp': timestamp,
            'action': 'DISPUTE_RESOLVED',
            'decision': final_decision,
            'reason': reason
        })
        
        self.db.save_dispute(dispute)
        
        return resolution
    
    def generate_resolution_communication(self, dispute_id: str) -> str:
        """
        Generate customer-facing resolution letter
        Professional, respectful tone
        """
        dispute = self.db.get_dispute(dispute_id)
        resolution = dispute.get('resolution', {})
        final_decision = resolution.get('final_decision')
        
        customer_name = dispute.get('customer_name', 'Valued Customer')
        
        if final_decision == 'APPROVED':
            letter = f"""
Dear {customer_name},

Thank you for contacting us regarding your recent verification.

We have reviewed your dispute and your additional documentation. Based on this 
complete assessment, we are pleased to inform you that your verification has been APPROVED.

Your account is now active and ready to use.

We appreciate your patience and apologize for any inconvenience.

Best regards,
RPR CIS Dashboard Team
            """
        elif final_decision == 'APPROVED_OVERRIDE':
            letter = f"""
Dear {customer_name},

Thank you for contacting us regarding your recent verification dispute.

We have carefully reviewed your case and the additional information you provided. 
While there were minor discrepancies in your documentation, we recognize the context 
you've provided and have decided to APPROVE your verification.

Your account is now active. If you have any questions, please don't hesitate to reach out.

Best regards,
RPR CIS Dashboard Team
            """
        else:  # REJECTED_UPHELD
            letter = f"""
Dear {customer_name},

We have reviewed your dispute regarding your recent verification result.

After careful consideration of your appeal and the available documentation, 
we must respectfully uphold our initial decision.

The concerns identified during verification remain unresolved. If you believe 
this is in error, please provide additional documentation that addresses the 
specific issues noted.

We remain committed to assisting you.

Best regards,
RPR CIS Dashboard Team
            """
        
        return letter
    
    def get_dispute_analytics(self) -> Dict:
        """
        Generate dispute analytics for monitoring
        """
        all_disputes = self.db.get_all_disputes()
        
        total = len(all_disputes)
        resolved = len([d for d in all_disputes if d.get('status') == 'RESOLVED'])
        approved = len([d for d in all_disputes if d.get('resolution', {}).get('final_decision') == 'APPROVED'])
        rejected_upheld = len([d for d in all_disputes if d.get('resolution', {}).get('final_decision') == 'REJECTED_UPHELD'])
        
        analytics = {
            'total_disputes': total,
            'resolved_disputes': resolved,
            'pending_disputes': total - resolved,
            'approved_on_appeal': approved,
            'rejected_upheld': rejected_upheld,
            'approval_rate_on_appeal': round(approved / resolved * 100, 1) if resolved > 0 else 0,
            'recovery_rate': round(approved / total * 100, 1) if total > 0 else 0
        }
        
        return analytics