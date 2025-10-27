# app/services/pdf_service.py
from fpdf import FPDF
import io
import textwrap
import logging

logger = logging.getLogger(__name__)

def generate_pdf_from_markdown(markdown: str, title: str = "A11y Report") -> io.BytesIO:
    """
    Convert markdown string into a simple PDF document.
    Returns an io.BytesIO with the PDF data (positioned at 0).
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    # Title
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, title, ln=True, align="L")
    pdf.ln(4)

    pdf.set_font("Arial", size=11)
    # Basic handling: preserve lines, wrap long lines
    for line in markdown.splitlines():
        # For code blocks we reduce wrapping width and prefix
        if line.strip().startswith("```"):
            # code fence open/close: keep as simple separator
            pdf.set_font("Courier", size=9)
            pdf.multi_cell(0, 6, line)
            pdf.set_font("Arial", size=11)
            continue

        # wrap text to ~90 characters per line (adjust if needed)
        wrapped = textwrap.wrap(line, width=90, replace_whitespace=False)
        if not wrapped:
            pdf.ln(3)
        for w in wrapped:
            pdf.multi_cell(0, 6, w)
    buffer = io.BytesIO()
    try:
        pdf.output(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.exception("Failed to generate PDF: %s", e)
        raise
