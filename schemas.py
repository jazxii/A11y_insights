# schemas.py (V2)
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

class V5AnalyzeRequest(BaseModel):
    """
    Request body for /v5/analyze endpoint.
    """
    ticket_id: str
    summary: str
    description: str
    platform: Optional[str] = "iOS"
    project_name: Optional[str] = None
    ai_model: Optional[str] = "gpt-4o"


class ReportSchema(BaseModel):
    """
    MongoDB schema for a stored accessibility report.
    """
    _id: str = Field(..., alias="_id")  # ticket_id acts as primary key
    summary: str
    description: str
    platform: Optional[str]
    project_name: Optional[str]
    ai_model: str
    markdown_report: str
    json_report: Any
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class UserStoryIn(BaseModel):
    story_id: Optional[str] = Field(None, description='Optional external id (Jira id)')
    title: str
    description: str
    changelog: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class DetectedComponent(BaseModel):
    name: str
    type: str
    hint: Optional[str]

# New detailed schema pieces
class AccessibilityChecklistItem(BaseModel):
    text: str
    done: Optional[bool] = False

class WCAGReference(BaseModel):
    sc: str
    url: Optional[HttpUrl] = None
    note: Optional[str] = None

class DeveloperReportSection(BaseModel):
    title: str
    intent: Optional[str] = None
    expected_behavior: Optional[str] = None
    implementation_details: Optional[Dict[str, str]] = None  # e.g. {"web": "...", "ios": "...", "android": "..."}
    good_example: Optional[str] = None
    bad_example: Optional[str] = None
    wcag_references: Optional[List[WCAGReference]] = None
    testing_steps: Optional[List[str]] = None

class PlatformMatrixItem(BaseModel):
    attribute: str
    web: Optional[str] = None
    ios: Optional[str] = None
    android: Optional[str] = None

class TestingToolSuggestion(BaseModel):
    tool: str
    platform: Optional[str]
    use_case: Optional[str]

class SeverityItem(BaseModel):
    issue_type: str
    user_impact: Optional[str]
    severity: Optional[str]
    recommended_priority: Optional[str]

class AccessibilityAcceptanceCriterion(BaseModel):
    text: str

class A11yDeepReportOut(BaseModel):
    # extends typical report with deep analysis fields
    story_id: Optional[str]
    title: str
    summary: Optional[str]
    detected_components: List[DetectedComponent] = []
    checklist: Optional[List[AccessibilityChecklistItem]] = []
    report_sections: Optional[List[DeveloperReportSection]] = []
    platform_matrix: Optional[List[PlatformMatrixItem]] = []
    testing_tools: Optional[List[TestingToolSuggestion]] = []
    severity_table: Optional[List[SeverityItem]] = []
    acceptance_criteria: Optional[List[AccessibilityAcceptanceCriterion]] = []
    raw_markdown: Optional[str] = None
    created_at: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

# Keep old ReportOut compatibility (simple)
class WCAGMapping(BaseModel):
    criterion: str
    url: Optional[str]
    principle: Optional[str] = None

class ComponentInsight(BaseModel):
    component: DetectedComponent
    issues: List[str] = []
    suggestions: List[str] = []
    wcag_references: List[WCAGMapping] = []

class ReportOut(BaseModel):
    story_id: Optional[str]
    title: str
    summary: str
    detected_components: List[DetectedComponent]
    insights: List[ComponentInsight]
    severity: Optional[str]
    created_at: Optional[str]
    
class WCAGOverview(BaseModel):
    sc_number: str
    name: str
    link: HttpUrl
    applies_to: List[str]
    
class WCAGContextLink(BaseModel):
    related_checklist: Optional[str]
    related_developer_report: Optional[str]
    story_segment: Optional[str]

class WCAGOverview(BaseModel):
    sc_number: str
    name: str
    link: HttpUrl
    applies_to: List[str]
    context_links: Optional[List[WCAGContextLink]] = None

class DeveloperChecklistItem(BaseModel):
    text: str

class WCAGRef(BaseModel):
    sc_number: str
    name: str
    link: HttpUrl

class DeveloperReportItem(BaseModel):
    title: str
    intent: Optional[str]
    expected_behavior: Optional[str]
    non_accessible_example: Optional[str]
    accessible_example: Optional[str]
    web_guidance: Optional[str]
    ios_guidance: Optional[str]
    android_guidance: Optional[str]
    wcag_reference: Optional[WCAGRef]
    testing_tips: Optional[List[str]]

class PlatformMatrixItem(BaseModel):
    attribute: str
    web: Optional[str]
    ios: Optional[str]
    android: Optional[str]

class TestingToolItem(BaseModel):
    tool: str
    platform: Optional[str]
    use_case: Optional[str]

class SeverityPrediction(BaseModel):
    issue_type: str
    user_impact: str
    severity: str
    recommended_priority: str

class Metadata(BaseModel):
    generated_at: str
    model_version: str
    confidence_score: float

class A11yV3JSONOut(BaseModel):
    wcag_overview: List[WCAGOverview]
    developer_checklist: List[str]
    developer_report: List[DeveloperReportItem]
    platform_matrix: List[PlatformMatrixItem]
    testing_tools: List[TestingToolItem]
    severity_predictions: List[SeverityPrediction]
    acceptance_criteria: List[str]
    metadata: Metadata