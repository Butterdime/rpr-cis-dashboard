"""
Audit Trail Module - 7-Year Immutable Audit Trail
"""

from datetime import datetime, timedelta
from typing import Dict, List
import json
import hashlib
import logging
import os

class AuditTrail:
    """
    7-year immutable audit trail with encryption
    """
    
    def __init__(self, audit_folder: str = "data/audit_trail"):
        self.audit_folder = audit_folder
        self.logger = logging.getLogger(__name__)
        self.retention_years = 7
        
        # Ensure audit folder exists
        os.makedirs(audit_folder, exist_ok=True)
    
    def log_event(self, entity_type: str, entity_id: str, action: str, 
                  details: Dict, user_id: str = None) -> str:
        """
        Log an auditable event with immutable record
        Returns audit entry ID
        """
        timestamp = datetime.utcnow()
        entry_id = self._generate_entry_id(entity_type, entity_id, timestamp)
        
        audit_entry = {
            'id': entry_id,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'action': action,
            'details': details,
            'user_id': user_id,
            'timestamp': timestamp.isoformat(),
            'hash': self._calculate_hash({
                'entity_type': entity_type,
                'entity_id': entity_id,
                'action': action,
                'details': json.dumps(details, sort_keys=True),
                'user_id': user_id,
                'timestamp': timestamp.isoformat()
            })
        }
        
        # Save to immutable file
        self._save_audit_entry(audit_entry)
        
        return entry_id
    
    def get_audit_trail(self, entity_id: str, entity_type: str = None, 
                       start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Retrieve audit trail for an entity
        """
        entries = []
        
        # Scan audit files for entries matching criteria
        for filename in os.listdir(self.audit_folder):
            if filename.endswith('.audit'):
                filepath = os.path.join(self.audit_folder, filename)
                with open(filepath, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry['entity_id'] == entity_id:
                                if entity_type and entry['entity_type'] != entity_type:
                                    continue
                                if start_date and entry['timestamp'] < start_date:
                                    continue
                                if end_date and entry['timestamp'] > end_date:
                                    continue
                                entries.append(entry)
                        except json.JSONDecodeError:
                            continue
        
        # Sort by timestamp
        entries.sort(key=lambda x: x['timestamp'])
        
        return entries
    
    def verify_integrity(self, entity_id: str) -> Dict:
        """
        Verify audit trail integrity for an entity
        """
        entries = self.get_audit_trail(entity_id)
        
        integrity_check = {
            'entity_id': entity_id,
            'total_entries': len(entries),
            'verified_entries': 0,
            'corrupted_entries': 0,
            'is_integrity_maintained': True
        }
        
        for entry in entries:
            calculated_hash = self._calculate_hash({
                'entity_type': entry['entity_type'],
                'entity_id': entry['entity_id'],
                'action': entry['action'],
                'details': json.dumps(entry['details'], sort_keys=True),
                'user_id': entry.get('user_id'),
                'timestamp': entry['timestamp']
            })
            
            if calculated_hash == entry.get('hash'):
                integrity_check['verified_entries'] += 1
            else:
                integrity_check['corrupted_entries'] += 1
                integrity_check['is_integrity_maintained'] = False
        
        return integrity_check
    
    def cleanup_expired_entries(self):
        """
        Remove audit entries older than 7 years
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_years * 365)
        cutoff_str = cutoff_date.isoformat()
        
        removed_count = 0
        
        for filename in os.listdir(self.audit_folder):
            if filename.endswith('.audit'):
                filepath = os.path.join(self.audit_folder, filename)
                temp_entries = []
                
                with open(filepath, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry['timestamp'] >= cutoff_str:
                                temp_entries.append(line.strip())
                        except json.JSONDecodeError:
                            continue
                
                # Rewrite file with only non-expired entries
                if len(temp_entries) < self._count_lines(filepath):
                    with open(filepath, 'w') as f:
                        for entry in temp_entries:
                            f.write(entry + '\n')
                    removed_count += (self._count_lines(filepath) - len(temp_entries))
        
        return removed_count
    
    def _generate_entry_id(self, entity_type: str, entity_id: str, timestamp: datetime) -> str:
        """Generate unique audit entry ID"""
        data = f"{entity_type}:{entity_id}:{timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _calculate_hash(self, data: Dict) -> str:
        """Calculate SHA-256 hash of audit data"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _save_audit_entry(self, entry: Dict):
        """Save audit entry to immutable file"""
        # Use date-based filename for organization
        date_str = entry['timestamp'][:10]  # YYYY-MM-DD
        filename = f"audit_{date_str}.audit"
        filepath = os.path.join(self.audit_folder, filename)
        
        with open(filepath, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def _count_lines(self, filepath: str) -> int:
        """Count lines in a file"""
        with open(filepath, 'r') as f:
            return sum(1 for _ in f)