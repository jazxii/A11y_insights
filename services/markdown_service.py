# app/services/markdown_service.py
import io
import re
import unicodedata
from datetime import datetime

def sanitize_filename(name: str) -> str:
    """
    Create a filesystem-safe filename from name.
    """
    if not name:
        name = "report"
    # normalize & remove non-ascii
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    # strip disallowed chars
    name = re.sub(r"[^\w\s-]", "", name).strip()
    name = re.sub(r"[-\s]+", "_", name)
    return name[:200]

def markdown_bytes_io(markdown: str) -> io.BytesIO:
    """
    Return a BytesIO containing the markdown text (utf-8).
    """
    b = io.BytesIO()
    b.write(markdown.encode("utf-8"))
    b.seek(0)
    return b

def default_md_filename(ticket_id: str, title: str = None) -> str:
    base = ticket_id or "report"
    if title:
        name = f"{base}_{sanitize_filename(title)}"
    else:
        name = f"{base}_A11y_Report"
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{name}_{timestamp}.md"
