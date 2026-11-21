
import fitz
from pathlib import Path


def extract_pdf_text(pdf_path):
    """
    Extract text from every page of a PDF.
    Identify pages that may require OCR.
    """

    document = fitz.open(pdf_path)

    pages = []
    scanned_pages = []

    for page_number, page in enumerate(document, start=1):

        text = page.get_text("text").strip()

        # Detect pages with little or no selectable text
        if len(text) < 20:
            scanned_pages.append(page_number)

        pages.append({
            "page": page_number,
            "text": text
        })

    document.close()

    full_text = "\n\n".join(
        page["text"] for page in pages
    )

    return {
        "pages": pages,
        "total_pages": len(pages),
        "full_text": full_text,
        "total_characters": len(full_text),
        "scanned_pages": scanned_pages
    }
