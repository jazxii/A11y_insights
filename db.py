import os
import logging
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
from typing import Any, Dict
from fastapi.encoders import jsonable_encoder



# Load environment variables
load_dotenv()

logger = logging.getLogger("accessibility_insights.db")
logging.basicConfig(level=logging.INFO)

# Mongo configuration
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "a11y_insights")
REPORTS_COLLECTION = os.getenv("REPORTS_COLLECTION", "ai_reports")

client = None
db = None
collection = None

# Attempt to connect to MongoDB Atlas securely
try:
    if not MONGO_URI:
        raise ValueError("MONGO_URI not found in environment variables.")

    # ✅ Correct: create client once with certifi CA
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=8000
    )

    # ✅ Select DB and collection
    db = client[DATABASE_NAME]
    collection = db[REPORTS_COLLECTION]

    # ✅ Test connection
    client.admin.command("ping")
    logger.info(f"✅ Connected to MongoDB Atlas database '{DATABASE_NAME}' successfully.")

except Exception as e:
    logger.error(f"⚠️ Failed to connect to MongoDB: {e}")
    client = None
    db = None
    collection = None


def save_report_to_db(report_data: dict) -> str:
    """
    Saves a full accessibility report to MongoDB.
    Returns the inserted ID (or error message if failed).
    """
    if collection is None:
        logger.warning("⚠️ MongoDB connection not available. Skipping database save.")
        return "DB not connected"

    try:
        report_data["created_at"] = report_data.get("created_at", datetime.utcnow().isoformat() + "Z")
        result = collection.insert_one(report_data)
        logger.info(f"🗂️ Report saved to MongoDB with ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"❌ Error saving report to MongoDB: {e}")
        return "Insert failed"
    
def save_v3json_to_db(v3json: Dict[str, Any]) -> str:
    """
    Saves a V3JSON accessibility report document to MongoDB.
    Ensures created_at is present. Returns inserted_id or error string.
    """
    if collection is None:
        logger.warning("⚠️ MongoDB connection not available. Skipping V3JSON save.")
        return "DB not connected"

    try:
        # ensure metadata and created_at exist
        metadata = v3json.get("metadata", {})
        if "generated_at" not in metadata:
            metadata["generated_at"] = datetime.utcnow().isoformat() + "Z"
        v3json["metadata"] = metadata
        v3json["_saved_at"] = datetime.utcnow().isoformat() + "Z"

        # Convert Pydantic/other special types to plain Python types
        serializable = jsonable_encoder(v3json)

        # Now insert the converted dict
        result = collection.insert_one(serializable)
        logger.info(f"🗂️ V3JSON saved to MongoDB with ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"❌ Error saving V3JSON to MongoDB: {e}")

        return "Insert failed"
