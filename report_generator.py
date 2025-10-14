from typing import List, Dict, Any, Optional
from ..schemas import (
    A11yDeepReportOut,
    ReportOut,
    DetectedComponent,
    ComponentInsight,
    WCAGMapping,
    AccessibilityChecklistItem,
    DeveloperReportSection,
    PlatformMatrixItem,
    TestingToolSuggestion,
    SeverityItem,
    AccessibilityAcceptanceCriterion,
)
from datetime import datetime
import re
import logging

logger = logging.getLogger("accessibility_insights.report_generator")

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _parse_checklist_from_section(text: str) -> List[AccessibilityChecklistItem]:
    if not text:
        return []
    items = []
    # Match both "- [ ]" style and numbered lists "1."
    for m in re.finditer(r"^(?:- \[([ xX])\]\s*|(\d+)\.\s*)(.+)$", text, re.MULTILINE):
        done_flag = (m.group(1) or "").strip().lower() == "x"
        txt = m.group(3).strip()
        items.append(AccessibilityChecklistItem(text=txt, done=done_flag))
    return items


def _parse_simple_list(text: str) -> List[str]:
    if not text:
        return []
    return [line.strip("-• ").strip() for line in text.splitlines() if line.strip().startswith(("-", "•", "*", "1."))]


def _parse_platform_matrix(text: str) -> List[PlatformMatrixItem]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines or "|" not in lines[0]:
        return []
    rows = []
    for line in lines[1:]:
        if "|" not in line or "---" in line:
            continue
        cols = [c.strip() for c in line.split("|") if c.strip()]
        if not cols:
            continue
        attr = cols[0]
        web = cols[1] if len(cols) > 1 else None
        ios = cols[2] if len(cols) > 2 else None
        android = cols[3] if len(cols) > 3 else None
        rows.append(PlatformMatrixItem(attribute=attr, web=web, ios=ios, android=android))
    return rows


def _parse_severity_table(text: str) -> List[SeverityItem]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines or "|" not in lines[0]:
        return []
    header_cols = [h.strip().lower() for h in lines[0].split("|") if h.strip()]
    items = []
    for line in lines[1:]:
        if "|" not in line or "---" in line:
            continue
        cols = [c.strip() for c in line.split("|") if c.strip()]
        mapping = {}
        for i, h in enumerate(header_cols):
            mapping[h] = cols[i] if i < len(cols) else ""
        items.append(
            SeverityItem(
                issue_type=mapping.get("issue type") or mapping.get("issue") or "",
                user_impact=mapping.get("user impact") or "",
                severity=mapping.get("severity") or "",
                recommended_priority=mapping.get("recommended priority") or mapping.get("priority") or "",
            )
        )
    return items


def _parse_developer_report_section(text: str) -> DeveloperReportSection:
    """
    Extracts key sub-sections from the Developer Accessibility Report markdown:
    - Intent
    - Expected Behavior (or Expected vs Actual)
    - Good / Bad examples
    - Code snippets
    """
    intent = None
    expected_behavior = None
    good_example = None
    bad_example = None
    implementation_details = {}

    # Extract "Intent:"
    m_intent = re.search(r"\*\*Intent:\*\*\s*(.+)", text)
    if m_intent:
        intent = m_intent.group(1).strip()

    # Extract "Expected Behavior" or "Expected vs Actual"
    m_expected = re.search(r"\*\*Expected[^:]*:\*\*\s*(.+)", text)
    if m_expected:
        expected_behavior = m_expected.group(1).strip()

    # Extract code snippets for Web/iOS/Android
    web_match = re.search(r"Web:\s*```[a-zA-Z]*\n(.+?)```", text, re.DOTALL)
    ios_match = re.search(r"iOS:\s*```[a-zA-Z]*\n(.+?)```", text, re.DOTALL)
    android_match = re.search(r"Android:\s*```[a-zA-Z]*\n(.+?)```", text, re.DOTALL)
    if web_match:
        implementation_details["web"] = web_match.group(1).strip()
    if ios_match:
        implementation_details["ios"] = ios_match.group(1).strip()
    if android_match:
        implementation_details["android"] = android_match.group(1).strip()

    # General code block extraction (fallback)
    code_blocks = re.findall(r"```[a-zA-Z]*\n(.+?)```", text, re.DOTALL)
    if code_blocks and not implementation_details:
        good_example = code_blocks[0].strip()
        if len(code_blocks) > 1:
            bad_example = code_blocks[1].strip()

    # Testing steps (list items under report section)
    testing_steps = _parse_simple_list(text)

    return DeveloperReportSection(
        title="Developer Accessibility Report",
        intent=intent,
        expected_behavior=expected_behavior,
        implementation_details=implementation_details or None,
        good_example=good_example,
        bad_example=bad_example,
        wcag_references=None,
        testing_steps=testing_steps,
    )

# ---------------------------------------------------------------------------
# Core V2 report builder
# ---------------------------------------------------------------------------

def build_deep_report(
    story_id: Optional[str],
    title: str,
    description: str,
    detected_components: List[DetectedComponent],
    ai_result: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
) -> A11yDeepReportOut:
    md = ai_result.get("markdown")
    sections = ai_result.get("sections") or {}
    parsed_json = ai_result.get("parsed_json")

    checklist = []
    report_sections = []
    platform_matrix = []
    testing_tools = []
    severity_table = []
    acceptance_criteria = []

    # JSON-first structured extraction
    if parsed_json and isinstance(parsed_json, dict):
        raw_check = parsed_json.get("checklist") or parsed_json.get("developer_checklist")
        if raw_check and isinstance(raw_check, list):
            checklist = [AccessibilityChecklistItem(text=str(i)) for i in raw_check]

        raw_platform = parsed_json.get("platform_matrix") or parsed_json.get("platforms")
        if raw_platform and isinstance(raw_platform, list):
            for p in raw_platform:
                platform_matrix.append(PlatformMatrixItem(**p) if isinstance(p, dict) else PlatformMatrixItem(attribute=str(p)))

        raw_tools = parsed_json.get("testing_tools") or parsed_json.get("tools")
        if raw_tools and isinstance(raw_tools, list):
            for t in raw_tools:
                testing_tools.append(TestingToolSuggestion(tool=t if isinstance(t, str) else t.get("tool", "")))

        raw_sev = parsed_json.get("severity_table") or parsed_json.get("severity")
        if raw_sev and isinstance(raw_sev, list):
            for s in raw_sev:
                severity_table.append(SeverityItem(**s) if isinstance(s, dict) else SeverityItem(issue_type=str(s)))

        raw_accept = parsed_json.get("acceptance_criteria") or parsed_json.get("acceptance")
        if raw_accept and isinstance(raw_accept, list):
            for a in raw_accept:
                acceptance_criteria.append(AccessibilityAcceptanceCriterion(text=str(a)))

    # Markdown parsing
    if md:
        for hdr, body in sections.items():
            if "Checklist" in hdr:
                checklist = _parse_checklist_from_section(body)
            elif "Developer Accessibility Report" in hdr or "Accessibility Report" in hdr:
                report_sections.append(_parse_developer_report_section(body))
            elif "Platform Matrix" in hdr:
                platform_matrix = _parse_platform_matrix(body)
            elif "Testing Tools" in hdr:
                tools = _parse_simple_list(body)
                testing_tools = [
                TestingToolSuggestion(tool=t, platform=None, use_case=None)
                for t in tools
                ]   
            elif "Severity" in hdr:
                severity_table = _parse_severity_table(body)
            elif "Acceptance" in hdr:
                lines = [l.strip() for l in body.splitlines() if l.strip().startswith(("-", "1.", "*"))]
                acceptance_criteria = [AccessibilityAcceptanceCriterion(text=l.lstrip("-*1234567890. ").strip()) for l in lines]

    report = A11yDeepReportOut(
        story_id=story_id,
        title=title,
        summary=(md[:200] if md else description[:200]),
        detected_components=detected_components,
        checklist=checklist,
        report_sections=report_sections,
        platform_matrix=platform_matrix,
        testing_tools=testing_tools,
        severity_table=severity_table,
        acceptance_criteria=acceptance_criteria,
        raw_markdown=md,
        created_at=datetime.utcnow().isoformat() + "Z",
        meta=meta or {},
    )
    return report

# ---------------------------------------------------------------------------
# Legacy V1 builder (for backward compatibility)
# ---------------------------------------------------------------------------

def build_report(story_id: str | None, title: str, description: str,
                 components: List[DetectedComponent], ai_json: Dict[str, Any]) -> ReportOut:
    insights = []

    ai_components = ai_json.get('components') or {}
    if isinstance(ai_components, list):
        comp_map: Dict[str, Any] = {}
        for item in ai_components:
            if isinstance(item, str):
                comp_map[item] = comp_map.get(item, {})
            elif isinstance(item, dict):
                name = item.get('component') or item.get('name')
                if name:
                    comp_map[name] = {**comp_map.get(name, {}), **item}
        ai_components = comp_map
    elif not isinstance(ai_components, dict):
        ai_components = {}

    for ins in (ai_json.get('insights') or []):
        if not isinstance(ins, dict):
            continue
        name = ins.get('component') or ins.get('name')
        if not name:
            continue
        entry = ai_components.setdefault(name, {})
        if ins.get('issues'):
            entry.setdefault('issues', []).extend(ins.get('issues') or [])
        if ins.get('recommendation'):
            entry.setdefault('suggestions', []).append(ins.get('recommendation'))
        if ins.get('wcag'):
            entry.setdefault('wcag', []).append({
                "criterion": ins.get('wcag'),
                "url": ins.get('wcag_url'),
                "principle": ins.get('principle')
            })

    for c in components:
        comp_info = ai_components.get(c.name) or {}
        issues = comp_info.get('issues', [])
        suggestions = comp_info.get('suggestions', [])
        wcag_list = []
        raw_wcag = comp_info.get('wcag', [])
        for w in (raw_wcag if isinstance(raw_wcag, list) else [raw_wcag]):
            if isinstance(w, dict):
                wcag_list.append(WCAGMapping(
                    criterion=w.get('criterion', ''),
                    url=w.get('url', ''),
                    principle=w.get('principle', '')
                ))
        insights.append(ComponentInsight(
            component=c,
            issues=issues,
            suggestions=suggestions,
            wcag_references=wcag_list
        ))

    return ReportOut(
        story_id=story_id,
        title=title,
        summary=ai_json.get('short_summary', description[:200]),
        detected_components=components,
        insights=insights,
        severity=ai_json.get('overall_severity', 'medium'),
        created_at=datetime.utcnow().isoformat() + 'Z'
    )
