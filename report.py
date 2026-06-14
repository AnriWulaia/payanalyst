from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import io

def generate_pdf(stats: dict, ai_report: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", fontSize=18, fontName="Helvetica-Bold", spaceAfter=12)
    heading_style = ParagraphStyle("heading", fontSize=13, fontName="Helvetica-Bold",
                                   spaceAfter=6, spaceBefore=14, textColor=colors.HexColor("#1a1a2e"))
    body_style = ParagraphStyle("body", fontSize=10, fontName="Helvetica",
                                spaceAfter=6, leading=15)

    story = []

    story.append(Paragraph("PayAnalyst — Payment Report", title_style))
    story.append(Spacer(1, 0.3*cm))

    # Key metrics
    story.append(Paragraph("Key Metrics", heading_style))
    metrics = [
        ["Metric", "Value"],
        ["Total Transactions", str(stats["total_transactions"])],
        ["Successful", str(stats["successful"])],
        ["Failed", str(stats["failed"])],
        ["Success Rate", f"{stats['success_rate']}%"],
        ["Total Volume", f"${stats['total_volume']:,}"],
        ["Average Amount", f"${stats['average_amount']:,}"],
    ]
    story.append(_table(metrics))

    # Top merchants by volume
    story.append(Paragraph("Top Merchants by Volume", heading_style))
    merchant_data = [["Merchant", "Volume"]] + [
        [k, f"${v:,}"] for k, v in stats["top_merchants_by_volume"].items()
    ]
    story.append(_table(merchant_data))

    # Failure reasons breakdown
    if stats.get("failure_reasons"):
        story.append(Paragraph("Failure Reasons Breakdown", heading_style))
        reason_data = [["Reason", "Count"]] + [
            [k, str(v)] for k, v in stats["failure_reasons"].items()
        ]
        story.append(_table(reason_data))

    # Failure reason per merchant
    if stats.get("failure_reason_by_merchant"):
        story.append(Paragraph("Top Failure Reason by Merchant", heading_style))
        merchant_reason_data = [["Merchant", "Top Failure Reason"]] + [
            [k, v] for k, v in stats["failure_reason_by_merchant"].items()
        ]
        story.append(_table(merchant_reason_data))

    # High value transactions
    if stats.get("high_value_transactions"):
        story.append(Paragraph("High Value Transactions (>$10,000)", heading_style))
        hv = stats["high_value_transactions"]
        has_reason = "reason" in hv[0]
        hv_headers = ["Merchant", "Amount", "Status", "Reason"] if has_reason else ["Merchant", "Amount", "Status"]
        hv_rows = []
        for row in hv:
            r = [row.get("merchant", ""), f"${row.get('amount', 0):,}", row.get("status", "")]
            if has_reason:
                r.append(row.get("reason", "") or "—")
            hv_rows.append(r)
        story.append(_table([hv_headers] + hv_rows))

    # AI analysis
    story.append(Paragraph("AI Analysis", heading_style))
    for line in ai_report.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.2*cm))
        elif line.startswith("**") and line.endswith("**"):
            story.append(Paragraph(line.replace("**", ""), heading_style))
        else:
            story.append(Paragraph(line, body_style))

    doc.build(story)
    return buffer.getvalue()


def _table(data):
    t = Table(data, colWidths=[8*cm, 8*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    return t