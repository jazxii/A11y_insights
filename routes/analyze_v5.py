from fastapi import APIRouter, HTTPException
from schemas import V5AnalyzeRequest
from ai_client import generate_a11y_report_v5
from services.db_service import save_report

router = APIRouter(prefix="/v5", tags=["Analyze V5"])

@router.post("/analyze")
async def analyze_v5(request: V5AnalyzeRequest):
    """
    Analyzes accessibility defect data and stores report in MongoDB.
    Uses ticket_id as primary key (_id).
    """
    try:
        # 1️⃣ Generate AI output
        ai_output = await generate_a11y_report_v5(
            ticket_id=request.ticket_id,
            summary=request.summary,
            description=request.description,
            platform=request.platform,
            ai_model=request.ai_model
        )


        # 2️⃣ Parse AI output -> Markdown + JSON
        markdown_report = ai_output.get("markdown", "")
        json_report = ai_output.get("json", {})


        # 3️⃣ Prepare MongoDB document
        report_data = {
            "ticket_id": request.ticket_id,
            "summary": request.summary,
            "description": request.description,
            "platform": request.platform,
            "project_name": request.project_name,
            "ai_model": request.ai_model,
            "markdown_report": markdown_report,
            "json_report": json_report
        }

        # 4️⃣ Save or update MongoDB record
        report_id = save_report(report_data)

        # 5️⃣ Return structured response
        return {
            "status": "success",
            "ticket_id": report_id,
            "markdown_report": markdown_report,
            "json_report": json_report,
            "saved": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze ticket: {str(e)}")

