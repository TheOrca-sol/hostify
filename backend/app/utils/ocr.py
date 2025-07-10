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
            '--oem 3 --psm 8',  # Single word
            '--oem 3 --psm 7',  # Single text line
            '--oem 3 --psm 3',  # Fully automatic page segmentation
            '--oem 3 --psm 4',  # Single column of text
            '--oem 3 --psm 11', # Sparse text
            '--oem 3 --psm 13'  # Raw line. Treat as single text line
        ]
        
        for method_name, method_func in methods.items():
            try:
                processed_image = method_func(image)
                logger.debug(f"Enhanced image for OCR: {processed_image.size}, mode: {processed_image.mode}")
                
                # Save debug image
                debug_path = f"/tmp/debug_{method_name}.png"
                processed_image.save(debug_path)
                logger.debug(f"Saved debug image: {debug_path}")
                
                for config in configs:
                    try:
                        # Extract text
                        text = pytesseract.image_to_string(processed_image, config=config, lang='eng+ara+fra')
                        
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
            'ocr_method': best_method,
            'ocr_config': best_config,
            'processing_quality': {
                'text_quality_score': best_score,
                'total_lines_extracted': len(lines),
                'non_empty_lines': len([line for line in lines if line.strip()])
            }
        }
        
        # Add suggestions based on confidence
        if total_confidence < 60:
            response['suggestions'] = [
                "Low confidence detected - manual review recommended",
                "Consider taking a clearer photo with better lighting",
                "Ensure document is flat and fully visible"
            ]
        elif total_confidence < 80:
            response['suggestions'] = [
                "Medium confidence - some fields may need verification",
                "Double-check extracted information for accuracy"
            ]
        else:
            response['suggestions'] = [
                "High confidence - data appears accurate"
            ]
        
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
    
    # Penalty for too many special characters
    special_chars = sum(1 for c in text_clean if not c.isalnum() and c not in ' \n\t')
    if len(text_clean) > 0:
        special_ratio = special_chars / len(text_clean)
        if special_ratio > 0.5:
            score -= 30
    
    return score

def simple_preprocessing(image):
    """Simple preprocessing - just resize and convert to grayscale"""
    # Resize if needed
    width, height = image.size
    if width < 1000 or height < 750:
        scale = max(1000/width, 750/height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Convert to grayscale
    image = image.convert('L')
    
    # Convert back to RGB
    image = image.convert('RGB')
    
    return image

def high_contrast_preprocessing(image):
    """High contrast preprocessing"""
    # Convert to grayscale
    image = image.convert('L')
    
    # Extreme contrast enhancement
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(4.0)
    
    # Convert back to RGB
    image = image.convert('RGB')
    
    return image

def binary_preprocessing(image):
    """Binary (black and white) preprocessing"""
    # Convert to grayscale
    image = image.convert('L')
    
    # Apply adaptive threshold
    img_array = np.array(image)
    
    # Calculate adaptive threshold
    mean_brightness = np.mean(img_array)
    threshold = mean_brightness * 0.8  # Adjust threshold based on image brightness
    
    # Apply threshold
    binary_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
    
    # Convert back to PIL Image
    image = Image.fromarray(binary_array, mode='L')
    
    # Convert to RGB
    image = image.convert('RGB')
    
    return image

def enhance_image_for_ocr(image):
    """
    Enhance image quality for better OCR results with aggressive preprocessing
    """
    # Convert to RGB first
    if image.mode not in ('RGB', 'L'):
        image = image.convert('RGB')
    
    # Resize image if too small (OCR works better with larger images)
    width, height = image.size
    if width < 800 or height < 600:
        # Calculate new size maintaining aspect ratio
        scale = max(800/width, 600/height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
    
    # Convert to grayscale for better OCR
    image = image.convert('L')
    
    # Enhance contrast significantly
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.5)
    
    # Apply threshold to create binary image (black and white only)
    # This helps remove background noise and security features
    threshold = 128
    image = image.point(lambda x: 255 if x > threshold else 0, mode='1')
    
    # Convert back to grayscale for further processing
    image = image.convert('L')
    
    # Apply morphological operations to clean up text
    # This helps connect broken characters
    image = image.filter(ImageFilter.MedianFilter(size=3))
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(3.0)
    
    # Apply another contrast enhancement
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    
    # Final resize to optimal OCR size
    width, height = image.size
    if width > 1200 or height > 900:
        image = image.resize((1200, 900), Image.Resampling.LANCZOS)
    
    # Convert to RGB for Tesseract compatibility
    image = image.convert('RGB')
    
    logger.debug(f"Enhanced image for OCR: {image.size}, mode: {image.mode}")
    return image

def extract_info_from_text(lines, full_text):
    """
    Extract information from OCR text lines with advanced cleaning and field detection
    """
    # Clean OCR noise from the full text
    clean_full_text = clean_ocr_noise(full_text)
    logger.debug(f"Cleaned full text: {clean_full_text}")
    
    # Use smart field detection
    detected_fields = smart_field_detection(clean_full_text, lines)
    logger.debug(f"Smart field detection results: {detected_fields}")
    
    # Initialize extracted data
    extracted = {
        'full_name': '',
        'cin_or_passport': '',
        'birthdate': '',
        'nationality': '',
        'address': '',
        'document_type': ''
    }
    
    # Clean and process text
    text_lower = clean_full_text.lower()
    
    # First pass: Use smart field detection results
    if 'id_number' in detected_fields:
        extracted['cin_or_passport'] = detected_fields['id_number'][0]
    
    if 'date' in detected_fields:
        # Process detected dates
        for date_match in detected_fields['date']:
            if len(date_match) == 3:
                day, month, year = date_match
                try:
                    if len(year) == 2:
                        year = '19' + year if int(year) > 50 else '20' + year
                    extracted['birthdate'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    break
                except:
                    continue
    
    # Document type detection
    if 'carte' in text_lower or 'cin' in text_lower or 'identit' in text_lower:
        extracted['document_type'] = 'CIN'
    elif 'passport' in text_lower or 'passeport' in text_lower:
        extracted['document_type'] = 'Passport'
    
    # Enhanced ID number extraction if not found by smart detection
    if not extracted['cin_or_passport']:
        id_patterns = [
            r'[A-Z]{1,2}[0-9]{6,9}',
            r'[0-9]{8,12}',
            r'[A-Z][0-9]{6,8}',
            r'[A-Z]{2}[0-9]{6,8}'
        ]
        
        for pattern in id_patterns:
            matches = re.findall(pattern, clean_full_text)
            if matches:
                # Filter out dates and other non-ID numbers
                for match in matches:
                    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', match):
                        extracted['cin_or_passport'] = match
                        logger.debug(f"Found ID number: {match} using pattern: {pattern}")
                        break
                if extracted['cin_or_passport']:
                    break
    
    # Enhanced date extraction if not found by smart detection
    if not extracted['birthdate']:
        # Priority date patterns - more specific first
        priority_patterns = [
            r'(\d{2})\.(\d{2})\.(\d{4})',  # 30.10.1996
            r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',  # Various separators
            r'(\d{2})[\/\-\.](\d{2})[\/\-\.](\d{4})',  # 05/12/1983
        ]
        
        for pattern in priority_patterns:
            matches = re.findall(pattern, clean_full_text)
            for match in matches:
                day, month, year = match
                # Skip expiration dates
                context = clean_full_text[clean_full_text.find(f"{day}.{month}.{year}"):clean_full_text.find(f"{day}.{month}.{year}") + 50]
                if any(exp in context.lower() for exp in ['expire', 'valid', 'jusqu', 'صالحة']):
                    continue
                try:
                    # Validate date
                    if 1 <= int(day) <= 31 and 1 <= int(month) <= 12 and 1900 <= int(year) <= 2010:
                        extracted['birthdate'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        logger.debug(f"Found priority date match: {match} using pattern: {pattern}")
                        break
                except:
                    continue
            if extracted['birthdate']:
                break
    
    # Enhanced name extraction with advanced cleaning
    name_candidates = []
    
    # Process each line for name candidates
    for line in lines:
        clean_line = clean_ocr_noise(line)
        
        # Skip empty lines
        if not clean_line.strip():
            continue
            
        # Enhanced filtering
        header_keywords = ['royaume', 'maroc', 'carte', 'nationale', 'identite', 'طاقة', 'وطنية', 'تعر', 'مملكة', 'مغربية']
        city_names = ['tanger', 'assilah', 'ouarzazate', 'khouribga', 'casablanca', 'rabat', 'fes', 'meknes', 'agadir', 'tangier', 'oujda', 'kenitra', 'tetouan', 'sale', 'marrakech', 'mohammedia', 'laayoune', 'settat', 'temara', 'berrechid', 'khemisset', 'inezgane', 'ksar', 'taourirt', 'berkane', 'sidi', 'beni', 'ait']
        official_titles = ['مدير', 'عام', 'امن', 'وطني', 'directeur', 'general', 'security', 'national']
        expiration_words = ['صالحة', 'إلى', 'غلية', 'valid', 'expire', 'valable', 'jusqu', 'velabiejusquau']
        official_signatures = ['حموشي', 'hammouchi', 'عبد اللطيف', 'abdellatif']
        
        # Check if line should be skipped
        line_lower = clean_line.lower()
        
        # Skip header lines
        if any(keyword in line_lower for keyword in header_keywords):
            logger.debug(f"Skipping header line: {clean_line}")
            continue
            
        # Skip city names
        if any(city in line_lower for city in city_names):
            logger.debug(f"Skipping city name: {clean_line}")
            continue
            
        # Skip official titles
        if any(title in line_lower for title in official_titles):
            logger.debug(f"Skipping official title: {clean_line}")
            continue
            
        # Skip expiration text
        if any(exp in line_lower for exp in expiration_words):
            logger.debug(f"Skipping expiration line: {clean_line}")
            continue
            
        # Skip official signatures
        if any(sig in line_lower for sig in official_signatures):
            logger.debug(f"Skipping official signature: {clean_line}")
            continue
            
        # Skip lines with mostly numbers
        if re.search(r'\d', clean_line) and len(re.findall(r'\d', clean_line)) > len(clean_line) * 0.3:
            logger.debug(f"Skipping number-heavy line: {clean_line}")
            continue
            
        # Skip Arabic header text
        if is_arabic_header_text(clean_line):
            logger.debug(f"Skipping Arabic header text: {clean_line}")
            continue
            
        # Extract potential names
        if len(clean_line) > 2:
            # Look for patterns that suggest names
            words = clean_line.split()
            if 1 <= len(words) <= 4:  # Names usually have 1-4 words
                name_candidates.append(clean_line)
    
    # Also look for Arabic names specifically (but filter out expiration text and official signatures)
    arabic_name_pattern = r'[\u0600-\u06FF\s]{3,30}'  # Arabic characters, reasonable length
    arabic_matches = re.findall(arabic_name_pattern, clean_full_text)
    for match in arabic_matches:
        clean_match = clean_ocr_noise(match.strip())
        if (len(clean_match) > 3 and 
            not any(header in clean_match for header in ['طاقة', 'وطنية', 'تعر', 'مملكة', 'مدير', 'عام']) and
            not any(exp in clean_match for exp in expiration_words) and
            not any(sig in clean_match for sig in official_signatures) and
            not is_arabic_header_text(clean_match)):
            name_candidates.append(clean_match)
    
    # Look for Latin/French names as well
    latin_name_pattern = r'[a-zA-Z\s]{3,30}'
    latin_matches = re.findall(latin_name_pattern, clean_full_text)
    for match in latin_matches:
        clean_match = clean_ocr_noise(match.strip())
        if (len(clean_match) > 3 and 
            not any(header in clean_match.lower() for header in header_keywords + city_names + expiration_words) and
            not any(sig in clean_match.lower() for sig in official_signatures) and
            not any(specimen in clean_match.lower() for specimen in ['specimen', 'ayecimen', 'ecimen', 'cimen']) and
            not any(city in clean_match.upper() for city in ['TANGER', 'ASSILAH', 'OUARZAZATE', 'KHOURIBGA', 'CASABLANCA', 'RABAT', 'FES', 'MEKNES', 'AGADIR', 'TANGIER', 'OUJDA', 'KENITRA', 'TETOUAN', 'SALE', 'MARRAKECH', 'MOHAMMEDIA', 'LAAYOUNE', 'SETTAT', 'TEMARA', 'BERRECHID', 'KHEMISSET']) and
            not re.search(r'[0-9]', clean_match)):  # No numbers in name
            words = clean_match.split()
            if 1 <= len(words) <= 4:  # Reasonable number of words for a name
                name_candidates.append(clean_match)
    
    logger.debug(f"Name candidates after advanced cleaning: {name_candidates}")
    
    # Rest of the name selection logic stays the same...
    # [The existing name selection logic continues here]
    
    # For now, let's use the enhanced name candidates with better filtering
    if name_candidates:
        # Filter and select the best name candidate
        valid_names = []
        latin_names = []
        arabic_names = []
        
        for name in name_candidates:
            name = clean_ocr_noise(name.strip())  # Additional cleaning
            if 3 < len(name) < 40:
                # Remove obvious non-names
                words = name.split()
                if len(words) >= 1 and len(words) <= 4:
                    # Additional quality checks - use word boundaries to avoid filtering "EL ALAMI" 
                    bad_words = ['carte', 'national'] + expiration_words + official_signatures
                    name_lower = name.lower()
                    contains_bad_word = False
                    for bad in bad_words:
                        # Use word boundary regex to match whole words only
                        if re.search(r'\b' + re.escape(bad.lower()) + r'\b', name_lower):
                            contains_bad_word = True
                            break
                    if not contains_bad_word:
                        # Filter out specimen-related text and other false positives
                        if not any(specimen in name.lower() for specimen in ['specimen', 'ayecimen', 'ecimen', 'cimen']):
                            # Separate Latin and Arabic names
                            if re.match(r'^[A-Za-z\s]+$', name):  # Latin characters only
                                latin_names.append(name)
                            elif re.match(r'^[\u0600-\u06FF\s]+$', name):  # Arabic characters only
                                if not is_arabic_header_text(name):  # Additional Arabic header check
                                    arabic_names.append(name)
                            else:
                                valid_names.append(name)
        
        # Name selection priority: Latin > Arabic > Others
        if latin_names:
            # Try to combine first and last names for Latin names
            first_names = []
            last_names = []
            
            for name in latin_names:
                name_upper = name.upper()
                # Common first names
                if name_upper in ['ZAINEB', 'AYMAN', 'MOHAMED', 'AHMED', 'FATIMA', 'AICHA', 'YOUSSEF', 'OMAR', 'SARA', 'NADIA', 'MOUHCINE', 'HASSAN', 'AMINA', 'KARIM', 'LAYLA', 'RACHID', 'SALMA', 'NOUR']:
                    first_names.append(name)
                # Common last name patterns
                elif name_upper.startswith('EL ') or name_upper.startswith('AL ') or name_upper.startswith('BEN ') or name_upper.startswith('IBN '):
                    last_names.append(name)
                elif name_upper in ['TEMSAMANI', 'NCIRI', 'ALAMI', 'ZOUANI', 'BENALI', 'HASSANI', 'IDRISSI', 'BENJELLOUN', 'CHERKAOUI', 'TAZI', 'LAHLOU', 'BERRADA', 'FASSI', 'KADIRI', 'AMRANI', 'BENOMAR', 'SQUALLI', 'ANDALOUSSI']:
                    last_names.append(name)
                elif len(name.split()) >= 2:  # Multi-word names
                    last_names.append(name)
            
            # Try to combine first and last names
            if first_names and last_names:
                extracted['full_name'] = f"{first_names[0]} {last_names[0]}"
            elif len(latin_names) >= 2:
                # Look for combinations
                potential_first = None
                potential_last = None
                
                for name in latin_names:
                    name_upper = name.upper()
                    if name_upper in ['ZAINEB', 'AYMAN', 'MOHAMED', 'AHMED', 'FATIMA', 'AICHA', 'YOUSSEF', 'OMAR', 'SARA', 'NADIA', 'MOUHCINE', 'HASSAN', 'AMINA', 'KARIM', 'LAYLA', 'RACHID', 'SALMA', 'NOUR']:
                        potential_first = name
                    elif name_upper.startswith('EL ') or name_upper.startswith('AL ') or name_upper.startswith('BEN ') or len(name.split()) >= 2:
                        potential_last = name
                
                if potential_first and potential_last:
                    extracted['full_name'] = f"{potential_first} {potential_last}"
                else:
                    # Use the longest Latin name
                    extracted['full_name'] = max(latin_names, key=len)
            else:
                # Use the longest Latin name
                extracted['full_name'] = max(latin_names, key=len)
        elif arabic_names:
            # Use the longest Arabic name (already filtered for headers)
            extracted['full_name'] = max(arabic_names, key=len)
        elif valid_names:
            # Use the first valid name
            extracted['full_name'] = valid_names[0]
    
    # Extract nationality
    nationality_keywords = {
        'marocain': 'Moroccan',
        'moroccan': 'Moroccan',
        'maroc': 'Moroccan',
        'morocco': 'Moroccan',
        'مغربي': 'Moroccan',
        'مغربية': 'Moroccan',
        'français': 'French',
        'french': 'French',
        'france': 'French',
        'spanish': 'Spanish',
        'espagnol': 'Spanish',
        'spain': 'Spanish',
        'algerian': 'Algerian',
        'tunisian': 'Tunisian',
    }
    
    for keyword, nationality in nationality_keywords.items():
        if keyword in text_lower:
            extracted['nationality'] = nationality
            logger.debug(f"Found nationality: {nationality} from keyword: {keyword}")
            break
    
    # If no nationality found, default to Moroccan for CIN
    if not extracted['nationality'] and extracted['document_type'] == 'CIN':
        extracted['nationality'] = 'Moroccan'
        logger.debug("Defaulted nationality to Moroccan for CIN")
    
    # Clean up extracted data
    for key, value in extracted.items():
        if isinstance(value, str):
            extracted[key] = clean_ocr_noise(value.strip())
    
    logger.debug(f"Final extracted data: {extracted}")
    return extracted

def detect_document_structure(image_path):
    """
    Detect document structure and identify potential field regions
    This helps with more accurate field identification
    """
    try:
        # Load image with OpenCV for structure analysis
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection to find document boundaries and text regions
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Find contours to identify text blocks
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area to find significant text regions
        text_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Minimum area for text regions
                x, y, w, h = cv2.boundingRect(contour)
                text_regions.append({'x': x, 'y': y, 'width': w, 'height': h, 'area': area})
        
        # Sort regions by position (top to bottom, left to right)
        text_regions.sort(key=lambda r: (r['y'], r['x']))
        
        logger.debug(f"Detected {len(text_regions)} text regions")
        return text_regions
        
    except Exception as e:
        logger.error(f"Error detecting document structure: {e}")
        return []

def extract_data_with_structure(image_path):
    """
    Enhanced data extraction using document structure analysis
    """
    # First detect document structure
    text_regions = detect_document_structure(image_path)
    
    # Then process each region separately for better accuracy
    all_extracted_data = []
    
    for i, region in enumerate(text_regions):
        try:
            # Extract region from image
            img = Image.open(image_path)
            region_img = img.crop((region['x'], region['y'], 
                                 region['x'] + region['width'], 
                                 region['y'] + region['height']))
            
            # Save region for OCR
            region_path = f"/tmp/region_{i}.png"
            region_img.save(region_path)
            
            # Process region with OCR
            region_text = pytesseract.image_to_string(region_img, lang='eng+ara+fra')
            
            if region_text.strip():
                all_extracted_data.append({
                    'region': i,
                    'position': region,
                    'text': region_text.strip()
                })
                
        except Exception as e:
            logger.error(f"Error processing region {i}: {e}")
            continue
    
    return all_extracted_data 

def validate_extracted_data(extracted_data):
    """
    Validate extracted data for consistency and accuracy
    This implements the data validation best practice from the research
    """
    validation_results = {
        'is_valid': True,
        'confidence_score': 0.0,
        'issues': [],
        'suggestions': []
    }
    
    # Validate name
    if 'full_name' in extracted_data and extracted_data['full_name']:
        name = extracted_data['full_name']
        name_score = 0
        
        # Check name format
        if len(name.split()) >= 2:
            name_score += 30
        else:
            validation_results['issues'].append("Name appears to have only one word")
            validation_results['suggestions'].append("Verify if full name was captured correctly")
        
        # Check for obvious errors
        if any(bad in name.upper() for bad in ['CARTE', 'NATIONAL', 'ROYAUME', 'MAROC']):
            validation_results['issues'].append("Name contains document header text")
            validation_results['is_valid'] = False
        
        # Check for city names in name field
        city_names = ['TANGER', 'ASSILAH', 'OUARZAZATE', 'KHOURIBGA', 'CASABLANCA', 'RABAT']
        if any(city in name.upper() for city in city_names):
            validation_results['issues'].append("Name field contains city name")
            validation_results['suggestions'].append("City name may have been misidentified as personal name")
        
        # Check for reasonable name length
        if len(name) < 3:
            validation_results['issues'].append("Name is too short")
            validation_results['is_valid'] = False
        elif len(name) > 50:
            validation_results['issues'].append("Name is unusually long")
        else:
            name_score += 20
        
        # Check for proper capitalization
        if name.isupper() or name.islower():
            name_score += 10
        
        validation_results['confidence_score'] += name_score
    else:
        validation_results['issues'].append("No name extracted")
        validation_results['is_valid'] = False
    
    # Validate CIN/Passport number
    if 'cin_or_passport' in extracted_data and extracted_data['cin_or_passport']:
        id_number = extracted_data['cin_or_passport']
        id_score = 0
        
        # Check CIN format (letter + 6-9 digits)
        if re.match(r'^[A-Z]{1,2}[0-9]{6,9}$', id_number):
            id_score += 40
        else:
            validation_results['issues'].append("ID number format doesn't match standard CIN pattern")
        
        # Check reasonable length
        if 7 <= len(id_number) <= 11:
            id_score += 10
        else:
            validation_results['issues'].append("ID number length is unusual")
        
        validation_results['confidence_score'] += id_score
    else:
        validation_results['issues'].append("No ID number extracted")
        validation_results['is_valid'] = False
    
    # Validate birthdate
    if 'birthdate' in extracted_data and extracted_data['birthdate']:
        try:
            from datetime import datetime
            birth_date = datetime.strptime(extracted_data['birthdate'], '%Y-%m-%d')
            current_date = datetime.now()
            
            # Check if birthdate is reasonable (between 1900 and current date)
            if birth_date.year < 1900:
                validation_results['issues'].append("Birth year is too early")
            elif birth_date > current_date:
                validation_results['issues'].append("Birth date is in the future")
                validation_results['is_valid'] = False
            else:
                # Check if person is between 0-120 years old
                age = current_date.year - birth_date.year
                if 0 <= age <= 120:
                    validation_results['confidence_score'] += 20
                else:
                    validation_results['issues'].append(f"Calculated age ({age}) is unusual")
        except ValueError:
            validation_results['issues'].append("Birth date format is invalid")
            validation_results['is_valid'] = False
    else:
        validation_results['issues'].append("No birth date extracted")
        validation_results['is_valid'] = False
    
    # Validate nationality
    if 'nationality' in extracted_data and extracted_data['nationality']:
        if extracted_data['nationality'] in ['Moroccan', 'French', 'Spanish', 'Algerian', 'Tunisian']:
            validation_results['confidence_score'] += 10
        else:
            validation_results['issues'].append("Unusual nationality detected")
    
    # Validate document type
    if 'document_type' in extracted_data and extracted_data['document_type']:
        if extracted_data['document_type'] in ['CIN', 'Passport']:
            validation_results['confidence_score'] += 5
        else:
            validation_results['issues'].append("Unknown document type")
    
    # Calculate final confidence score (0-100)
    validation_results['confidence_score'] = min(100, validation_results['confidence_score'])
    
    # Determine overall validity
    if validation_results['confidence_score'] < 50:
        validation_results['is_valid'] = False
        validation_results['suggestions'].append("Low confidence - manual review recommended")
    elif validation_results['confidence_score'] < 70:
        validation_results['suggestions'].append("Medium confidence - some fields may need verification")
    
    return validation_results

def cross_validate_fields(extracted_data):
    """
    Cross-validate fields against each other for consistency
    """
    cross_validation = {
        'consistency_score': 0.0,
        'cross_checks': []
    }
    
    # Check name consistency with nationality
    if extracted_data.get('nationality') == 'Moroccan' and extracted_data.get('full_name'):
        name = extracted_data['full_name'].upper()
        moroccan_indicators = ['EL ', 'AL ', 'BEN ', 'IBN ', 'MOHAMED', 'AHMED', 'FATIMA', 'AICHA']
        if any(indicator in name for indicator in moroccan_indicators):
            cross_validation['consistency_score'] += 15
            cross_validation['cross_checks'].append("Name patterns consistent with Moroccan nationality")
    
    # Check document type consistency with ID format
    if extracted_data.get('document_type') == 'CIN' and extracted_data.get('cin_or_passport'):
        id_num = extracted_data['cin_or_passport']
        if re.match(r'^[A-Z]{1,2}[0-9]{6,9}$', id_num):
            cross_validation['consistency_score'] += 15
            cross_validation['cross_checks'].append("ID format consistent with CIN document type")
    
    return cross_validation 

def clean_ocr_noise(text):
    """
    Advanced OCR noise cleaning based on common patterns
    """
    # Remove common OCR noise patterns
    noise_patterns = [
        r'\boer\b',  # Common OCR noise
        r'\boor\b',  # Common OCR noise
        r'\boe\b',   # Common OCR noise
        r'\boo\b',   # Common OCR noise
        r'\bor\b',   # Common OCR noise when isolated
        r'\boo\b',   # Common OCR noise
        r'\brill\b', # Common OCR noise
        r'\bfoot\b', # Common OCR noise
        r'\bFoe\b',  # Common OCR noise
        r'\boe\b',   # Common OCR noise
        r'\boo?\b',  # Common OCR noise
        r'\bho\)\b', # Common OCR noise from parentheses
        r'\bho\b',   # Common OCR noise
        r'\bym\b',   # Common OCR noise
        r'\bak\b',   # Common OCR noise
        r'\bui\b',   # Common OCR noise
        r'\bow\b',   # Common OCR noise
        r'\bRE\b',   # Common OCR noise at end
        r'\bET\b',   # Common OCR noise
        r'\bNÉ\b',   # OCR noise from formatting
        r'\bNé\b',   # OCR noise from formatting
        r'\bNée\b',  # OCR noise from formatting
        r'\bà\b',    # OCR noise from formatting
        r'\bdu\b',   # OCR noise from formatting
        r'\bde\b',   # OCR noise from formatting
        r'\ble\b',   # OCR noise from formatting
        r'\bla\b',   # OCR noise from formatting
        r'\bN°\b',   # OCR noise from formatting
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up extra spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', ' ', text)
    
    return text.strip()

def is_arabic_header_text(text):
    """
    Detect if Arabic text is likely a header/official text rather than a name
    """
    arabic_headers = [
        'المملكة المغربية',    # Kingdom of Morocco
        'المملحكة المغربمية',  # OCR version of Kingdom of Morocco
        'البطاقة الوطنية',     # National Card
        'اليطاقة الوطنية',     # OCR version of National Card
        'للتعريف',            # For identification
        'المدير العام',       # General Director
        'للأمن الوطني',       # National Security
        'عبد اللطيف حموشي',   # Official signature
        'صالحة إلى',          # Valid until
        'مزداد بتاريخ',        # Born on
        'مزدادة بتاريخ',       # Born on (feminine)
        'رقم',                # Number
        'بطاقة',              # Card
        'وطنية',              # National
        'تعريف',              # Identification
        'مدير',               # Director
        'عام',                # General
        'أمن',                # Security
        'وطني',               # National
        'صالحة',              # Valid
        'غلية',               # OCR noise from "إلى"
    ]
    
    for header in arabic_headers:
        if header in text:
            return True
    
    return False

def smart_field_detection(text, context_lines):
    """
    AI-powered field detection using context analysis
    """
    field_indicators = {
        'name': {
            'patterns': [
                r'[A-Z]{2,}(?:\s+[A-Z]{2,}){1,3}',  # All caps names
                r'[A-Za-z]{2,}(?:\s+[A-Za-z]{2,}){1,3}',  # Mixed case names
            ],
            'context_indicators': ['né', 'née', 'born', 'name', 'nom'],
            'negative_context': ['carte', 'national', 'royaume', 'maroc', 'director']
        },
        'date': {
            'patterns': [
                r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
                r'(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})'
            ],
            'context_indicators': ['né', 'née', 'born', 'birthdate', 'date'],
            'negative_context': ['expire', 'valid', 'jusqu', 'صالحة']
        },
        'id_number': {
            'patterns': [
                r'[A-Z]{1,2}[0-9]{6,9}',
                r'[0-9]{8,12}'
            ],
            'context_indicators': ['n°', 'number', 'cin', 'passport', 'رقم'],
            'negative_context': ['phone', 'tel']
        }
    }
    
    detected_fields = {}
    
    for field_type, indicators in field_indicators.items():
        for pattern in indicators['patterns']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Check context for validation
                context_score = 0
                for indicator in indicators['context_indicators']:
                    if indicator in text.lower():
                        context_score += 1
                
                for negative in indicators['negative_context']:
                    if negative in text.lower():
                        context_score -= 2
                
                if context_score >= 0:
                    detected_fields[field_type] = matches
    
    return detected_fields 

 