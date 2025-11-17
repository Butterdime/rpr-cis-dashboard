"""
Flask UI Application
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

# Import our modules
from modules.document_processor import DocumentQualityAssessor, DocumentEnhancer, OCRExtractor
from modules.mismatch_detector import MismatchDetector, RiskAssessor
from modules.dispute_manager import DisputeManager
from modules.report_generator import ReportGenerator
from modules.audit_trail import AuditTrail
from database import Database
from config import Config

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/documents'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize components
config = Config()
db = Database(config.database_path)
audit_trail = AuditTrail(config.audit_folder)
dispute_manager = DisputeManager(db)
report_generator = ReportGenerator(db)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Document upload page"""
    if request.method == 'POST':
        files = request.files.getlist('documents')
        if not files or files[0].filename == '':
            return render_template('upload.html', error='No files selected')
        
        # Save uploaded files
        saved_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                saved_paths.append(filepath)
        
        if len(saved_paths) >= 2:
            # Redirect to verification
            return redirect(url_for('verify', doc1=saved_paths[0], doc2=saved_paths[1]))
        else:
            return render_template('upload.html', error='Please upload at least 2 documents')
    
    return render_template('upload.html')

@app.route('/verify')
def verify():
    """Perform verification"""
    doc1_path = request.args.get('doc1')
    doc2_path = request.args.get('doc2')
    
    if not doc1_path or not doc2_path:
        return render_template('error.html', message='Missing document paths')
    
    try:
        # Quality assessment
        assessor = DocumentQualityAssessor()
        quality1 = assessor.assess_document_quality(doc1_path)
        quality2 = assessor.assess_document_quality(doc2_path)
        
        # OCR extraction
        enhancer = DocumentEnhancer()
        ocr = OCRExtractor()
        
        enhanced1, _ = enhancer.enhance_document(doc1_path)
        enhanced2, _ = enhancer.enhance_document(doc2_path)
        
        extracted1 = ocr.extract_text_with_confidence(enhanced1)
        extracted2 = ocr.extract_text_with_confidence(enhanced2)
        
        structured1 = ocr.extract_structured_data(enhanced1, extracted1)
        structured2 = ocr.extract_structured_data(enhanced2, extracted2)
        
        # Mismatch detection
        detector = MismatchDetector()
        mismatches = detector.detect_mismatches(
            structured1.get('fields', {}), 
            structured2.get('fields', {})
        )
        
        # Risk assessment
        risk_assessor = RiskAssessor()
        risk_result = risk_assessor.assess_risk_tier(
            mismatches, 
            min(quality1.get('score', 0), quality2.get('score', 0))
        )
        
        # Save verification
        verification_id = f"ver_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        verification = {
            'id': verification_id,
            'customer_id': 'customer_123',  # Would come from session/user
            'document_paths': [doc1_path, doc2_path],
            'extracted_data': {
                'doc1': structured1,
                'doc2': structured2
            },
            'quality_score': min(quality1.get('score', 0), quality2.get('score', 0)),
            'risk_tier': risk_result['tier'],
            'decision': risk_result['decision'],
            'created_at': datetime.now().isoformat()
        }
        
        db.save_verification(verification)
        
        # Log to audit trail
        audit_trail.log_event(
            'verification', verification_id, 'CREATED',
            {'decision': risk_result['decision'], 'risk_tier': risk_result['tier']}
        )
        
        return render_template('result.html', 
                             verification=verification,
                             quality1=quality1,
                             quality2=quality2,
                             mismatches=mismatches,
                             risk=risk_result)
    
    except Exception as e:
        app.logger.error(f"Verification failed: {str(e)}")
        return render_template('error.html', message=f'Verification failed: {str(e)}')

@app.route('/dispute', methods=['GET', 'POST'])
def dispute():
    """Dispute submission"""
    if request.method == 'POST':
        verification_id = request.form.get('verification_id')
        reason = request.form.get('reason')
        additional_docs = request.files.getlist('additional_docs')
        
        # Save additional documents
        additional_paths = []
        for file in additional_docs:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                additional_paths.append(filepath)
        
        # Create dispute
        dispute = dispute_manager.create_dispute(
            verification_id, reason, additional_paths
        )
        
        # Log to audit trail
        audit_trail.log_event(
            'dispute', dispute['id'], 'CREATED',
            {'reason': reason, 'verification_id': verification_id}
        )
        
        return render_template('dispute_submitted.html', dispute=dispute)
    
    verification_id = request.args.get('verification_id')
    return render_template('dispute.html', verification_id=verification_id)

@app.route('/report/<verification_id>')
def report(verification_id):
    """Generate report"""
    report_data = report_generator.generate_internal_report(verification_id)
    return jsonify(report_data)

def allowed_file(filename):
    """Check if file type is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)