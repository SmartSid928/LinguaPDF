
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)


BASE_DIR = Path(__file__).resolve().parent.parent
FONT_DIR = BASE_DIR / "assets" / "fonts"


# Language code -> Font filename
FONT_MAPPING = {
    # Latin and Cyrillic scripts
    "en": "NotoSans-Regular.ttf",
    "fr": "NotoSans-Regular.ttf",
    "de": "NotoSans-Regular.ttf",
    "es": "NotoSans-Regular.ttf",
    "it": "NotoSans-Regular.ttf",
    "pt": "NotoSans-Regular.ttf",
    "id": "NotoSans-Regular.ttf",
    "tr": "NotoSans-Regular.ttf",
    "vi": "NotoSans-Regular.ttf",
    "sw": "NotoSans-Regular.ttf",
    "nl": "NotoSans-Regular.ttf",
    "pl": "NotoSans-Regular.ttf",
    "ru": "NotoSans-Regular.ttf",

    # Indian scripts
    "hi": "NotoSansDevanagari-Regular.ttf",
    "mr": "NotoSansDevanagari-Regular.ttf",
    "ta": "NotoSansTamil-Regular.ttf",
    "ml": "NotoSansMalayalam-Regular.ttf",
    "te": "NotoSansTelugu-Regular.ttf",
    "bn": "NotoSansBengali-Regular.ttf",
    "gu": "NotoSansGujarati-Regular.ttf",
    "kn": "NotoSansKannada-Regular.ttf",
    "pa": "NotoSansGurmukhi-Regular.ttf",

    # East Asian scripts
    "ja": "NotoSansJP-Regular.ttf",
    "ko": "NotoSansKR-Regular.ttf",
    "zh": "NotoSansSC-Regular.ttf",
    "zh-CN": "NotoSansSC-Regular.ttf",

    # Middle Eastern scripts
    "ar": "NotoSansArabic-Regular.ttf",
    "fa": "NotoSansArabic-Regular.ttf",
    "ur": "NotoNastaliqUrdu-Regular.ttf",
    "he": "NotoSansHebrew-Regular.ttf",

    # Southeast Asian scripts
    "th": "NotoSansThai-Regular.ttf",
}


# Register fonts only once
def register_font(font_filename):

    font_path = FONT_DIR / font_filename

    if not font_path.exists():
        raise FileNotFoundError(
            f"Font file not found: {font_path}"
        )

    font_name = Path(font_filename).stem

    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(
            TTFont(
                font_name,
                str(font_path),
                shapable=True
            )
        )

    return font_name


# Select font according to target language
def get_language_font(language_code):

    font_filename = FONT_MAPPING.get(
        language_code,
        "NotoSans-Regular.ttf"
    )

    return register_font(font_filename)


def generate_pdf(
    translated_pages,
    output_path,
    title="Translated Document",
    target_language="en"
):

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Automatically select the target language font
    body_font = get_language_font(target_language)

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=55,
        bottomMargin=55,
        title=title
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocumentTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#5141BD"),
        spaceAfter=25
    )

    heading_style = ParagraphStyle(
        "PageHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#5141BD"),
        spaceAfter=12
    )

    body_style = ParagraphStyle(
        "TranslatedBody",
        parent=styles["BodyText"],
        fontName=body_font,
        fontSize=11,
        leading=19,
        shaping=1,
        spaceAfter=12
    )

    story = [
        Paragraph(escape(title), title_style),
        Spacer(1, 10)
    ]

    for index, page_text in enumerate(translated_pages):

        story.append(
            Paragraph(
                f"Translated Page {index + 1}",
                heading_style
            )
        )

        safe_text = escape(page_text or "No text found.")
        safe_text = safe_text.replace("\n", "<br/>")

        story.append(
            Paragraph(safe_text, body_style)
        )

        if index < len(translated_pages) - 1:
            story.append(PageBreak())

    document.build(story)

    return output_path
