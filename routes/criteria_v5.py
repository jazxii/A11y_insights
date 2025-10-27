# app/routes/criteria_v5.py
from fastapi import APIRouter, HTTPException
from services.db_service import get_acceptance_criteria, get_report_by_id

router = APIRouter(prefix="/v5", tags=["Criteria V5"])

@router.get("/criteria/{id}")
def get_criteria(id: str):
    doc = get_report_by_id(id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    criteria = get_acceptance_criteria(id)
    return {"ticket_id": id, "acceptance_criteria": criteria}
