import google.generativeai as genai
import json
import os
from typing import Optional

def _sample_images(images: list, max_count: int = 8) -> list:
    """Sample images evenly across all pages for better coverage."""
    if len(images) <= max_count:
        return images
    
    # Get unique pages and sample evenly
    pages = sorted(set(img["page"] for img in images))
    if len(pages) <= max_count:
        # Pick one image per page
        sampled = []
        seen_pages = set()
        for img in images:
            if img["page"] not in seen_pages:
                sampled.append(img)
                seen_pages.add(img["page"])
            if len(sampled) >= max_count:
                break
        return sampled
    
    # More pages than max_count — sample evenly across page range
    step = max(1, len(pages) // max_count)
    selected_pages = pages[::step][:max_count]
    
    sampled = []
    for pg in selected_pages:
        for img in images:
            if img["page"] == pg:
                sampled.append(img)
                break
    return sampled


def call_gemini_for_ddr(inspection_data: dict, thermal_data: dict) -> dict:
    """
    Send extracted inspection and thermal data to Gemini API.
    Returns a structured DDR dict with 7 sections.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"success": False, "error": "GEMINI_API_KEY not found in environment variables. Please check your .env file."}

    genai.configure(api_key=api_key)

    inspection_text = inspection_data.get("text", "Not Available")
    thermal_text = thermal_data.get("text", "Not Available")
    inspection_images = inspection_data.get("images", [])
    thermal_images = thermal_data.get("images", [])

    # Build image page summary for context
    insp_img_pages = sorted(set([img["page"] for img in inspection_images]))
    therm_img_pages = sorted(set([img["page"] for img in thermal_images]))

    system_prompt = """You are an expert building diagnostic analyst working for UrbanRoof Private Limited.
You analyze site inspection data and thermal imaging data to produce professional Detailed Diagnostic Reports (DDR).
You always respond ONLY with valid JSON — no markdown, no preamble, no explanation outside the JSON."""

    # Send much more text to Gemini (supports 1M tokens) for better accuracy
    user_prompt = f"""You have been provided with raw data from two documents:

1. INSPECTION REPORT / SITE REPORT (text extracted from the document)
2. THERMAL IMAGING REPORT (text extracted from the thermal document)

=== INSPECTION REPORT TEXT ===
{inspection_text[:30000]}

=== THERMAL REPORT TEXT ===
{thermal_text[:30000]}

=== IMAGE SUMMARY ===
- Inspection Report contains {len(inspection_images)} images (on pages: {insp_img_pages})
- Thermal Report contains {len(thermal_images)} thermal images (on pages: {therm_img_pages})

STRICT RULES:
1. DO NOT invent any facts not present in the documents
2. If information is missing → write exactly: "Not Available"
3. If two documents conflict → write: "Conflict: [describe both versions]"
4. Remove duplicate observations — mention each issue only ONCE
5. Combine the room/area and specific location in the area name (e.g. "Hall — Skirting Level", "Master Bedroom — Window Wall").
6. Write highly descriptive observations merging both visible issues and thermal findings (e.g., coldspots, temperatures). Don't just say "Observed dampness"; be professional and thorough.
7. severity level must be one of: "High", "Medium", "Low"
8. CRITICAL: For image_refs, you MUST provide the EXACT integer page number ('page') where the photo is located in the document. 
   - Look for the "--- Page X ---" header directly above the photo's caption/mention in the text.
   - Do NOT use the page number where the text observation is written; use the page where the image itself is located.
   - Pick at most 1 or 2 specific photos per area. Avoid grouping like "Photos 1-7". Pick one specific page.
   - 'source' must be exactly 'inspection' or 'thermal'.

Respond ONLY with this exact JSON structure (no other text). Use this EXACT style of rich, descriptive phrasing and singular page numbers:
{{
  "property_issue_summary": "2-3 sentence overview of all issues found, summarizing the root causes and affected areas.",
  "area_wise_observations": [
    {{
      "area": "Master Bedroom — Skirting Level",
      "observations": [
        "Dampness and early efflorescence observed at skirting level. Thermal imaging confirmed a coldspot at 20.5°C indicating sustained moisture beneath the substrate."
      ],
      "image_refs": [
        {{"source": "inspection", "page": 12, "description": "Master bedroom skirting dampness"}},
        {{"source": "thermal", "page": 4, "description": "MB skirting – coldspot 20.5°C"}}
      ]
    }}
  ],
  "probable_root_cause": "Detailed explanation of why these issues exist",
  "severity_assessment": {{
    "level": "High",
    "reasoning": "Why this severity level was assigned"
  }},
  "recommended_actions": [
    "Action 1 with specific treatment details",
    "Action 2"
  ],
  "additional_notes": "Any extra context",
  "missing_or_unclear": [
    "Item that was unclear"
  ]
}}"""

    # Gemini expects a list of parts, which can be text strings or inline image dictionaries
    content = [system_prompt, user_prompt]

    # Sample images evenly across pages for better multimodal coverage
    sampled_thermal = _sample_images(thermal_images, max_count=8)
    sampled_inspection = _sample_images(inspection_images, max_count=5)

    for img in sampled_thermal:
        mime_type = f"image/{img['ext']}" if img['ext'] in ['png', 'jpeg', 'webp'] else "image/jpeg"
        try:
            content.append({
                "mime_type": mime_type,
                "data": img["bytes"]
            })
        except Exception:
            pass

    for img in sampled_inspection:
        mime_type = f"image/{img['ext']}" if img['ext'] in ['png', 'jpeg', 'webp'] else "image/jpeg"
        try:
            content.append({
                "mime_type": mime_type,
                "data": img["bytes"]
            })
        except Exception:
            pass

    try:
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(content)

        # Handle safety blocks — Gemini may return an empty response
        if not response.candidates or not response.candidates[0].content.parts:
            return {"success": False, "error": "Gemini returned an empty response (possible safety filter). Try again or check your input documents."}

        raw_text = response.text.strip()
        ddr_data = json.loads(raw_text)
        return {"success": True, "data": ddr_data}

    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parse error: {e}", "raw": raw_text if 'raw_text' in locals() else ""}
    except Exception as e:
        return {"success": False, "error": str(e)}
