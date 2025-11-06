# app/services/db_service.py
from typing import Any, Dict, Iterable, List, Optional, Tuple
from datetime import datetime
import logging

from db import reports_collection  # assumes app.db initializes Mongo client and reports_collection
from pymongo.results import UpdateResult, DeleteResult

logger = logging.getLogger(__name__)


def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Mongo document to a plain dict for API responses:
    - map `_id` -> `id`
    - leave other fields intact
    """
    if not doc:
        return {}
    normalized = dict(doc)
    # Convert Mongo _id -> id (string)
    if "_id" in normalized:
        normalized["id"] = str(normalized["_id"])
        # Keep ticket_id as-is (if present)
    return normalized


def get_report_by_id(ticket_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single report document by its ticket_id (stored as _id in Mongo).
    Returns normalized dict or None if not found.
    """
    try:
        doc = reports_collection.find_one({"_id": ticket_id})
        return _normalize_doc(doc) if doc else None
    except Exception as e:
        logger.exception("Error fetching report %s: %s", ticket_id, e)
        return None

def get_report_by_ticket_id(ticket_id: str) -> Dict[str, Any]:
    """
    Fetch a report document by ticket_id (stored as _id).
    Returns the raw document (with _id as string) or None.
    """
    doc = reports_collection.find_one({"_id": ticket_id})
    if not doc:
        return None
    # convert _id to string for safe JSON serialization
    doc["_id"] = str(doc["_id"])
    return doc


def list_reports(
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None,
    sort: Optional[List[Tuple[str, int]]] = None,
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    List reports with optional pagination and basic filters.

    Args:
      skip: number of documents to skip
      limit: maximum number of documents returned
      filters: simple Mongo-style filter dict (e.g., {"platform": "iOS", "project_name": "Safeway"})
      sort: list of (field, direction) pairs, e.g. [("created_at", -1)]

    Returns:
      (total_count, [normalized_docs...])
    """
    filters = filters or {}
    try:
        total = reports_collection.count_documents(filters)
        cursor = reports_collection.find(filters, {"markdown_report": 0}).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        docs = [_normalize_doc(d) for d in cursor]
        return total, docs
    except Exception as e:
        logger.exception("Error listing reports: %s", e)
        return 0, []


def save_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upsert (insert or update) a report using `ticket_id` as the key.
    Ensures consistent created_at / updated_at handling.
    Returns dict: {ticket_id, created(bool), created_at(str), updated_at(str)}.
    """

    if "ticket_id" not in report_data:
        raise ValueError("report_data must contain 'ticket_id'")

    ticket_id = report_data["ticket_id"]
    now = datetime.utcnow()

    # Fetch existing document by _id (we store _id = ticket_id)
    existing = reports_collection.find_one({"_id": ticket_id})
    created_at = existing.get("created_at", now) if existing else now

    # Always set _id, ensure timestamps exist
    report_data["_id"] = ticket_id
    report_data["ticket_id"] = ticket_id
    report_data["updated_at"] = now
    report_data["created_at"] = created_at

    # ❌ DO NOT include created_at in $set to avoid conflict with $setOnInsert
    set_data = {k: v for k, v in report_data.items() if k != "created_at"}

    try:
        result: UpdateResult = reports_collection.update_one(
            {"_id": ticket_id},
            {"$set": set_data, "$setOnInsert": {"created_at": created_at}},
            upsert=True,
        )

        created = result.upserted_id is not None

        logger.debug(
            "save_report: %s — created=%s matched=%s modified=%s",
            ticket_id, created, result.matched_count, result.modified_count
        )

        return {
            "ticket_id": ticket_id,
            "created": created,
            "created_at": created_at.isoformat(),
            "updated_at": now.isoformat()
        }

    except Exception as e:
        logger.exception("Failed to save report %s: %s", ticket_id, e)
        raise


def update_report(ticket_id: str, update_fields: Dict[str, Any]) -> bool:
    """Update an existing report and return success status."""
    result = reports_collection.update_one({"_id": ticket_id}, {"$set": update_fields})
    # consider the update successful if a document matched (even if no fields changed)
    return result.matched_count > 0



def delete_report(ticket_id: str) -> bool:
    """
    Delete a report by ticket_id. Returns True if a document was deleted.
    """
    try:
        result: DeleteResult = reports_collection.delete_one({"_id": ticket_id})
        logger.debug("delete_report: deleted_count=%s", result.deleted_count)
        return result.deleted_count > 0
    except Exception as e:
        logger.exception("Error deleting report %s: %s", ticket_id, e)
        return False


# Convenience extractors for checklist/criteria
def get_developer_checklist(ticket_id: str) -> List[Dict[str, Any]]:
    """
    Return the developer_checklist list from json_report or empty list.
    """
    doc = reports_collection.find_one({"_id": ticket_id}, {"json_report": 1})
    if not doc:
        return []
    return doc.get("json_report", {}).get("developer_checklist", []) or []


def get_acceptance_criteria(ticket_id: str) -> List[Any]:
    """
    Return the acceptance_criteria list from json_report or empty list.
    """
    doc = reports_collection.find_one({"_id": ticket_id}, {"json_report": 1})
    if not doc:
        return []
    return doc.get("json_report", {}).get("acceptance_criteria", []) or []
