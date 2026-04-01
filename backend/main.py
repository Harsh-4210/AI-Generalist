from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

from pdf_extractor import extract_pdf_content_from_bytes
from ai_processor import call_gemini_for_ddr
from pdf_generator import generate_ddr_pdf

app = FastAPI(title="DDR Report Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "DDR Report Generator API is running", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/generate-ddr")
async def generate_ddr(
    inspection_report: UploadFile = File(..., description="Inspection Report PDF"),
    thermal_report: UploadFile = File(..., description="Thermal Images Report PDF"),
):
    """
    Accepts two PDFs and returns a structured DDR as a downloadable PDF.
    """
    # Validate file types
    for f in [inspection_report, thermal_report]:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"{f.filename} must be a PDF file")

    try:
        # Read both files
        insp_bytes = await inspection_report.read()
        therm_bytes = await thermal_report.read()

        if len(insp_bytes) < 100:
            raise HTTPException(status_code=400, detail="Inspection report PDF appears to be empty")
        if len(therm_bytes) < 100:
            raise HTTPException(status_code=400, detail="Thermal report PDF appears to be empty")

        # Extract content
        inspection_data = extract_pdf_content_from_bytes(insp_bytes)
        thermal_data = extract_pdf_content_from_bytes(therm_bytes)

        if "[ERROR" in inspection_data.get("text", ""):
            raise HTTPException(status_code=422, detail="Could not extract content from Inspection Report")

        # Call Gemini API for AI analysis
        ai_result = call_gemini_for_ddr(inspection_data, thermal_data)

        if not ai_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"AI processing failed: {ai_result.get('error', 'Unknown error')}"
            )

        ddr_data = ai_result["data"]

        # Extract metadata hints from inspection text
        insp_text = inspection_data.get("text", "")
        property_name = "As Per Inspection Documents"
        inspector_name = "UrbanRoof Technical Team"

        for line in insp_text.split("\n"):
            if "Inspected By" in line or "Prepared By" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    inspector_name = parts[1].strip()[:50]
            if "Address" in line or "Flat No" in line or "Property" in line:
                if len(line) > 10 and len(line) < 120:
                    property_name = line.replace("Address:", "").replace("Property:", "").strip()[:80]

        report_meta = {
            "property": property_name,
            "inspector": inspector_name,
        }

        # Generate PDF
        pdf_bytes = generate_ddr_pdf(
            ddr_data=ddr_data,
            inspection_images=inspection_data.get("images", []),
            thermal_images=thermal_data.get("images", []),
            report_meta=report_meta
        )

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=DDR_Report.pdf",
                "Content-Length": str(len(pdf_bytes))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/preview-ddr")
async def preview_ddr(
    inspection_report: UploadFile = File(...),
    thermal_report: UploadFile = File(...),
):
    """Returns the DDR as JSON for preview (without PDF generation)."""
    insp_bytes = await inspection_report.read()
    therm_bytes = await thermal_report.read()

    inspection_data = extract_pdf_content_from_bytes(insp_bytes)
    thermal_data = extract_pdf_content_from_bytes(therm_bytes)

    ai_result = call_gemini_for_ddr(inspection_data, thermal_data)

    if not ai_result.get("success"):
        raise HTTPException(status_code=500, detail=ai_result.get("error"))

    return JSONResponse(content={
        "ddr": ai_result["data"],
        "stats": {
            "inspection_pages": inspection_data.get("page_count", 0),
            "inspection_images": len(inspection_data.get("images", [])),
            "thermal_pages": thermal_data.get("page_count", 0),
            "thermal_images": len(thermal_data.get("images", [])),
        }
    })
