"""
PDF generation utilities for contracts
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from jinja2 import Template
import uuid

# Register fonts (assuming we have these in a fonts directory)
FONTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts')
os.makedirs(FONTS_DIR, exist_ok=True)

# TODO: Add proper font files
# pdfmetrics.registerFont(TTFont('Arabic', os.path.join(FONTS_DIR, 'arabic.ttf')))
# pdfmetrics.registerFont(TTFont('French', os.path.join(FONTS_DIR, 'french.ttf')))

def generate_contract_pdf(template, guest, reservation, property):
    """Generate a PDF contract from template"""
    try:
        # Create contracts directory if it doesn't exist
        contracts_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'contracts')
        os.makedirs(contracts_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"contract_{uuid.uuid4()}.pdf"
        pdf_path = os.path.join(contracts_dir, filename)
        
        # Prepare template data
        template_data = {
            'guest': guest.to_dict(),
            'reservation': reservation.to_dict(),
            'property': property.to_dict(),
            'host': property.owner.to_dict(),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Render template content
        jinja_template = Template(template.template_content)
        content = jinja_template.render(**template_data)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Add custom style for RTL text if needed
        if template.language == 'ar':
            styles.add(ParagraphStyle(
                name='Arabic',
                fontName='Arabic',
                fontSize=12,
                leading=16,
                alignment=2  # RTL alignment
            ))
        
        # Convert content to PDF elements
        elements = []
        
        # Add header
        elements.append(Paragraph(
            f"RENTAL CONTRACT - {property.name}",
            styles['Heading1']
        ))
        elements.append(Spacer(1, 12))
        
        # Add content paragraphs
        for line in content.split('\n'):
            if line.strip():
                style = styles['Arabic'] if template.language == 'ar' else styles['Normal']
                elements.append(Paragraph(line, style))
                elements.append(Spacer(1, 12))
        
        # Add signature box if not signed
        if not hasattr(template_data, 'signature'):
            elements.append(Spacer(1, 36))
            elements.append(Paragraph("Guest Signature:", styles['Heading2']))
            elements.append(Spacer(1, 72))  # Space for signature
            elements.append(Paragraph(f"Date: {datetime.utcnow().date()}", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        return pdf_path
    
    except Exception as e:
        print(f"Failed to generate contract PDF: {str(e)}")
        return None

def generate_signed_contract_pdf(contract):
    """Generate a signed version of the contract PDF"""
    try:
        # Get original PDF path
        original_pdf = contract.generated_pdf_path
        if not original_pdf or not os.path.exists(original_pdf):
            return None
        
        # Create signed contracts directory
        signed_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'contracts', 'signed')
        os.makedirs(signed_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"signed_contract_{uuid.uuid4()}.pdf"
        signed_pdf_path = os.path.join(signed_dir, filename)
        
        # TODO: Add signature to PDF
        # For now, just copy the original
        import shutil
        shutil.copy2(original_pdf, signed_pdf_path)
        
        return signed_pdf_path
    
    except Exception as e:
        print(f"Failed to generate signed contract PDF: {str(e)}")
        return None 