from fastapi import APIRouter, HTTPException
from db import reports_collection
from services.db_service import get_developer_checklist, get_report_by_id

router = APIRouter(prefix="/v5", tags=["Checklist V5"])

@router.get("/checklist/{id}")
def get_checklist(id: str):
    doc = get_report_by_id(id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Report not found")
    checklist = get_developer_checklist(id)
    return {"ticket_id": id, "developer_checklist": checklist}

    # report = reports_collection.find_one({"_id": id})
    # if not report:
    #     raise HTTPException(status_code=404, detail="Report not found")

    # checklist = report.get("json_report", {}).get("developer_checklist", [])
    # return {"ticket_id": id, "developer_checklist": checklist}
