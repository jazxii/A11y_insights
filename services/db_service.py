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


def save_report(report_data: Dict[str, Any]) -> str:
    """
    Upsert a report using report_data["ticket_id"] as the key (stored into _id).
    Returns the ticket_id (which is used as the primary key).
    """
    if "ticket_id" not in report_data:
        raise ValueError("report_data must contain 'ticket_id'")

    ticket_id = report_data["ticket_id"]
    # ensure timestamps
    now = datetime.utcnow()
    report_data["_id"] = ticket_id
    report_data["updated_at"] = now

    # Avoid storing duplicate ticket_id key inside the document if you prefer
    # but keeping ticket_id field is useful for queries; keep it.
    try:
        result: UpdateResult = reports_collection.update_one(
            {"_id": ticket_id},
            {
                "$set": report_data,
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        logger.debug("save_report upsert result: matched=%s modified=%s upserted_id=%s",
                     result.matched_count, result.modified_count, getattr(result, "upserted_id", None))
        return ticket_id
    except Exception as e:
        logger.exception("Failed to save report %s: %s", ticket_id, e)
        raise


def update_report(ticket_id: str, update_fields: Dict[str, Any]) -> bool:
    result = reports_collection.update_one(
        {"ticket_id": ticket_id},
        {"$set": update_fields}
    )
    return result.modified_count > 0



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
