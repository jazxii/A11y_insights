# app/routes/reports_v5.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.db_service import get_report_by_id, list_reports, update_report, delete_report

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
def update_report_endpoint(id: str, update_data: Dict[str, Any]):
    allowed = {"summary", "description", "project_name", "platform"}
    update_fields = {k: v for k, v in update_data.items() if k in allowed}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    ok = update_report(id, update_fields)
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "updated", "ticket_id": id, "updated_fields": update_fields}


@router.delete("/reports/{id}")
def delete_report_endpoint(id: str):
    ok = delete_report(id)
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "deleted", "ticket_id": id}
