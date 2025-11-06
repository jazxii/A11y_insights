# app/routes/reports_v5.py
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from services.db_service import get_report_by_id, list_reports, update_report, delete_report, get_report_by_ticket_id
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


# @router.put("/reports/{id}")
# def update_report_endpoint(id: str, update_data: Dict[str, Any] = Body(...)):
#     """
#     Update a report with new fields (summary, description, project_name, platform,
#     json_report, markdown_report). Automatically updates `updated_at`.
#     """

#     # ✅ Extend allowed update fields
#     allowed = {
#         "summary",
#         "description",
#         "project_name",
#         "platform",
#         "json_report",
#         "markdown_report",
#     }

#     # Keep only allowed fields in update
#     update_fields = {k: v for k, v in update_data.items() if k in allowed}

#     if not update_fields:
#         raise HTTPException(status_code=400, detail="No valid fields to update")

#     # Always refresh timestamp
#     update_fields["updated_at"] = datetime.utcnow()

#     ok = update_report(id, update_fields)
#     if not ok:
#         raise HTTPException(status_code=404, detail=f"Report {id} not found")

#     # ✅ Fetch the updated report to return
#     updated_doc = get_report_by_id(id)
#     if not updated_doc:
#         raise HTTPException(status_code=404, detail="Updated report not found")

#     return {
#         "status": "updated",
#         "ticket_id": id,
#         "updated_fields": list(update_fields.keys()),
#         "updated_report": updated_doc,
#     }

@router.put("/reports/{id}")
def update_report_endpoint(id: str, update_data: Dict[str, Any] = Body(...)):
    """
    Updates a report in MongoDB by ticket_id.
    Preserves created_at, updates updated_at, and returns structured response.
    """

    try:
        # 1️⃣ Validate request
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        # 2️⃣ Fetch existing report
        existing_report = get_report_by_ticket_id(id)
        if not existing_report:
            raise HTTPException(status_code=404, detail=f"Report {id} not found")

        # 3️⃣ Merge updates
        updated_fields = {}
        allowed = {
            "summary", "description", "project_name", "platform",
            "json_report", "markdown_report"
        }

        for key, value in update_data.items():
            if key in allowed:
                updated_fields[key] = value

        if not updated_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        # 4️⃣ Preserve created_at, update timestamp
        updated_fields["updated_at"] = datetime.utcnow().isoformat()
        updated_fields["created_at"] = existing_report.get("created_at", updated_fields["updated_at"])

        # 5️⃣ Update MongoDB record
        ok = update_report(id, updated_fields)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to update report in database")

        # 6️⃣ Fetch updated record to return
        updated_doc = get_report_by_ticket_id(id)
        if not updated_doc:
            raise HTTPException(status_code=404, detail="Updated document not found")

        # 7️⃣ Response structure aligned with /v5/analyze
        return {
            "status": "success",
            "ticket_id": id,
            "updated": True,
            "created_at": updated_doc.get("created_at"),
            "updated_at": updated_doc.get("updated_at"),
            "markdown_report": updated_doc.get("markdown_report"),
            "json_report": updated_doc.get("json_report"),
            "saved": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update report {id}: {str(e)}")


@router.delete("/reports/{id}")
def delete_report_endpoint(id: str):
    ok = delete_report(id)
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "deleted", "ticket_id": id}
