# app/routes/reports_v5.py
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from services.db_service import get_report_by_id, list_reports, update_report, delete_report
from datetime import datetime
router = APIRouter(prefix="/v5", tags=["Reports V5"])

@router.get("/reports")
def list_reports_endpoint(skip: int = 0, limit: int = 100, platform: str = None):
    filters = {}
    if platform:
        filters["platform"] = platform
    total, docs = list_reports(skip=skip, limit=limit, filters=filters, sort=[("created_at", -1)])
    return {"count": total, "reports": docs}


@router.get("/reports/{id}")
def get_report(id: str):
    doc = get_report_by_id(id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    return doc


@router.put("/reports/{id}")
def update_report_endpoint(id: str, update_data: Dict[str, Any] = Body(...)):
    """
    Update a report with new fields (summary, description, project_name, platform,
    json_report, markdown_report). Automatically updates `updated_at`.
    """

    # ✅ Extend allowed update fields
    allowed = {
        "summary",
        "description",
        "project_name",
        "platform",
        "json_report",
        "markdown_report",
    }

    # Keep only allowed fields in update
    update_fields = {k: v for k, v in update_data.items() if k in allowed}

    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    # Always refresh timestamp
    update_fields["updated_at"] = datetime.utcnow()

    ok = update_report(id, update_fields)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Report {id} not found")

    # ✅ Fetch the updated report to return
    updated_doc = get_report_by_id(id)
    if not updated_doc:
        raise HTTPException(status_code=404, detail="Updated report not found")

    return {
        "status": "updated",
        "ticket_id": id,
        "updated_fields": list(update_fields.keys()),
        "updated_report": updated_doc,
    }


@router.delete("/reports/{id}")
def delete_report_endpoint(id: str):
    ok = delete_report(id)
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "deleted", "ticket_id": id}
