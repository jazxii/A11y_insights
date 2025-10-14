# app/services/save_markdown.py

import os
import re
from datetime import datetime

def sanitize_filename(title: str) -> str:
    """
    Converts the story title into a safe filename.
    Removes invalid characters and trims spaces.
    """
    sanitized = re.sub(r'[<>:"/\\|?*]', '', title)  # remove invalid chars
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()  # collapse spaces
    return sanitized[:150]  # limit length for safety

def save_markdown_report(response_data: dict, output_dir: str = "output") -> str:
    """
    Saves the raw_markdown from OpenAI output into a Markdown file.

    Args:
        response_data (dict): AI output containing title, raw_markdown, and created_at.
        output_dir (str): Folder to store generated markdown files.

    Returns:
        str: Full path of the saved file.
    """
    title = response_data.get("title", "Untitled Report")
    raw_md = response_data.get("raw_markdown", "")
    created_at = response_data.get("created_at", datetime.utcnow().isoformat())

    # Format date prefix (YYYY-MM-DD)
    try:
        date_prefix = datetime.fromisoformat(created_at.replace("Z", "")).strftime("%Y-%m-%d")
    except Exception:
        date_prefix = datetime.utcnow().strftime("%Y-%m-%d")

    # Build filename
    safe_title = sanitize_filename(title)
    filename = f"{date_prefix}_{safe_title}.md"

    # Create output directory if missing
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    # Clean and write Markdown
    clean_md = raw_md.strip().replace("\r\n", "\n")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(clean_md)

    return file_path
