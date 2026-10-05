"""Read uploaded documents (.txt, .md, .pdf) into clean plain text."""
from __future__ import annotations

import io
import re


def _clean_pdf_text(text: str) -> str:
    """Fix typical PDF extraction artefacts so sentence splitting works."""
    text = text.replace("\r", "\n")
    # re-join words hyphenated across lines: "plagia-\nrism" -> "plagiarism"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # a single line break inside a sentence -> space (keep paragraph breaks)
    text = re.sub(r"(?<![.!?:\n])\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(uploaded_file) -> str:
    """Return plain text from a Streamlit UploadedFile. Raises ValueError on problems."""
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()  # safe to call on every rerun, unlike .read()

    if name.endswith(".pdf"):
        from pypdf import PdfReader

        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted and reader.decrypt("") == 0:
                raise ValueError("This PDF is password-protected.")
            pages = [(page.extract_text() or "") for page in reader.pages]
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Could not read this PDF: {exc}") from exc

        text = _clean_pdf_text("\n\n".join(pages))
        if not text:
            raise ValueError(
                "No text found in this PDF. It is probably a scanned image; "
                "OCR is needed for scanned PDFs."
            )
        return text

    return data.decode("utf-8", errors="ignore")
