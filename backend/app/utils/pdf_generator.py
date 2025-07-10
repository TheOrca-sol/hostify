from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
import tempfile
import os

def generate_police_form(guest_data):
    """
    Generate a French police form (Fiche de Police) PDF
    """
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            temp_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        # Build PDF content
        story = []
        
        # Header
        story.append(Paragraph("ROYAUME DU MAROC", title_style))
        story.append(Paragraph("FICHE DE POLICE", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Current date
        current_date = datetime.now().strftime("%d/%m/%Y")
        story.append(Paragraph(f"Date: {current_date}", normal_style))
        story.append(Spacer(1, 20))
        
        # Guest information table
        data = [
            ['INFORMATIONS DE L\'INVITÉ', ''],
            ['', ''],
            ['Nom complet:', guest_data.get('full_name', '')],
            ['Numéro CIN/Passeport:', guest_data.get('cin_or_passport', '')],
            ['Date de naissance:', format_date(guest_data.get('birthdate', ''))],
            ['Nationalité:', guest_data.get('nationality', '')],
            ['Type de document:', guest_data.get('document_type', '')],
            ['Adresse:', guest_data.get('address', '')],
            ['', ''],
            ['Date d\'arrivée:', current_date],
            ['Statut:', 'Invité'],
        ]
        
        # Create table
        table = Table(data, colWidths=[3*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Footer information
        story.append(Paragraph("DÉCLARATION", subtitle_style))
        story.append(Spacer(1, 10))
        
        declaration_text = """
        Je soussigné(e), propriétaire/gérant de l'établissement d'hébergement, déclare sur l'honneur 
        que les informations ci-dessus sont exactes et complètes. L'invité mentionné ci-dessus séjourne 
        dans mon établissement aux dates indiquées.
        """
        
        story.append(Paragraph(declaration_text, normal_style))
        story.append(Spacer(1, 30))
        
        # Signature section
        signature_data = [
            ['Signature de l\'hôte:', 'Signature de l\'invité:'],
            ['', ''],
            ['', ''],
            ['Date:', 'Date:'],
            [current_date, current_date],
        ]
        
        signature_table = Table(signature_data, colWidths=[3.5*inch, 3.5*inch])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 1), (-1, 2), 30),
        ]))
        
        story.append(signature_table)
        story.append(Spacer(1, 20))
        
        # Footer
        footer_text = """
        Cette fiche doit être conservée par l'établissement d'hébergement et présentée 
        aux autorités compétentes sur demande.
        """
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey,
            fontName='Helvetica-Oblique'
        )
        
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        
        return temp_path
    
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")

def format_date(date_str):
    """
    Format date string for display
    """
    try:
        if not date_str:
            return ''
        
        # Parse ISO format date
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime("%d/%m/%Y")
    
    except (ValueError, AttributeError):
        return date_str 