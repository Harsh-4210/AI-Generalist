import fitz  # PyMuPDF
import base64
from typing import Optional

def extract_pdf_content(pdf_path: str) -> dict:
    """
    Extract all text and images from a PDF file.
    Returns dict with 'text' (str) and 'images' (list of dicts).
    Each image dict has: bytes, ext, page, index, b64
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"text": f"[ERROR: Could not open PDF: {e}]", "images": [], "page_count": 0}

    full_text = ""
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()
        full_text += f"\n--- Page {page_num + 1} ---\n{page_text}"

        # Extract images from this page
        img_list = page.get_images(full=True)
        for img_index, img in enumerate(img_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                img_ext = base_image.get("ext", "png")
                # Only include reasonably sized images (skip tiny icons)
                if len(img_bytes) > 2000:
                    images.append({
                        "bytes": img_bytes,
                        "ext": img_ext,
                        "page": page_num + 1,
                        "index": img_index,
                        "b64": base64.b64encode(img_bytes).decode("utf-8"),
                        "size": len(img_bytes)
                    })
            except Exception:
                continue

    page_count = len(doc)
    doc.close()
    return {
        "text": full_text.strip(),
        "images": images,
        "page_count": page_count
    }

def extract_pdf_content_from_bytes(pdf_bytes: bytes) -> dict:
    """Extract content from PDF bytes (for API usage)."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        return {"text": f"[ERROR: {e}]", "images": [], "page_count": 0}

    full_text = ""
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        full_text += f"\n--- Page {page_num + 1} ---\n{page.get_text()}"

        for img_index, img in enumerate(page.get_images(full=True)):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                img_ext = base_image.get("ext", "png")
                if len(img_bytes) > 2000:
                    images.append({
                        "bytes": img_bytes,
                        "ext": img_ext,
                        "page": page_num + 1,
                        "index": img_index,
                        "b64": base64.b64encode(img_bytes).decode("utf-8"),
                        "size": len(img_bytes)
                    })
            except Exception:
                continue

    page_count = len(doc)
    doc.close()
    return {
        "text": full_text.strip(),
        "images": images,
        "page_count": page_count
    }
