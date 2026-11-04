import io
import csv
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.settings import HospitalSetting

def export_to_csv(headers, rows):
    """Generate in-memory CSV file bytes"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode('utf-8')

def export_to_excel(sheet_name, headers, rows):
    """Generate in-memory Excel (.xlsx) file bytes using openpyxl"""
    df = pd.DataFrame(rows, columns=headers)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    output.seek(0)
    return output.getvalue()

def export_to_pdf(title, headers, rows, orientation='portrait'):
    """Generate a publication-quality PDF report using ReportLab"""
    buffer = io.BytesIO()
    page_size = landscape(letter) if orientation == 'landscape' else letter
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )
    header_cell_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )

    elements = []
    
    # Hospital header
    hospital_name = "Apex Health & Analytics Center"
    try:
        settings = HospitalSetting.get_settings()
        if settings and settings.hospital_name:
            hospital_name = settings.hospital_name
    except Exception:
        pass

    elements.append(Paragraph(hospital_name, title_style))
    elements.append(Paragraph(f"{title} | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
    elements.append(Spacer(1, 8))

    # Format table data
    table_data = []
    # Headers
    table_data.append([Paragraph(str(h), header_cell_style) for h in headers])

    # Truncate rows to avoid huge 5000-page PDFs if report is too large (limit to first 150 rows)
    display_rows = rows[:150]
    for row in display_rows:
        table_data.append([Paragraph(str(c if c is not None else ''), table_cell_style) for c in row])

    # Table styling
    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))

    elements.append(t)
    
    if len(rows) > 150:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Note: Displaying first 150 of {len(rows)} total records. For the complete dataset, please download the CSV or Excel version.", subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
