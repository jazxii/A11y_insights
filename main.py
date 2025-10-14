# main.py (V2)
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.services.save_markdown import save_markdown_report
from .schemas import UserStoryIn, ReportOut, A11yDeepReportOut, DetectedComponent,A11yV3JSONOut
from .services.parser import extract_components
from .services.ai_client import analyze_with_ai, analyze_with_ai_v3, analyze_with_ai_v3json, analyze_with_ai_v4
from .services.report_generator import build_report, build_deep_report
from .db import save_report_to_db, save_v3json_to_db
from .config import settings
import logging
import traceback

app = FastAPI(title='Accessibility Early Insights API')

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

logger = logging.getLogger("accessibility_insights")
logging.basicConfig(level=logging.INFO)

@app.get("/")
async def root():
    return {"message": "A11y Insights API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)



@app.post("/v1/analyze", response_model=ReportOut)
async def analyze_v1(user_story: UserStoryIn):
    """
    Backward-compatible Analyze endpoint (v1).
    """
    try:
        ai_result = analyze_with_ai(user_story.dict())
        # attempt to reuse existing build_report flow
        # Prefer parsed_json if it matches the older structure
        components = []
        ai_components_raw = ai_result.get("parsed_json", {}).get("components") if isinstance(ai_result.get("parsed_json"), dict) else None
        if ai_components_raw:
            for item in ai_components_raw:
                if isinstance(item, str):
                    components.append(DetectedComponent(name=item, type="unknown", hint="Detected by AI"))
                elif isinstance(item, dict):
                    name = item.get("name") or item.get("component")
                    typ = item.get("type") or "unknown"
                    hint = item.get("hint") or "Detected by AI"
                    components.append(DetectedComponent(name=name, type=typ, hint=hint))
        else:
            components = extract_components(user_story.description)

        report = build_report(getattr(user_story, "story_id", None), user_story.title, user_story.description, components, ai_result.get("parsed_json") or ai_result)
        try:
            save_report(report.dict() if hasattr(report, "dict") else report)
        except Exception:
            logger.exception("Saving report failed - continuing without failing request")
        return report
    except Exception as exc:
        logger.exception("Unhandled exception in /v1/analyze")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "error": str(exc), "traceback": traceback.format_exc()})

@app.post("/v2/analyze", response_model=A11yDeepReportOut)
async def analyze_v2(user_story: UserStoryIn):
    """
    A11y Insights V2 - Deep Ticket Analysis Mode (Markdown-first)
    """
    try:
        ai_result = analyze_with_ai(user_story.dict())

        # Determine components: prefer AI-detected, else parser
        components = []
        parsed = ai_result.get("parsed_json") if isinstance(ai_result.get("parsed_json"), dict) else None
        ai_components_raw = None
        if parsed:
            ai_components_raw = parsed.get("components")
        else:
            # sometimes AI returns components key at top-level in sections: try ai_result dict
            ai_components_raw = ai_result.get("parsed_json", {}).get("components") if isinstance(ai_result.get("parsed_json"), dict) else None

        if ai_components_raw:
            for item in ai_components_raw:
                if isinstance(item, str):
                    components.append(DetectedComponent(name=item, type="unknown", hint="Detected by AI"))
                elif isinstance(item, dict):
                    name = item.get("name") or item.get("component")
                    typ = item.get("type") or "unknown"
                    hint = item.get("hint") or "Detected by AI"
                    components.append(DetectedComponent(name=name, type=typ, hint=hint))
        else:
            components = extract_components(user_story.description)

        report = build_deep_report(getattr(user_story, "story_id", None), user_story.title, user_story.description, components, ai_result, meta={"source": ai_result.get("source")})
        try:
            save_report(report.dict() if hasattr(report, "dict") else report)
        except Exception:
            logger.exception("Saving report failed - continuing without failing request")
        return report
    except Exception as exc:
        logger.exception("Unhandled exception in /v2/analyze")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "error": str(exc), "traceback": traceback.format_exc()})

# @app.post("/v3/analyze")
# async def analyze_v3(user_story: UserStoryIn):
#     ai_result = analyze_with_ai_v3(user_story.dict())
#     # For V3, we don’t parse — we just return Markdown and meta
#     return {
#         "title": user_story.title,
#         "story_id": getattr(user_story, "story_id", None),
#         "raw_markdown": ai_result.get("markdown"),
#         "source": ai_result.get("source"),
#         "created_at": datetime.utcnow().isoformat() + "Z"
#     }

@app.post("/v3/analyze")
async def analyze_v3(user_story: UserStoryIn):
    """
    Runs Accessibility Insights V3 (Markdown report generation),
    saves the .md file locally, and stores metadata + raw markdown in MongoDB.
    """
    try:
        # Step 1: Run AI analysis
        ai_result = analyze_with_ai_v3(user_story.dict())

        # Support either key returned by OpenAI
        raw_md = ai_result.get("raw_markdown") or ai_result.get("markdown")
        if not raw_md:
            raise HTTPException(status_code=500, detail="AI response missing markdown content.")

        # Step 2: Build a clean structured report object
        report = {
            "story_id": ai_result.get("story_id") or getattr(user_story, "story_id", None),
            "title": ai_result.get("title") or user_story.title,
            "raw_markdown": raw_md,
            "created_at": ai_result.get("created_at", datetime.utcnow().isoformat() + "Z"),
            "source": ai_result.get("source", "openai")
        }

        # Step 3: Save Markdown to /output folder
        report["file_path"] = save_markdown_report(report)

        # Step 4: Save complete record to MongoDB
        mongo_id = save_report_to_db(report)

        # Step 5: Return clean response
        return {
            "message": "Accessibility report generated, saved, and stored successfully.",
            "mongo_id": mongo_id,
            "file_path": report["file_path"],
            "title": report["title"],
            "story_id": report["story_id"],
            "created_at": report["created_at"],
            "source": report["source"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate and save markdown report: {e}")

# @app.post("/v3json/analyze", response_model=A11yV3JSONOut)
# async def analyze_v3json(user_story: UserStoryIn):
#     ai_result = analyze_with_ai_v3json(user_story.dict())
#     parsed = ai_result.get("parsed_json", {})

#     # Attach metadata if missing
#     if "metadata" not in parsed:
#         parsed["metadata"] = {
#             "generated_at": datetime.utcnow().isoformat() + "Z",
#             "model_version": settings.OPENAI_MODEL,
#             "confidence_score": 0.9,
#         }

#     return parsed

@app.post("/v3json/analyze", response_model=A11yV3JSONOut)
async def analyze_v3json(user_story: UserStoryIn):
    """
    Generate V3JSON from AI, validate and save to MongoDB, return DB id + saved object.
    """
    try:
        ai_result = analyze_with_ai_v3json(user_story.dict())
        parsed = ai_result.get("parsed_json") or {}

        if not parsed:
            # AI returned nothing useful
            raise HTTPException(status_code=500, detail="AI returned no parsed_json.")

        # Ensure metadata present
        metadata = parsed.get("metadata", {})
        if "generated_at" not in metadata:
            metadata["generated_at"] = datetime.utcnow().isoformat() + "Z"
        if "model_version" not in metadata:
            metadata["model_version"] = ai_result.get("model_version", "gpt-5")
        if "confidence_score" not in metadata:
            # optional: if AI produced confidence, keep it; else set null/0.0
            metadata["confidence_score"] = metadata.get("confidence_score", 0.0)
        parsed["metadata"] = metadata

        # Validate and coerce the parsed JSON through Pydantic (this will raise if structure is wrong)
        try:
            validated = A11yV3JSONOut.model_validate(parsed)  # pydantic v2 API
            # convert back to primitive dict for DB insertion
            validated_dict = validated.model_dump()
        except ValidationError as ve:
            # If validation fails, include the raw parsed JSON for debugging but do not crash
            logger.warning("V3JSON validation failed — returning raw parsed JSON and still saving it for inspection.")
            # Option: attempt to save raw parsed payload anyway for debugging/auditing
            validated_dict = parsed

        # Save to MongoDB
        mongo_id = save_v3json_to_db(validated_dict)

        # Return saved object reference and metadata (do NOT return full raw_markdown if huge)
        response = {
            "message": "V3JSON generated and saved.",
            "mongo_id": mongo_id,
            "metadata": validated_dict.get("metadata", {}),
            "source": ai_result.get("source", "openai")
        }

        return validated_dict  # because response_model=A11yV3JSONOut will serialize validated_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate/save V3JSON")
        raise HTTPException(status_code=500, detail=f"Failed to generate/save V3JSON: {e}")

@app.post("/v4/analyze")
async def analyze_v4(user_story: UserStoryIn):
    """Generate V4 Markdown report, save as .md and store metadata in MongoDB."""
    try:
        ai_result = analyze_with_ai_v4(user_story.dict())
        raw_md = ai_result.get("markdown")
        if not raw_md:
            raise HTTPException(status_code=500, detail="AI response missing markdown content for V4.")

        report = {
            "story_id": ai_result.get("story_id") or getattr(user_story, "story_id", None),
            "title": ai_result.get("title") or user_story.title,
            "raw_markdown": raw_md,
            "created_at": ai_result.get("created_at") or datetime.utcnow().isoformat() + "Z",
            "source": ai_result.get("source", "openai"),
        }

        report["file_path"] = save_markdown_report(report)
        mongo_id = save_report_to_db(report)

        return {
            "message": "V4 Accessibility report generated, saved, and stored.",
            "mongo_id": mongo_id,
            "file_path": report["file_path"],
            "title": report["title"],
            "story_id": report["story_id"],
            "created_at": report["created_at"],
            "source": report["source"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate/save V4 markdown report")
        raise HTTPException(status_code=500, detail=f"Failed to generate and save V4 markdown report: {e}")


@app.get("/health")
async def health():
    return {"status": "ok", "openai_model": settings.OPENAI_MODEL}

# global exception handler
@app.exception_handler(Exception)
async def all_exceptions_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for request %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
            "traceback": traceback.format_exc()
        },
    )
    
    
