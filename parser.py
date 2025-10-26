import re
from typing import List
from schemas import DetectedComponent
import json
import logging
# A small rule-based parser to extract likely components from user story text.
COMPONENT_KEYWORDS = {
 'button': [r'button', r'click', r'tap'],
 'form': [r'form', r'submit', r'input field', r'input'],
 'modal': [r'modal', r'dialog', r'popup'],
 'toast': [r'toast', r'notification', r'alert'],
 'search': [r'search', r'find'],
 'navigation': [r'nav', r'navigate', r'menu', r'tab'],
 'image': [r'image', r'photo', r'thumbnail'],
 'link': [r'link', r'anchor'],
 'list': [r'list', r'items', r'results'],
}

logger = logging.getLogger(__name__)

def extract_components(text: str) -> List[DetectedComponent]:
 text_l = text.lower()
 found = {}
 for comp, patterns in COMPONENT_KEYWORDS.items():
     for p in patterns:
         if re.search(p, text_l):
             found[comp] = found.get(comp, 0) + 1
 components = []
 for c in found.keys():
     components.append(DetectedComponent(name=c, type=c, hint='Detected by keyword match'))
 # Fallback: if none found, suggest generic 'screen' component
 if not components:
     components.append(DetectedComponent(name='screen', type='screen', hint='No specific components detected - treat as full screen flow'))
 return components

def parse_to_markdown_and_json(ai_output: str):
    """
    Parses AI output that may contain both Markdown and JSON sections.

    Supports these formats:
    1. Markdown only (fallback)
    2. Markdown followed by JSON, delimited by:
       ---JSON-START--- and ---JSON-END---

    Returns:
        tuple: (markdown_report: str, json_report: dict)
    """

    if not ai_output or not isinstance(ai_output, str):
        logger.warning("Invalid AI output type — expected string.")
        return "", {}

    markdown_report = ai_output.strip()
    json_report = {}

    try:
        # Check for JSON delimiters
        if "---JSON-START---" in ai_output:
            parts = ai_output.split("---JSON-START---")
            markdown_report = parts[0].strip()

            if len(parts) > 1:
                json_raw = parts[1].split("---JSON-END---")[0].strip()

                # Handle malformed JSON safely
                try:
                    json_report = json.loads(json_raw)
                except json.JSONDecodeError:
                    # Attempt recovery — remove trailing commas or invalid characters
                    cleaned = re.sub(r",\s*}", "}", json_raw)
                    cleaned = re.sub(r",\s*]", "]", cleaned)
                    try:
                        json_report = json.loads(cleaned)
                        logger.warning("JSON parsed after cleanup.")
                    except Exception:
                        logger.error("Failed to parse JSON even after cleanup.")
                        json_report = {}

        # 🧩 Case 2: Try to detect inline JSON (no delimiters)
        elif re.search(r"\{[\s\S]*\}", ai_output):
            # Extract first JSON-like structure
            json_candidate = re.search(r"\{[\s\S]*\}", ai_output)
            if json_candidate:
                json_text = json_candidate.group(0)
                try:
                    json_report = json.loads(json_text)
                    markdown_report = ai_output.replace(json_text, "").strip()
                except json.JSONDecodeError:
                    logger.warning("Inline JSON detected but failed to parse.")

    except Exception as e:
        logger.exception(f"Error parsing AI output: {e}")

    # 🧩 Ensure defaults
    markdown_report = markdown_report or "# Accessibility Report\n*(No content)*"
    json_report = json_report or {
        "developer_checklist": [],
        "acceptance_criteria": [],
        "wcag_references": []
    }

    return markdown_report, json_report
