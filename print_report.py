"""Combined print-ready Letter checklist: every uploaded stop/city/LPN in one table."""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def create_print_pdf(rows):
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=letter, leftMargin=28, rightMargin=28,
                            topMargin=32, bottomMargin=37,
                            title='Packing Slip Inspection Checklist')
    styles = getSampleStyleSheet()
    title = ParagraphStyle('TitleCustom', parent=styles['Heading1'], fontName='Helvetica-Bold',
                           fontSize=15, leading=19, spaceAfter=11,
                           textColor=colors.HexColor('#17324f'))
    small = ParagraphStyle('InfoCustom', parent=styles['Normal'], fontSize=9, leading=13)
    story = [Paragraph('PACKING SLIP - CONTAINER CHECKLIST', title)]
    info = Table([
        ['Date', '_________________', 'Transporter', '____________________________'],
        ['Trailer ID', '_________________', 'Name', '____________________________'],
    ], colWidths=[68, 175, 79, 234], rowHeights=[29, 29])
    info.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), .7, colors.HexColor('#b8c7d1')),
        ('INNERGRID', (0,0), (-1,-1), .5, colors.HexColor('#d3dce3')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.extend([info, Spacer(1, 14),
                  Paragraph('Mark the appropriate container type for each LPN.', small), Spacer(1, 7)])
    headings = ['STOP ID', 'CITY', 'LPN', 'PALLET', 'BOX', 'PIPE', 'BUNDLE']
    data = [headings]
    # Keep a row for every extracted stop/city/LPN; no cross-document grouping.
    for row in rows:
        data.append([str(row['Stop ID']), str(row['City']), str(row['LPN']), '', '', '', ''])
    # Widths add to 556 points, matching available printable area.
    widths = [111, 91, 91, 70, 58, 61, 74]
    table = Table(data, colWidths=widths, rowHeights=[29] + [34] * len(rows), repeatRows=1,
                  hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#17324f')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('ALIGN', (3,1), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), .55, colors.HexColor('#b8c7d1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f8fa')]),
    ]))
    story.extend([table, Spacer(1, 11), Paragraph(f'<b>Total LPN rows:</b> {len(rows)}', small)])

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#d6dfe6'))
        canvas.line(28, 28, letter[0]-28, 28)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(28, 17, 'Packing Slip Inspection Checklist')
        canvas.drawRightString(letter[0]-28, 17, f'Page {document.page}')
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return out.getvalue()
