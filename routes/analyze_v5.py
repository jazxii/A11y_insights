# routes/analyze_v5.py (your analyze endpoint)
from fastapi import APIRouter, HTTPException
from schemas import V5AnalyzeRequest
from ai_client import generate_a11y_report_v5
from services.db_service import save_report, get_report_by_ticket_id
from datetime import datetime

router = APIRouter(prefix="/v5", tags=["Analyze V5"])

@router.post("/analyze")
async def analyze_v5(request: V5AnalyzeRequest):
    """
    Analyzes accessibility data for a user story or JIRA ticket.
    If the report exists, updates it; otherwise, creates a new one.
    Returns `updated` boolean (True when this was an update).
    """
    try:
        # 1) Generate AI output
        ai_output = await generate_a11y_report_v5(
            ticket_id=request.ticket_id,
            summary=request.summary,
            description=request.description,
            platform=request.platform,
            ai_model=request.ai_model
        )

        # 2) Extract generated reports
        markdown_report = ai_output.get("markdown", "")
        json_report = ai_output.get("json", {})

        # 3) Prepare data payload
        report_data = {
            "ticket_id": request.ticket_id,
            "summary": request.summary,
            "description": request.description,
            "platform": request.platform,
            "project_name": request.project_name,
            "ai_model": request.ai_model,
            "markdown_report": markdown_report,
            "json_report": json_report,
        }

        # 4) Save to MongoDB (upsert) and read save_result
        save_result = save_report(report_data)  # returns dict
        # save_result keys: ticket_id, created (bool), created_at, updated_at

        updated = not bool(save_result.get("created", False))
        created_at = save_result.get("created_at")
        updated_at = save_result.get("updated_at")

        # 5) Return structured response with 'updated' boolean
        return {
            "status": "success",
            "ticket_id": save_result["ticket_id"],
            "platform": request.platform,
            "updated": updated,                # <-- frontend expects this
            "created_at": created_at,
            "updated_at": updated_at,
            "markdown_report": markdown_report,
            "json_report": json_report,
            "saved": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze ticket: {str(e)}")
