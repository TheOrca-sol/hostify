from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
from ..utils.ocr import process_id_document
from ..utils.auth import verify_firebase_token

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload-id', methods=['POST'])
def upload_id_document():
    """
    Upload and process ID document using OCR
    """
    try:
        # Verify Firebase token (optional for now)
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            user_id = verify_firebase_token(token)
            if not user_id:
                return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Only PNG, JPG, and JPEG are allowed'}), 400
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Process the image using OCR
            extracted_data = process_id_document(temp_path)
            
            # Handle new response format
            if not extracted_data.get('success'):
                return jsonify({
                    'success': False,
                    'error': extracted_data.get('error', 'OCR processing failed'),
                    'confidence_score': extracted_data.get('confidence_score', 0),
                    'validation': extracted_data.get('validation', {})
                }), 500
            
            return jsonify({
                'success': True,
                'data': extracted_data.get('data', {}),
                'confidence_score': extracted_data.get('confidence_score', 0),
                'validation': extracted_data.get('validation', {}),
                'suggestions': extracted_data.get('suggestions', []),
                'processing_quality': extracted_data.get('processing_quality', {}),
                'message': 'ID document processed successfully'
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'OCR processing failed: {str(e)}'
            }), 500
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500 