"""
Database Module for SQLite Setup
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List
import logging

class Database:
    """
    SQLite database handler for CIS Dashboard
    """
    
    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Verifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verifications (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    document_paths TEXT,
                    extracted_data TEXT,
                    quality_score INTEGER,
                    risk_tier INTEGER,
                    decision TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # Disputes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS disputes (
                    id TEXT PRIMARY KEY,
                    original_verification_id TEXT,
                    customer_reason TEXT,
                    additional_documents TEXT,
                    status TEXT,
                    triage TEXT,
                    re_verification TEXT,
                    resolution TEXT,
                    audit_trail TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (original_verification_id) REFERENCES verifications (id)
                )
            ''')
            
            # Audit trail table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT,
                    entity_id TEXT,
                    action TEXT,
                    details TEXT,
                    user_id TEXT,
                    timestamp TEXT,
                    encrypted_data TEXT
                )
            ''')
            
            conn.commit()
    
    def save_verification(self, verification: Dict):
        """Save verification record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO verifications 
                (id, customer_id, document_paths, extracted_data, quality_score, 
                 risk_tier, decision, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                verification['id'],
                verification.get('customer_id'),
                json.dumps(verification.get('document_paths', [])),
                json.dumps(verification.get('extracted_data', {})),
                verification.get('quality_score', 0),
                verification.get('risk_tier', 1),
                verification.get('decision', 'UNKNOWN'),
                verification.get('created_at', datetime.utcnow().isoformat()),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
    
    def get_verification(self, verification_id: str) -> Dict:
        """Get verification by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM verifications WHERE id = ?', (verification_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'customer_id': row[1],
                    'document_paths': json.loads(row[2]) if row[2] else [],
                    'extracted_data': json.loads(row[3]) if row[3] else {},
                    'quality_score': row[4],
                    'risk_tier': row[5],
                    'decision': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                }
            return None
    
    def save_dispute(self, dispute: Dict):
        """Save dispute record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO disputes 
                (id, original_verification_id, customer_reason, additional_documents, 
                 status, triage, re_verification, resolution, audit_trail, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dispute['id'],
                dispute.get('original_verification_id'),
                dispute.get('customer_reason'),
                json.dumps(dispute.get('additional_documents', [])),
                dispute.get('status'),
                json.dumps(dispute.get('triage', {})),
                json.dumps(dispute.get('re_verification', {})),
                json.dumps(dispute.get('resolution', {})),
                json.dumps(dispute.get('audit_trail', [])),
                dispute.get('created_at'),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
    
    def get_dispute(self, dispute_id: str) -> Dict:
        """Get dispute by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM disputes WHERE id = ?', (dispute_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'original_verification_id': row[1],
                    'customer_reason': row[2],
                    'additional_documents': json.loads(row[3]) if row[3] else [],
                    'status': row[4],
                    'triage': json.loads(row[5]) if row[5] else {},
                    're_verification': json.loads(row[6]) if row[6] else {},
                    'resolution': json.loads(row[7]) if row[7] else {},
                    'audit_trail': json.loads(row[8]) if row[8] else [],
                    'created_at': row[9],
                    'updated_at': row[10]
                }
            return None
    
    def get_all_disputes(self) -> List[Dict]:
        """Get all disputes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM disputes')
            rows = cursor.fetchall()
            
            disputes = []
            for row in rows:
                disputes.append({
                    'id': row[0],
                    'original_verification_id': row[1],
                    'customer_reason': row[2],
                    'additional_documents': json.loads(row[3]) if row[3] else [],
                    'status': row[4],
                    'triage': json.loads(row[5]) if row[5] else {},
                    're_verification': json.loads(row[6]) if row[6] else {},
                    'resolution': json.loads(row[7]) if row[7] else {},
                    'audit_trail': json.loads(row[8]) if row[8] else [],
                    'created_at': row[9],
                    'updated_at': row[10]
                })
            return disputes
    
    def save_audit_entry(self, entity_type: str, entity_id: str, action: str, 
                        details: Dict, user_id: str = None):
        """Save audit trail entry"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_trail 
                (entity_type, entity_id, action, details, user_id, timestamp, encrypted_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_type,
                entity_id,
                action,
                json.dumps(details),
                user_id,
                datetime.utcnow().isoformat(),
                None  # Placeholder for encrypted data
            ))
            conn.commit()