"""
exports/pdf_exporter.py
Generates a professionally formatted PDF report using ReportLab.
"""

import os
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)

from config.settings import EXPORT_DIR
from utils.logger import logger


# ── Brand colours ─────────────────────────────────────────────────────────────
BRAND_DARK = colors.HexColor("#1a2b4a")
BRAND_MID = colors.HexColor("#2563eb")
BRAND_LIGHT = colors.HexColor("#eff6ff")
ACCENT = colors.HexColor("#f59e0b")
TEXT_DARK = colors.HexColor("#111827")
TEXT_MUTED = colors.HexColor("#6b7280")


def _styles():
    base = getSampleStyleSheet()
    custom = {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Title"],
            fontSize=28, textColor=colors.white, alignment=TA_CENTER,
            spaceAfter=8, fontName="Helvetica-Bold",
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base["Normal"],
            fontSize=14, textColor=colors.HexColor("#bfdbfe"), alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "section_header": ParagraphStyle(
            "section_header", parent=base["Heading1"],
            fontSize=14, textColor=BRAND_DARK, fontName="Helvetica-Bold",
            spaceBefore=16, spaceAfter=6, borderPadding=(0, 0, 4, 0),
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=10, textColor=TEXT_DARK, leading=16, alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"],
            fontSize=10, textColor=TEXT_DARK, leading=15,
            leftIndent=12, bulletIndent=0, spaceAfter=4,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["Normal"],
            fontSize=8, textColor=TEXT_MUTED, spaceAfter=4,
        ),
        "confidence_high": ParagraphStyle(
            "confidence_high", parent=base["Normal"],
            fontSize=9, textColor=colors.HexColor("#065f46"),
            backColor=colors.HexColor("#d1fae5"), borderPadding=4,
        ),
        "confidence_low": ParagraphStyle(
            "confidence_low", parent=base["Normal"],
            fontSize=9, textColor=colors.HexColor("#7f1d1d"),
            backColor=colors.HexColor("#fee2e2"), borderPadding=4,
        ),
    }
    return {**{k: base[k] for k in base.byName}, **custom}


def _confidence_badge(level: str, styles) -> Paragraph:
    colours_map = {
        "high": ("confidence_high", "✅ High Confidence"),
        "medium": ("confidence_high", "⚠️ Medium Confidence"),
        "low": ("confidence_low", "⚠️ Low Confidence — Limited Data"),
    }
    style_key, label = colours_map.get(level, ("confidence_low", f"Confidence: {level}"))
    return Paragraph(label, styles[style_key])


def _section_divider():
    return HRFlowable(width="100%", thickness=1, color=BRAND_MID, spaceAfter=8, spaceBefore=4)


def _render_value(value, styles, indent=0) -> list:
    """Recursively render report values into ReportLab flowables."""
    elements = []
    indent_str = "&nbsp;" * (indent * 4)

    if isinstance(value, str):
        elements.append(Paragraph(f"{indent_str}{value}", styles["body"]))

    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                for k, v in item.items():
                    elements.append(Paragraph(
                        f"{indent_str}<b>{k}:</b>", styles["bullet"]
                    ))
                    elements.extend(_render_value(v, styles, indent + 1))
            elif isinstance(item, str):
                elements.append(Paragraph(f"{indent_str}• {item}", styles["bullet"]))

    elif isinstance(value, dict):
        for k, v in value.items():
            elements.append(Paragraph(
                f"{indent_str}<b>{k.replace('_', ' ').title()}:</b>", styles["bullet"]
            ))
            elements.extend(_render_value(v, styles, indent + 1))

    return elements


def export_pdf(report: dict, company: str, country: str) -> str:
    """Generate a PDF report and return the file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() else "_" for c in company)
    filename = f"sales_report_{safe_name}_{timestamp}.pdf"
    filepath = EXPORT_DIR / filename

    doc = SimpleDocTemplate(
        str(filepath), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
    )

    styles = _styles()
    story = []

    # ── Cover table ───────────────────────────────────────────────────────────
    cover_data = [[
        Paragraph(f"Sales Intelligence Report", styles["cover_title"]),
    ], [
        Paragraph(f"{company} | {country}", styles["cover_subtitle"]),
    ], [
        Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M UTC')}", styles["cover_subtitle"]),
    ]]
    cover_table = Table(cover_data, colWidths=[doc.width])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [8, 8, 8, 8]),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 0.4 * cm))

    # Confidence badge
    story.append(_confidence_badge(report.get("confidence", "unknown"), styles))
    story.append(Spacer(1, 0.3 * cm))

    # ── Report sections ───────────────────────────────────────────────────────
    sections = report.get("sections", {})
    section_order = [
        "Company Overview",
        "Industry Information",
        "Recent News & Events",
        "Potential Business Opportunities",
        "Pain Points Identified",
        "Suggested Sales Approach",
        "Key Contacts Guidance",
        "Competitive Context",
        "Data Gaps",
    ]

    for section_name in section_order:
        value = sections.get(section_name)
        if value is None:
            continue

        story.append(_section_divider())
        story.append(Paragraph(section_name, styles["section_header"]))

        story.extend(_render_value(value, styles))
        story.append(Spacer(1, 0.3 * cm))

    # ── Sources ───────────────────────────────────────────────────────────────
    sources = report.get("sources", [])
    if sources:
        story.append(PageBreak())
        story.append(Paragraph("Sources & References", styles["section_header"]))
        story.append(_section_divider())
        for i, src in enumerate(sources, 1):
            story.append(Paragraph(f"{i}. {src}", styles["caption"]))

    # ── Warnings / caveats ────────────────────────────────────────────────────
    warnings = report.get("warnings", [])
    if warnings:
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("⚠️ Caveats & Limitations", styles["section_header"]))
        for w in warnings:
            story.append(Paragraph(f"• {w}", styles["bullet"]))

    doc.build(story)
    logger.info(f"PDF exported: {filepath}")
    return str(filepath)
