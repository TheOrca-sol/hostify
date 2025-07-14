import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import re
from datetime import datetime
import logging
import numpy as np
import cv2

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_id_document(image_path):
    """
    Enhanced process ID document with validation and structure analysis
    """
    try:
        logger.info(f"Processing ID document: {image_path}")
        
        # Load and enhance image
        image = Image.open(image_path)
        logger.debug(f"Original image size: {image.size}, mode: {image.mode}")
        
        # Try different preprocessing methods and configurations
        best_score = 0
        best_result = None
        best_method = None
        best_config = None
        
        # Preprocessing methods
        methods = {
            'enhanced': enhance_image_for_ocr,
            'simple': simple_preprocessing,
            'high_contrast': high_contrast_preprocessing,
            'binary': binary_preprocessing
        }
        
        # OCR configurations
        configs = [
            '--oem 3 --psm 6',  # Uniform block of text
            '--oem 3 --psm 3',  # Fully automatic page segmentation
            '--oem 3 --psm 11', # Sparse text
        ]
        
        for method_name, method_func in methods.items():
            try:
                processed_image = method_func(image)
                logger.debug(f"Enhanced image for OCR: {processed_image.size}, mode: {processed_image.mode}")
                
                for config in configs:
                    try:
                        # Extract text
                        text = pytesseract.image_to_string(processed_image, config=config, lang='eng+fra')
                        
                        if text.strip():
                            # Calculate quality score
                            score = calculate_text_quality_score(text)
                            
                            if score > best_score:
                                best_score = score
                                best_result = text
                                best_method = method_name
                                best_config = config
                                logger.debug(f"New best result - Method: {method_name}, Config: {config}, Score: {score}")
                    except Exception as e:
                        logger.error(f"Error with config {config}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error with method {method_name}: {e}")
                continue
        
        if not best_result:
            logger.error("No OCR results obtained")
            return {
                'success': False,
                'error': 'OCR processing failed',
                'data': {},
                'validation': {'is_valid': False, 'issues': ['No text could be extracted from document']},
                'confidence_score': 0
            }
        
        logger.debug(f"Best method: {best_method}, Config: {best_config}")
        logger.debug(f"OCR Extracted Text: {repr(best_result)}")
        
        # Process text into structured data
        lines = [line.strip() for line in best_result.split('\n') if line.strip()]
        logger.debug(f"OCR Lines: {lines}")
        
        # Extract structured information
        extracted_data = extract_info_from_text(lines, best_result)
        logger.debug(f"Extracted Data: {extracted_data}")
        
        # Validate extracted data
        validation_results = validate_extracted_data(extracted_data)
        logger.debug(f"Validation Results: {validation_results}")
        
        # Cross-validate fields
        cross_validation = cross_validate_fields(extracted_data)
        logger.debug(f"Cross-validation: {cross_validation}")
        
        # Combine confidence scores
        total_confidence = (validation_results['confidence_score'] + cross_validation['consistency_score']) / 2
        
        # Prepare response
        response = {
            'success': True,
            'data': extracted_data,
            'validation': validation_results,
            'cross_validation': cross_validation,
            'confidence_score': round(total_confidence, 2),
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing ID document: {e}")
        return {
            'success': False,
            'error': f'Processing failed: {str(e)}',
            'data': {},
            'validation': {'is_valid': False, 'issues': ['Processing error occurred']},
            'confidence_score': 0
        }

def calculate_text_quality_score(text):
    """Calculate a quality score for OCR text"""
    if not text or not text.strip():
        return 0
    
    score = 0
    text_clean = text.strip()
    
    # Length bonus
    score += min(len(text_clean), 100)
    
    # Letter ratio bonus
    letters = sum(1 for c in text_clean if c.isalpha())
    if len(text_clean) > 0:
        letter_ratio = letters / len(text_clean)
        score += letter_ratio * 50
    
    # Word count bonus
    words = text_clean.split()
    recognizable_words = sum(1 for word in words if len(word) > 2 and word.isalpha())
    score += recognizable_words * 10
    
    return score

def simple_preprocessing(image):
    """Simple preprocessing - just resize and convert to grayscale"""
    image = image.convert('L')
    return image.convert('RGB')

def high_contrast_preprocessing(image):
    """High contrast preprocessing"""
    image = image.convert('L')
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    return image.convert('RGB')

def binary_preprocessing(image):
    """Binary (black and white) preprocessing"""
    image = image.convert('L')
    img_array = np.array(image)
    binary_array = cv2.adaptiveThreshold(
        img_array, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    image = Image.fromarray(binary_array, mode='L')
    return image.convert('RGB')

def enhance_image_for_ocr(image):
    """
    Enhance image quality for better OCR results with a simplified and robust pipeline.
    """
    if image.mode not in ('RGB', 'L'):
        image = image.convert('RGB')

    gray_image = image.convert('L')
    img_array = np.array(gray_image)

    denoised_array = cv2.bilateralFilter(img_array, 9, 75, 75)

    binary_array = cv2.adaptiveThreshold(
        denoised_array, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    enhanced_image = Image.fromarray(binary_array, mode='L')
    return enhanced_image.convert('RGB')

def extract_info_from_text(lines, full_text):
    """
    Extract information from OCR text lines with a more general and robust approach.
    """
    extracted = {
        'full_name': '',
        'cin_or_passport': '',
        'birthdate': '',
        'nationality': '',
        'document_type': ''
    }

    # General keywords to ignore when looking for names
    ID_KEYWORDS = [
        'id', 'identity', 'card', 'passport', 'document', 'national',
        'republic', 'government', 'specimen', 'personal', 'number',
        'royaume', 'maroc', 'carte', 'nationale', 'identite', 'passeport',
        'république', 'gouvernement', 'numéro', 'nom', 'prénom',
        'surname', 'given name', 'date of birth', 'nationality'
    ]
    
    # Document type detection
    text_lower = full_text.lower()
    if 'passport' in text_lower or 'passeport' in text_lower:
        extracted['document_type'] = 'Passport'
    elif 'identit' in text_lower or 'card' in text_lower:
        extracted['document_type'] = 'ID Card'

    # Date of Birth Extraction
    date_patterns = [
        r'(?i)(?:date of birth|birthdate|né\s*le|date\s*de\s*naissance)\s*:?\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})',
        r'\b([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})\b'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, full_text)
        if match:
            date_str = match.group(1) if len(match.groups()) > 0 else match.group(0)
            try:
                # Normalize and parse the date
                normalized_date = re.sub(r'[./]', '-', date_str)
                dt_obj = None
                parts = normalized_date.split('-')
                if len(parts[2]) == 2:
                    parts[2] = '19' + parts[2] if int(parts[2]) > 25 else '20' + parts[2]
                    normalized_date = '-'.join(parts)

                for fmt in ('%d-%m-%Y', '%m-%d-%Y'):
                    try:
                        dt_obj = datetime.strptime(normalized_date, fmt)
                        break
                    except ValueError:
                        pass
                
                if dt_obj and 1920 < dt_obj.year < datetime.now().year:
                    extracted['birthdate'] = dt_obj.strftime('%Y-%m-%d')
                    break
            except (ValueError, TypeError):
                continue

    # Name Extraction
    name_candidates = []
    for line in lines:
        words = line.split()
        line_lower = line.lower()
        if 2 <= len(words) <= 5 and all(word.isalpha() or word in ["-", "'"] for word in words):
            if not any(keyword in line_lower for keyword in ID_KEYWORDS):
                name_candidates.append(line)

    if name_candidates:
        extracted['full_name'] = max(name_candidates, key=len)

    # ID Number Extraction
    id_patterns = [
        r'(?i)(?:passport|id\s*number|cin|n°)\s*:?\s*([A-Z0-9<]{7,15})',
        r'\b[A-Z]{1,2}[0-9]{6,9}\b',
        r'\b[A-Z0-9<]{9,15}\b'
    ]
    for pattern in id_patterns:
        match = re.search(pattern, full_text)
        if match:
            id_str = match.group(1) if len(match.groups()) > 0 else match.group(0)
            id_str = id_str.replace('<', '')
            if len(id_str) > 5:
                extracted['cin_or_passport'] = id_str
                break
            
    return extracted

def validate_extracted_data(extracted_data):
    """
    Validate extracted data for consistency and accuracy.
    """
    validation_results = {
        'is_valid': True,
        'confidence_score': 0.0,
        'issues': [],
        'suggestions': []
    }
    
    if extracted_data.get('full_name'):
        validation_results['confidence_score'] += 33
    else:
        validation_results['issues'].append("No name extracted")
        validation_results['is_valid'] = False

    if extracted_data.get('cin_or_passport'):
        validation_results['confidence_score'] += 33
    else:
        validation_results['issues'].append("No ID number extracted")
        validation_results['is_valid'] = False

    if extracted_data.get('birthdate'):
        validation_results['confidence_score'] += 34
    else:
        validation_results['issues'].append("No birth date extracted")
        validation_results['is_valid'] = False

    if validation_results['confidence_score'] < 50:
        validation_results['is_valid'] = False
        validation_results['suggestions'].append("Low confidence - manual review recommended")
    
    return validation_results

def cross_validate_fields(extracted_data):
    """
    Cross-validate fields against each other for consistency
    """
    cross_validation = {
        'consistency_score': 0.0,
        'cross_checks': []
    }
    
    if extracted_data.get('document_type') == 'CIN' and extracted_data.get('cin_or_passport'):
        id_num = extracted_data['cin_or_passport']
        if re.match(r'^[A-Z]{1,2}[0-9]{6,9}$', id_num):
            cross_validation['consistency_score'] += 15
            cross_validation['cross_checks'].append("ID format consistent with CIN document type")

    return cross_validation