# ai_client.py (V2)
from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
import re
from typing import Dict, Any, Optional
from openai import OpenAI
from config import settings

logger = logging.getLogger("accessibility_insights.ai_client")
logging.basicConfig(level=logging.INFO)

# Mock markdown fallback in case OpenAI key or API unavailable
MOCK_MARKDOWN = """
### 🧩 Component Context: Sample Button

#### Accessibility Developer Checklist
- [ ] Ensure button has accessible name.
- [ ] Do not rely on color alone for state indication.

### Developer Accessibility Report – Sample Button
1. **Intent:** Buttons must be operable and perceivable for assistive technologies.
- **Expected Behavior:** Buttons expose name and role to screen readers.
- **Implementation Details (Web):**
```html
<button aria-label="Save">Save</button>
````

### Platform Matrix

| Accessibility Attribute | Web        | iOS                | Android            |
| ----------------------- | ---------- | ------------------ | ------------------ |
| Labeling                | aria-label | accessibilityLabel | contentDescription |

### Testing Tools

* AXE DevTools
* VoiceOver (iOS)
* TalkBack (Android)

### Severity Prediction Table

| Issue Type    | User Impact                            | Severity | Priority |
| ------------- | -------------------------------------- | -------- | -------- |
| Missing label | Screen reader users unaware of control | High     | P1       |

### Accessibility Acceptance Criteria

* Buttons have programmatic labels.
* Button names are announced by assistive tech.
  """

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _get_openai_client() -> Optional[OpenAI]:
    api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        logger.exception("Failed to instantiate OpenAI client")
        return None


def _parse_ai_json_text(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            snippet = text[start:end]
            return json.loads(snippet)
        except Exception:
            return None


def _extract_markdown_sections(md: str) -> Dict[str, str]:
    """
    Split Markdown content by major headers (### or ####).
    Returns a dictionary of {header: section body}.
    """
    if not md:
        return {}
    md = md.replace("\r\n", "\n").strip()
    parts = re.split(r"\n(?=#{3,}\s)", md)
    sections = {}
    for part in parts:
        lines = part.strip().split("\n", 1)
        header = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections[header] = body
    return sections

# ------------------------------------------------------------------------------
# Main function
# ------------------------------------------------------------------------------

def analyze_with_ai(user_story: dict) -> Dict[str, Any]:
    """
    Calls OpenAI to perform Deep Ticket Analysis Mode.
    Returns dict with:
    - source: "mock" | "openai"
    - markdown: full Markdown text (if present)
    - sections: parsed Markdown sections
    - parsed_json: if model returns JSON in response
    """
    system_prompt = (
        "You are an Accessibility Implementation Advisor trained in WCAG 2.2 and "
        "cross-platform accessibility APIs. Interpret the provided software ticket "
        "and produce a DEEP TICKET ANALYSIS in Markdown.\n\n"
        "Your output must contain these exact sections:\n"
        "### Accessibility Developer Checklist\n"
        "### Developer Accessibility Report\n"
        "### Platform Matrix\n"
        "### Testing Tools\n"
        "### Severity Prediction Table\n"
        "### Accessibility Acceptance Criteria\n\n"
        "Each section should contain actionable, developer-focused accessibility insights, "
        "WCAG 2.2 references with links, code examples for Web/iOS/Android, "
        "testing guidance, and severity ratings. Respond in Markdown only."
    )

    user_prompt = f"""Analyze the following product story for accessibility implications.

Input Story (JSON):
{json.dumps(user_story, indent=2)}

Expected Output:
Markdown document with all sections above. Include actionable checklist items,
detailed developer report (intent, expected vs. actual, examples, code snippets),
platform matrix, testing tool suggestions, severity prediction table, and
accessibility acceptance criteria for JIRA inclusion.
"""

    client = _get_openai_client()
    if client is None:
        logger.info("OPENAI_API_KEY not set — returning MOCK_MARKDOWN")
        md = MOCK_MARKDOWN
        return {"source": "mock", "markdown": md, "sections": _extract_markdown_sections(md), "parsed_json": None}

    try:
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1400,
            temperature=0.0,
        )

        # Extract text content safely
        text = None
        try:
            if isinstance(resp, dict):
                text = resp["choices"][0]["message"]["content"]
            else:
                choices = getattr(resp, "choices", None)
                if choices:
                    first = choices[0]
                    msg = getattr(first, "message", None) or (first.get("message") if isinstance(first, dict) else None)
                    if msg:
                        text = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
        except Exception:
            logger.exception("Failed to extract text content from OpenAI response")

        if not text:
            logger.warning("OpenAI returned empty response — using mock fallback.")
            md = MOCK_MARKDOWN
            return {"source": "mock", "markdown": md, "sections": _extract_markdown_sections(md), "parsed_json": None}

        # Try parsing JSON block if present
        parsed_json = _parse_ai_json_text(text)

        # Markdown mode preferred
        if not parsed_json:
            sections = _extract_markdown_sections(text)
            return {"source": "openai", "markdown": text, "sections": sections, "parsed_json": None}

        # JSON-only mode fallback
        return {"source": "openai", "markdown": None, "sections": {}, "parsed_json": parsed_json}

    except Exception:
        logger.exception("OpenAI request failed — returning mock response.")
        md = MOCK_MARKDOWN
        return {"source": "mock", "markdown": md, "sections": _extract_markdown_sections(md), "parsed_json": None}


def analyze_with_ai_v3(user_story: dict) -> Dict[str, Any]:
    """
    Accessibility Insights V3 – Deep Developer Guidance Mode
    Produces a structured, developer-focused Markdown accessibility report.
    """
    system_prompt = """
You are an **Accessibility Implementation Advisor** specializing in **WCAG 2.2**, **ARIA**, and **platform accessibility APIs (Web/iOS/Android)**.
Your task is to deeply analyze a product story and generate a **developer-ready accessibility report** in standardized Markdown.

Each report must follow the exact structure and headings shown below, but **populate all tables and examples dynamically** based on the story’s context.

---

# 🧩 Component Context: <component name / UI element>

## Accessibility Developer Checklist
- [ ] Include 5–8 **developer-focused, testable accessibility actions**
- [ ] Cover aspects like **labeling, focus, color, feedback, and assistive tech support**
- [ ] Each checklist item should be **clear, actionable, and measurable**
📘 **WCAG References:** SC numbers only (comma-separated)

---

### Developer Accessibility Report – <Feature / Use Case>

Include **2–3 detailed subsections** covering distinct accessibility aspects (e.g., focus handling, error messaging, contrast).

Each subsection must include:
1. **<Aspect Name>**
   - **Intent:** Explain why this aspect matters for accessibility
   - **Expected Behavior:** Describe what accessible implementation looks like
   - **Non-Accessible Example:** Show incorrect implementation (code snippet)
   - **Accessible Example:** Show corrected implementation (code snippet)
   - **Implementation Tips:**
     - Web: <code guidance>
     - iOS: <code guidance>
     - Android: <code guidance>
   - **WCAG Reference:** Include SC number, name, and link
   - **Validation Step:** Suggest a screen reader or testing action

---

### WCAG Overview

| SC Number | Name | WCAG Link | Applies To | Context Links |
|------------|------|------------|-------------|----------------|
| Populate **relevant WCAG 2.2 criteria** identified from the story context. Each row must contain: |
| - A **valid SC number** (e.g., 1.3.1, 2.4.3, 3.3.1, 1.4.3, etc.) |
| - The **Success Criterion name** |
| - The **official WCAG 2.2 Understanding link** |
| - A short description of what part of accessibility it governs (Applies To) |
| - Context links mapping to the **developer checklist**, **developer report**, and **story segment** |

Example:
| `3.3.1` | **Error Identification** | [WCAG 2.2 – Error Identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html) | *Error Handling, Form Validation* | **Related Checklist:** Associate error messages with inputs.<br>**Related Developer Report:** Error Announcement.<br>**Story Segment:** Checkout error label. |

*(Generate unique WCAG entries for each story — never reuse static examples.)*

---

### Platform Matrix
| Accessibility Attribute | Web | iOS | Android |
|---------------------------|-----|-----|----------|
| Populate platform-specific **accessibility techniques** relevant to the story. |
| - Each row represents one accessibility concept (Focus, Labeling, Contrast, etc.) |
| - Web column: ARIA or HTML guidance |
| - iOS column: UIKit or SwiftUI API guidance |
| - Android column: Jetpack Compose or XML attribute guidance |

*(Do not reuse fixed examples. Generate new attributes and guidance based on the story context.)*

---

### Testing Tools Suggestions
| Tool | Platform | Use Case |
|------|-----------|----------|
| Suggest 4–6 accessibility testing tools relevant to this feature or platform. |
| Examples include: AXE, Accessibility Scanner, VoiceOver, TalkBack, Lighthouse, NVDA, JAWS, etc. |
| Each entry must include a **platform** and a **specific testing purpose** (e.g., contrast validation, ARIA role check, focus order verification). |

*(Do not copy fixed rows; generate dynamically.)*

---

### Severity Prediction Table
| Issue Type | User Impact | Severity | Recommended Priority |
|-------------|--------------|-----------|----------------------|
| Predict 6–9 possible accessibility issues arising from this story context. |
| - Use realistic issue names (e.g., Missing Alt Text, Improper Focus Order) |
| - Specify real-world user impact |
| - Assign **High / Medium / Low** severity |
| - Assign **P1 / P2 / P3** recommended priority |

*(Values must be based on the story’s accessibility risk — not static examples.)*

---

### Accessibility Acceptance Criteria (for JIRA)
- List **4–6 acceptance criteria** ensuring the feature meets accessibility compliance.
- Each should describe an expected accessible behavior, not just a test step.
- Mention both functional (keyboard, screen reader) and visual (contrast, color) aspects.

---
#### 🎯 Example Instruction Summary for the Model

**Goal:** Build a WCAG Overview table that acts as a semantic map between accessibility criteria, the developer checklist, and the corresponding developer report details for the user story.

---

### ✅ Developer Note
When added to your `system_prompt`, this Markdown table teaches the model the **structure and relationships** to maintain between WCAG, checklist, and developer report data.

---

### Output Rules
1. Respond **only** in Markdown using the structure above.
2. Do **not** return JSON, explanations, or reasoning text.
3. Properly analyze the user story to identify relevant WCAG success criteria and situations where Accessibility comes into play with WCAG A and AA Conformance Levels.
4. Generate **unique**, story-specific examples, WCAG mappings, and tables.
5. Use realistic, platform-accurate code snippets and tool suggestions.
6. Focus tone on **developers**, with instructional and corrective guidance.
7. Ensure all WCAG references use **official 2.2 Understanding URLs**.
"""
    user_prompt = f"""
Analyze the following product story for accessibility implications.

Input Story (JSON):
{json.dumps(user_story, indent=2)}

Generate a full accessibility report in Markdown following the template above.
"""

    client = _get_openai_client()
    if client is None:
        return {
            "source": "mock",
            "markdown": "Mocked Markdown Accessibility Report (V3 mode)",
            "sections": {},
        }

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=2000,
        )

        text = response.choices[0].message.content
        return {"source": "openai", "markdown": text, "sections": {}}

    except Exception as e:
        logger.exception("V3 OpenAI request failed.")
        return {"source": "mock", "markdown": f"Error or mock response: {e}", "sections": {}}


def analyze_with_ai_v3json(user_story: dict) -> Dict[str, Any]:
    """
    A11y Insights V3JSON — Structured Developer Output
    Direct JSON generation from the LLM following strict schema.
    """
    system_prompt = """
You are an Accessibility Implementation Advisor specializing in WCAG 2.2 and platform APIs (Web/iOS/Android).

Generate a *fully structured JSON* accessibility developer report based on the user story below.

Follow this exact JSON schema:

{
  "wcag_overview": [
    {
      "sc_number": "string",
      "name": "string",
      "link": "url",
      "applies_to": ["string"],
      "context_links": [
        {
          "related_checklist": "string",
          "related_developer_report": "string",
          "story_segment": "string"
        }
      ]
    }
  ],
    "developer_checklist": ["string", "string", "..."],
  "developer_report": [
    {
      "title": "<must exactly match a checklist item>",
      "intent": "string",
      "expected_behavior": "string",
      "non_accessible_example": "string (HTML, Swift, or Java example)",
      "accessible_example": "string (HTML, Swift, or Java example)",
      "web_guidance": "string",
      "ios_guidance": "string",
      "android_guidance": "string",
      "wcag_reference": {
        "sc_number": "string",
        "name": "string",
        "link": "url"
      },
      "testing_tips": ["string", "string"]
    }
  ],
  "platform_matrix": [{"attribute": "string", "web": "string", "ios": "string", "android": "string"}],
  "testing_tools": [{"tool": "string", "platform": "string", "use_case": "string"}],
  "severity_predictions": [{"issue_type": "string", "user_impact": "string", "severity": "string", "recommended_priority": "string"}],
  "acceptance_criteria": ["string"],
  "metadata": {"generated_at": "ISO datetime", "model_version": "gpt-4", "confidence_score": 0.95}
}

---

🧠 Rules:
- Properly analyze the user story to identify relevant WCAG success criteria and situations where Accessibility comes into play with WCAG A and AA Conformance Levels.
- Each `wcag_overview` entry must include **context_links** that describe how that criterion applies to:
  - specific checklist items
  - developer report entries
  - parts of the user story
- If multiple WCAG SCs apply to different aspects, include them all with distinct `context_links`.
- Every developer_report item must reference exactly one WCAG criterion (via `wcag_reference`).
- Respond only in valid JSON — no Markdown or natural language.
- Provide examples and guidance for Web, iOS, and Android.
- Fill all required fields — no null values.
"""

    user_prompt = f"Analyze this user story and produce the JSON accessibility developer report:\n{json.dumps(user_story, indent=2)}"

    client = _get_openai_client()
    if client is None:
        return {"source": "mock", "parsed_json": {"developer_checklist": ["Mocked item"], "metadata": {"generated_at": "N/A", "model_version": "mock", "confidence_score": 0.0}}}

    try:
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=2000,
        )
        text = resp.choices[0].message.content
        parsed_json = json.loads(text)
        return {"source": "openai", "parsed_json": parsed_json}
    except Exception as e:
        logger.exception("V3JSON generation failed")
        return {"source": "mock", "parsed_json": {"error": str(e)}}


def analyze_with_ai_v4(user_story: dict) -> Dict[str, Any]:
    """
    Accessibility Insights V4 — Generates the new Markdown structure required by PM.
    Returns: {"source": "openai"|"mock", "markdown": str}
    """
    system_prompt = """
You are an Accessibility Implementation Advisor specialized in WCAG 2.2, ARIA, and platform accessibility APIs (Web/iOS/Android).


Task: Analyze the product story (JSON) and produce a **developer-ready Markdown report** following the EXACT structure below. Respond only in Markdown.


Required structure (must appear exactly):


## Accessibility Developer Checklist
- [ ] Include 5–8 **developer-focused, testable accessibility actions**
- [ ] Cover aspects like **labeling, focus, color, feedback, and assistive tech support**
- [ ] Each checklist item should be **clear, actionable, and measurable**
- Under each checklist item include:
- **Intent:** Why this matters
- **Non-Accessible Example:** code block showing the incorrect implementation
- **Accessible Example:** code block with corrected implementation
- **Implementation Tips:** Web: <code>, iOS: <code>, Android: <code> (if applicable)
- **WCAG Reference:** SC number — name — official Understanding URL


---


### Accessibility Acceptance Criteria (for JIRA)
- Provide 6–8 acceptance criteria. Each must describe an expected accessible behavior (keyboard + screen reader behaviors, plus visual contrast/state expectations). Use concise bullet points.


Rules:
- Properly analyze the user story to identify relevant WCAG success criteria and situations where Accessibility comes into play with WCAG A and AA Conformance Levels.
- Use real WCAG 2.2 SC numbers and the official Understanding links (https://www.w3.org/WAI/WCAG22/Understanding/<shortname>.html).
- Provide concrete, short code examples. Keep each code block under ~40 lines.
- Do not include any JSON or explanation outside the markdown report.
- Where SC applies, mention it inline next to the checklist item.


Tone: succinct, developer-focused, and actionable.
    """

    user_prompt = f"Analyze the following product story and produce a V4 Markdown report:\n\n{json.dumps(user_story, indent=2)}"

    client = _get_openai_client()
    if client is None:
        # Fallback: generate a small mocked but valid V4 Markdown sample
        mock = (
            "## Accessibility Developer Checklist\n"
            "- [ ] Ensure button has programmatic name (aria-label or visible text). **WCAG:** 4.1.2 — Name, Role, Value — https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html\n\n"
            " - **Intent:** Screen readers require programmatic names so users know what the control does.\n"
            " - **Non-Accessible Example:**\n"
            "```html\n<button></button>\n```\n"
            " - **Accessible Example:**\n"
            "```html\n<button aria-label=\"Save\">\n <span aria-hidden=\"true\">💾</span>\n</button>\n```\n"
            " - **Implementation Tips:** Web: Use aria-label or visible text; iOS: accessibilityLabel; Android: contentDescription.\n\n"
            "### Accessibility Acceptance Criteria (for JIRA)\n"
            "- Keyboard: Component is reachable and operable using Tab + Enter/Space.\n"
            "- Screen reader: Name and role are announced correctly.\n"
        )
        return {"source": "mock", "markdown": mock}

    try:
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=2500,
        )
        text = None
        try:
            text = resp["choices"][0]["message"]["content"] if isinstance(resp, dict) else resp.choices[0].message.content
        except Exception:
            # try safer path
            text = getattr(resp.choices[0].message, "content", None) if getattr(resp, "choices", None) else None

        if not text:
            raise Exception("Empty response from OpenAI")

        return {"source": "openai", "markdown": text}

    except Exception as e:
        logger.exception("V4 OpenAI request failed — returning mock")
        return {"source": "mock", "markdown": f"# Error generating V4 report: {e}\n\n(Mocked content would appear here)"}


