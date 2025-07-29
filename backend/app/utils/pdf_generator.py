"""
PDF generation utilities for contracts and documents
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
from datetime import datetime
import uuid
import base64
import io
from PIL import Image as PILImage
from flask import current_app

def generate_contract_pdf(content, guest, contract):
    """
    Generate a PDF contract document
    
    Args:
        content (str): Populated contract content
        guest: Guest object
        contract: Contract object
    
    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Create contracts directory if it doesn't exist
        contracts_dir = os.path.join(os.getcwd(), 'contracts')
        os.makedirs(contracts_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"contract_{contract.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(contracts_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.darkblue
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_LEFT
        )
        
        # Add title
        story.append(Paragraph("RENTAL CONTRACT", title_style))
        story.append(Spacer(1, 20))
        
        # Add contract details table
        contract_data = [
            ['Guest Name:', guest.full_name or 'N/A'],
            ['Property:', guest.reservation.property.name if guest.reservation and guest.reservation.property else 'N/A'],
            ['Check-in Date:', guest.reservation.check_in.strftime('%B %d, %Y') if guest.reservation and guest.reservation.check_in else 'N/A'],
            ['Check-out Date:', guest.reservation.check_out.strftime('%B %d, %Y') if guest.reservation and guest.reservation.check_out else 'N/A'],
            ['Contract Date:', datetime.now().strftime('%B %d, %Y')],
            ['Contract ID:', str(contract.id)]
        ]
        
        contract_table = Table(contract_data, colWidths=[2*inch, 4*inch])
        contract_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(contract_table)
        story.append(Spacer(1, 30))
        
        # Add contract content
        story.append(Paragraph("CONTRACT TERMS", header_style))
        story.append(Spacer(1, 15))
        
        # Split content into paragraphs and add them
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Convert line breaks to HTML breaks for ReportLab
                para_html = para.replace('\n', '<br/>')
                story.append(Paragraph(para_html, normal_style))
                story.append(Spacer(1, 10))
        
        # Add signature section
        story.append(Spacer(1, 30))
        story.append(Paragraph("SIGNATURES", header_style))
        story.append(Spacer(1, 20))
        
        # Get host signature from property owner
        host_signature_cell = '_________________'
        try:
            if contract.reservation and contract.reservation.property and contract.reservation.property.owner:
                host = contract.reservation.property.owner
                if host.signature:
                    # Create temporary host signature image
                    host_signature_data = host.signature
                    if host_signature_data.startswith('data:image/'):
                        host_signature_data = host_signature_data.split(',')[1]
                    
                    host_signature_bytes = base64.b64decode(host_signature_data)
                    host_signature_image = PILImage.open(io.BytesIO(host_signature_bytes))
                    
                    # Save temporary host signature file
                    temp_host_signature_path = os.path.join(contracts_dir, f"temp_host_signature_{contract.id}_{uuid.uuid4()}.png")
                    host_signature_image.save(temp_host_signature_path)
                    
                    # Create ReportLab image for host signature
                    host_sig_img = Image(temp_host_signature_path, width=2*inch, height=1*inch)
                    host_signature_cell = host_sig_img
                    
                    # Clean up temp file immediately after use
                    try:
                        os.remove(temp_host_signature_path)
                    except:
                        pass
        except Exception as sig_error:
            current_app.logger.error(f"Error processing host signature: {sig_error}")
            host_signature_cell = '_________________'
        
        # Signature table
        signature_data = [
            ['Host Signature:', host_signature_cell],
            ['Guest Signature:', '_________________'],
            ['Date:', datetime.now().strftime('%B %d, %Y')]
        ]
        
        signature_table = Table(signature_data, colWidths=[2*inch, 4*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ('LINEBELOW', (1, 0), (1, 1), 1, colors.black)
        ]))
        
        story.append(signature_table)
        
        # Build PDF
        doc.build(story)
        
        return filepath
        
    except Exception as e:
        current_app.logger.error(f"Error generating contract PDF: {e}", exc_info=True)
        raise

def generate_signed_contract_pdf(content, guest, contract, signature_data):
    """
    Generate a signed contract PDF with digital signature
    
    Args:
        content (str): Populated contract content
        guest: Guest object
        contract: Contract object
        signature_data (dict): Signature information
    
    Returns:
        str: Path to the generated signed PDF file
    """
    contracts_dir = os.path.join(os.getcwd(), 'contracts')
    os.makedirs(contracts_dir, exist_ok=True)
    
    filename = f"signed_contract_{contract.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(contracts_dir, filename)
    
    temp_signature_path = None
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkgreen
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.darkgreen
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_LEFT
        )
        
        # Add title with "SIGNED" indicator
        story.append(Paragraph("SIGNED RENTAL CONTRACT", title_style))
        story.append(Spacer(1, 20))
        
        # Add contract details table
        contract_data = [
            ['Guest Name:', guest.full_name or 'N/A'],
            ['Property:', guest.reservation.property.name if guest.reservation and guest.reservation.property else 'N/A'],
            ['Check-in Date:', guest.reservation.check_in.strftime('%B %d, %Y') if guest.reservation and guest.reservation.check_in else 'N/A'],
            ['Check-out Date:', guest.reservation.check_out.strftime('%B %d, %Y') if guest.reservation and guest.reservation.check_out else 'N/A'],
            ['Signed Date:', contract.signed_at.strftime('%B %d, %Y at %H:%M') if contract.signed_at else 'N/A'],
            ['Contract ID:', str(contract.id)]
        ]
        
        contract_table = Table(contract_data, colWidths=[2*inch, 4*inch])
        contract_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(contract_table)
        story.append(Spacer(1, 30))
        
        # Add contract content
        story.append(Paragraph("CONTRACT TERMS", header_style))
        story.append(Spacer(1, 15))
        
        # Split content into paragraphs and add them
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Convert line breaks to HTML breaks for ReportLab
                para_html = para.replace('\n', '<br/>')
                story.append(Paragraph(para_html, normal_style))
                story.append(Spacer(1, 10))
        
        # Add signature section with digital signature info
        story.append(Spacer(1, 30))
        story.append(Paragraph("DIGITAL SIGNATURES", header_style))
        story.append(Spacer(1, 20))
        
        # Add host signature first
        try:
            if contract.reservation and contract.reservation.property and contract.reservation.property.owner:
                host = contract.reservation.property.owner
                if host.signature:
                    story.append(Paragraph("Host Signature:", normal_style))
                    story.append(Spacer(1, 10))
                    
                    # Process host signature
                    host_signature_data = host.signature
                    if host_signature_data.startswith('data:image/'):
                        host_signature_data = host_signature_data.split(',')[1]
                    
                    host_signature_bytes = base64.b64decode(host_signature_data)
                    host_signature_image = PILImage.open(io.BytesIO(host_signature_bytes))
                    
                    # Save temporary host signature file
                    temp_host_signature_path = os.path.join(contracts_dir, f"temp_host_signature_{contract.id}_{uuid.uuid4()}.png")
                    host_signature_image.save(temp_host_signature_path)
                    
                    # Add host signature image to PDF
                    host_img = Image(temp_host_signature_path, width=3*inch, height=1.5*inch)
                    story.append(host_img)
                    story.append(Spacer(1, 20))
                    
                    # Clean up temp host signature file
                    try:
                        os.remove(temp_host_signature_path)
                    except:
                        pass
                else:
                    story.append(Paragraph("Host Signature: [No signature on file]", normal_style))
                    story.append(Spacer(1, 10))
        except Exception as host_sig_error:
            current_app.logger.error(f"Error processing host signature: {host_sig_error}")
            story.append(Paragraph("Host Signature: [Error loading signature]", normal_style))
            story.append(Spacer(1, 10))
        
        # Add actual guest signature image if available
        if signature_data and signature_data.get('signature'):
            try:
                # Extract base64 data from data URL
                signature_b64 = signature_data['signature']
                if signature_b64.startswith('data:image/'):
                    # Remove data URL prefix
                    signature_b64 = signature_b64.split(',')[1]
                
                # Decode base64 to image
                signature_bytes = base64.b64decode(signature_b64)
                signature_image = PILImage.open(io.BytesIO(signature_bytes))
                
                # Save temporary image file with unique name to avoid conflicts
                temp_signature_path = os.path.join(contracts_dir, f"temp_signature_{contract.id}_{uuid.uuid4()}.png")
                signature_image.save(temp_signature_path)
                
                # Add signature image to PDF
                story.append(Paragraph("Guest Signature:", normal_style))
                story.append(Spacer(1, 10))
                
                # Create ReportLab image with appropriate size
                img = Image(temp_signature_path, width=3*inch, height=1.5*inch)
                story.append(img)
                story.append(Spacer(1, 20))
                
            except Exception as sig_error:
                current_app.logger.error(f"Error processing signature image: {sig_error}", exc_info=True)
                # Fall back to text representation
                story.append(Paragraph("Guest Signature: [Digital signature applied]", normal_style))
                story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("Guest Signature: [Digital signature applied]", normal_style))
            story.append(Spacer(1, 10))
        
        # Signature table with digital signature details
        signature_data_table = [
            ['Guest Name:', guest.full_name or 'N/A'],
            ['Signed Date:', contract.signed_at.strftime('%B %d, %Y at %H:%M') if contract.signed_at else 'N/A'],
            ['Signature IP:', contract.signature_ip or 'N/A'],
            ['Contract Status:', 'SIGNED'],
            ['Digital Signature ID:', str(uuid.uuid4())]
        ]
        
        signature_table = Table(signature_data_table, colWidths=[2*inch, 4*inch])
        signature_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(signature_table)
        
        # Build PDF
        doc.build(story)
        
        return filepath
        
    except Exception as e:
        current_app.logger.error(f"Error generating signed contract PDF: {e}", exc_info=True)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as cleanup_error:
                current_app.logger.error(f"Error cleaning up failed PDF file: {cleanup_error}", exc_info=True)
        raise
        
    finally:
        # Always clean up temporary signature file
        if temp_signature_path and os.path.exists(temp_signature_path):
            try:
                os.remove(temp_signature_path)
            except Exception as cleanup_error:
                current_app.logger.error(f"Error cleaning up temporary signature file: {cleanup_error}", exc_info=True)