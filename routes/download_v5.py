# app/routes/download_v5.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from services.db_service import get_report_by_id
from services.pdf_service import generate_pdf_from_markdown
from services.markdown_service import markdown_bytes_io, default_md_filename
import io

router = APIRouter(prefix="/v5", tags=["Download V5"])

@router.get("/download/{id}")
def download_report(id: str, format: str = Query("md", regex="^(md|pdf)$")):
    doc = get_report_by_id(id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")

    markdown_content = doc.get("markdown_report", "") or ""
    title = doc.get("summary") or id
    filename_base = default_md_filename(id, title)

    if format == "md":
        stream = markdown_bytes_io(markdown_content)
        return StreamingResponse(stream, media_type="text/markdown",
                                 headers={"Content-Disposition": f"attachment; filename={filename_base}"})

    # pdf
    try:
        buffer = generate_pdf_from_markdown(markdown_content, title=title)
        pdf_filename = filename_base.replace(".md", ".pdf")
        return StreamingResponse(buffer, media_type="application/pdf",
                                 headers={"Content-Disposition": f"attachment; filename={pdf_filename}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")
