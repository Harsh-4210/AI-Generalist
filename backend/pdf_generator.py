from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from PIL import Image as PILImage
import datetime
import io

# ── Color palette (UrbanRoof brand) ─────────────────────────────────────────
YELLOW   = colors.HexColor("#F5A623")
BLACK    = colors.HexColor("#1A1A1A")
DARK_BG  = colors.HexColor("#2D2D2D")
WHITE    = colors.white
LIGHT_GRAY = colors.HexColor("#F7F7F7")
MID_GRAY = colors.HexColor("#EEEEEE")
GREEN_LINE = colors.HexColor("#4CAF50")
RED_HIGH   = colors.HexColor("#D32F2F")
ORANGE_MED = colors.HexColor("#F57C00")
GREEN_LOW  = colors.HexColor("#388E3C")
SECTION_BG = colors.HexColor("#F0F0F0")

def resize_image_bytes(img_bytes: bytes, max_width: int = 400, max_height: int = 300) -> bytes:
    """Resize an image to fit within max dimensions, preserving aspect ratio."""
    try:
        img = PILImage.open(io.BytesIO(img_bytes))
        img.thumbnail((max_width, max_height), PILImage.LANCZOS)
        buf = io.BytesIO()
        fmt = img.format if img.format else "JPEG"
        if fmt not in ["JPEG", "PNG", "GIF"]:
            fmt = "JPEG"
        if img.mode == "RGBA" and fmt == "JPEG":
            img = img.convert("RGB")
        img.save(buf, format=fmt)
        return buf.getvalue()
    except Exception:
        return img_bytes

def make_styles():
    styles = getSampleStyleSheet()
    custom = {
        "CoverTitle": ParagraphStyle("CoverTitle", fontSize=28, textColor=WHITE,
                                     fontName="Helvetica-Bold", spaceAfter=8,
                                     alignment=TA_CENTER),
        "CoverSub": ParagraphStyle("CoverSub", fontSize=13, textColor=YELLOW,
                                   fontName="Helvetica-Bold", spaceAfter=4,
                                   alignment=TA_CENTER),
        "CoverInfo": ParagraphStyle("CoverInfo", fontSize=10, textColor=WHITE,
                                    fontName="Helvetica", spaceAfter=4,
                                    alignment=TA_CENTER),
        "SectionTitle": ParagraphStyle("SectionTitle", fontSize=14, textColor=BLACK,
                                       fontName="Helvetica-Bold", spaceBefore=12,
                                       spaceAfter=6, borderPad=4),
        "AreaTitle": ParagraphStyle("AreaTitle", fontSize=12, textColor=BLACK,
                                    fontName="Helvetica-Bold", spaceBefore=8,
                                    spaceAfter=4),
        "BodyText": ParagraphStyle("BodyText", fontSize=10, textColor=BLACK,
                                   fontName="Helvetica", spaceAfter=4,
                                   leading=15, alignment=TA_JUSTIFY),
        "BulletText": ParagraphStyle("BulletText", fontSize=10, textColor=BLACK,
                                     fontName="Helvetica", spaceAfter=3,
                                     leftIndent=16, leading=14),
        "ImageCaption": ParagraphStyle("ImageCaption", fontSize=8, textColor=colors.grey,
                                       fontName="Helvetica-Oblique", spaceAfter=6,
                                       alignment=TA_CENTER),
        "MissingText": ParagraphStyle("MissingText", fontSize=10, textColor=colors.HexColor("#666666"),
                                      fontName="Helvetica-Oblique", spaceAfter=3,
                                      leftIndent=16),
    }
    return custom

def section_header(title: str, number: str, styles: dict):
    """Create a styled section header block."""
    header_data = [[Paragraph(f"{number}. {title}", styles["SectionTitle"])]]
    t = Table(header_data, colWidths=[160*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SECTION_BG),
        ("LINEBELOW", (0, 0), (-1, -1), 2, YELLOW),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [SECTION_BG]),
    ]))
    return t

def build_image_element(img_dict: dict, caption: str, styles: dict):
    """Build a ReportLab Image + caption from image dict."""
    try:
        resized = resize_image_bytes(img_dict["bytes"])
        img_buf = io.BytesIO(resized)
        rl_img = RLImage(img_buf, width=140*mm, height=90*mm, kind='proportional')
        cap = Paragraph(caption, styles["ImageCaption"])
        return [rl_img, cap, Spacer(1, 4*mm)]
    except Exception:
        return [Paragraph("⚠ Image could not be rendered", styles["MissingText"]),
                Spacer(1, 4*mm)]

def generate_ddr_pdf(ddr_data: dict, inspection_images: list, thermal_images: list,
                     report_meta: dict = None) -> bytes:
    """
    Generate a professional DDR PDF.
    Returns PDF as bytes.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title="Detailed Diagnostic Report",
        author="UrbanRoof Private Limited"
    )
    styles = make_styles()
    story = []
    today = datetime.date.today().strftime("%d %B %Y")
    meta = report_meta or {}

    # ── COVER PAGE ────────────────────────────────────────────────────────────
    cover_data = [[
        Paragraph("Detailed Diagnostic Report", styles["CoverTitle"]),
        Spacer(1, 6*mm),
        Paragraph("UrbanRoof Private Limited", styles["CoverSub"]),
        Spacer(1, 10*mm),
        Paragraph(f"Property: {meta.get('property', 'As Per Inspection')}", styles["CoverInfo"]),
        Paragraph(f"Report Date: {today}", styles["CoverInfo"]),
        Paragraph(f"Inspected By: {meta.get('inspector', 'UrbanRoof Technical Team')}", styles["CoverInfo"]),
        Spacer(1, 6*mm),
        Paragraph("www.urbanroof.in  |  info@urbanroof.in  |  +91-8925-805-805", styles["CoverInfo"]),
    ]]
    cover_table = Table([[cover_data[0]]], colWidths=[160*mm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
        ("LINEBELOW", (0, 0), (-1, -1), 4, YELLOW),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 8*mm))

    # Disclaimer box
    disc_text = (
        "<b>Disclaimer:</b> This report is based on visual and non-destructive inspection conducted on the "
        "specified date. It is not exhaustive and may not reveal all deficiencies. Refer to Section 5 "
        "of the full report for limitations."
    )
    disc_para = Paragraph(disc_text, ParagraphStyle("disc", fontSize=8, textColor=colors.HexColor("#555555"),
                                                     fontName="Helvetica", spaceAfter=4, leading=12))
    disc_table = Table([[disc_para]], colWidths=[160*mm])
    disc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF8E1")),
        ("BOX", (0, 0), (-1, -1), 0.5, YELLOW),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(disc_table)
    story.append(Spacer(1, 8*mm))

    # ── SECTION 1: Property Issue Summary ────────────────────────────────────
    story.append(section_header("PROPERTY ISSUE SUMMARY", "1", styles))
    story.append(Spacer(1, 3*mm))
    summary = ddr_data.get("property_issue_summary", "Not Available")
    story.append(Paragraph(summary, styles["BodyText"]))
    story.append(Spacer(1, 6*mm))

    # ── SECTION 2: Area-wise Observations ────────────────────────────────────
    story.append(section_header("AREA-WISE OBSERVATIONS", "2", styles))
    story.append(Spacer(1, 3*mm))

    # Build lookup maps for images by page
    insp_by_page = {}
    for img in inspection_images:
        p = img["page"]
        insp_by_page.setdefault(p, []).append(img)

    therm_by_page = {}
    for img in thermal_images:
        p = img["page"]
        therm_by_page.setdefault(p, []).append(img)

    # Track used images to prevent duplicates across areas
    used_image_keys = set()

    areas = ddr_data.get("area_wise_observations", [])
    for area_obj in areas:
        area_name = area_obj.get("area", "Unknown Area")
        observations = area_obj.get("observations", [])
        image_refs = area_obj.get("image_refs", [])

        # Area subheading
        area_header_data = [[Paragraph(f"▶  {area_name}", styles["AreaTitle"])]]
        at = Table(area_header_data, colWidths=[160*mm])
        at.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#CCCCCC")),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(at)

        # Observations
        for obs in observations:
            story.append(Paragraph(f"• {obs}", styles["BulletText"]))

        # Place relevant images
        images_placed = 0
        for ref in image_refs:
            source = str(ref.get("source", "")).lower()
            
            try:
                page = int(ref.get("page", 0))
            except (ValueError, TypeError):
                page = 0
                
            desc = ref.get("description", f"Image from {source} report, page {page}")

            if "thermal" in source and len(therm_by_page) > 0:
                # Find closest page, skipping already-used images
                sorted_pages = sorted(therm_by_page.keys(), key=lambda k: abs(k - page))
                for closest in sorted_pages:
                    img_key = ("thermal", closest, 0)
                    if img_key not in used_image_keys:
                        for img in therm_by_page[closest][:1]:
                            elems = build_image_element(img, f"Thermal Image — {desc}", styles)
                            for e in elems: story.append(e)
                            images_placed += 1
                            used_image_keys.add(img_key)
                        break
                        
            elif "inspection" in source and len(insp_by_page) > 0:
                sorted_pages = sorted(insp_by_page.keys(), key=lambda k: abs(k - page))
                for closest in sorted_pages:
                    img_key = ("inspection", closest, 0)
                    if img_key not in used_image_keys:
                        for img in insp_by_page[closest][:1]:
                            elems = build_image_element(img, f"Site Photo — {desc}", styles)
                            for e in elems: story.append(e)
                            images_placed += 1
                            used_image_keys.add(img_key)
                        break

        if images_placed == 0 and image_refs:
            story.append(Paragraph("⚠ Image Not Available", styles["MissingText"]))

        story.append(Spacer(1, 4*mm))

    # ── SECTION 3: Probable Root Cause ───────────────────────────────────────
    story.append(section_header("PROBABLE ROOT CAUSE", "3", styles))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(ddr_data.get("probable_root_cause", "Not Available"), styles["BodyText"]))
    story.append(Spacer(1, 6*mm))

    # ── SECTION 4: Severity Assessment ───────────────────────────────────────
    story.append(section_header("SEVERITY ASSESSMENT", "4", styles))
    story.append(Spacer(1, 3*mm))

    sev = ddr_data.get("severity_assessment", {})
    level = sev.get("level", "Medium")
    reasoning = sev.get("reasoning", "Not Available")

    level_color = {"High": RED_HIGH, "Medium": ORANGE_MED, "Low": GREEN_LOW}.get(level, ORANGE_MED)
    level_icon  = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}.get(level, "🟠")

    sev_badge_data = [[
        Paragraph(f"<b>{level_icon}  Severity Level: {level.upper()}</b>",
                  ParagraphStyle("sev_badge", fontSize=14, textColor=WHITE,
                                 fontName="Helvetica-Bold", alignment=TA_CENTER))
    ]]
    sev_badge = Table(sev_badge_data, colWidths=[160*mm])
    sev_badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), level_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [level_color]),
    ]))
    story.append(sev_badge)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"<b>Reasoning:</b> {reasoning}", styles["BodyText"]))
    story.append(Spacer(1, 6*mm))

    # ── SECTION 5: Recommended Actions ───────────────────────────────────────
    story.append(section_header("RECOMMENDED ACTIONS", "5", styles))
    story.append(Spacer(1, 3*mm))
    actions = ddr_data.get("recommended_actions", ["Not Available"])
    for i, action in enumerate(actions, 1):
        story.append(Paragraph(f"{i}. {action}", styles["BulletText"]))
        story.append(Spacer(1, 2*mm))
    story.append(Spacer(1, 4*mm))

    # ── SECTION 6: Additional Notes ──────────────────────────────────────────
    story.append(section_header("ADDITIONAL NOTES", "6", styles))
    story.append(Spacer(1, 3*mm))
    notes = ddr_data.get("additional_notes", "Not Available")
    story.append(Paragraph(notes, styles["BodyText"]))
    story.append(Spacer(1, 6*mm))

    # ── SECTION 7: Missing / Unclear Information ──────────────────────────────
    story.append(section_header("MISSING OR UNCLEAR INFORMATION", "7", styles))
    story.append(Spacer(1, 3*mm))
    missing = ddr_data.get("missing_or_unclear", [])
    if missing:
        for item in missing:
            story.append(Paragraph(f"• {item}", styles["MissingText"]))
    else:
        story.append(Paragraph("• All key information was available in the provided documents.",
                                styles["BulletText"]))
    story.append(Spacer(1, 8*mm))

    # ── FOOTER NOTE ───────────────────────────────────────────────────────────
    footer_text = (
        "This report is the intellectual property of UrbanRoof Private Limited. "
        "It is prepared exclusively for the client named herein and may not be shared without written consent. "
        "UrbanRoof | Office No. 03, Akshay House, Anand Nagar, Sinhgad Road, Pune – 411051"
    )
    story.append(HRFlowable(width="100%", thickness=1, color=YELLOW))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(footer_text, ParagraphStyle(
        "footer", fontSize=7, textColor=colors.HexColor("#888888"),
        fontName="Helvetica", alignment=TA_CENTER, leading=11
    )))

    doc.build(story)
    return buf.getvalue()
