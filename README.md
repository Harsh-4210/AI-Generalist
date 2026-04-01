# 🏗️ AI-Powered DDR Report Generator

> Automated pipeline that converts building Inspection + Thermal PDF reports into a professional Detailed Diagnostic Report (DDR) using AI

---

## 📌 What It Does

This system accepts **two PDF uploads** — a site Inspection Report and a Thermal Imaging Report — and automatically:

1. **Extracts** all text and images from both documents using PyMuPDF
2. **Analyzes** the combined data using Google Gemini 2.5 Flash (multimodal AI)
3. **Generates** a structured, client-ready DDR as a downloadable PDF with embedded images

The output is a professional diagnostic report — complete with area-wise observations, thermal temperature readings, severity assessment, and images placed under their relevant sections.

---

## 🏗️ Architecture & Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  React UI   │────▶│  FastAPI      │────▶│  Gemini 2.5     │────▶│  ReportLab   │
│  (Upload)   │     │  (Orchestrate)│     │  Flash (AI)     │     │  (PDF Build) │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
       │                   │                      │                      │
   Drag & Drop       PyMuPDF Extract      Merge + Deduplicate      Professional
   2 PDF files       Text + Images        Structured JSON          DDR PDF Output
```

---

## 📁 Project Structure

```
AI_GENERALIST/
├── backend/
│   ├── main.py              # FastAPI app — /generate-ddr and /preview-ddr endpoints
│   ├── pdf_extractor.py     # PyMuPDF: extract text + images from PDF bytes
│   ├── ai_processor.py      # Gemini API: multimodal prompt → structured DDR JSON
│   ├── pdf_generator.py     # ReportLab: JSON + images → professional DDR PDF
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # GEMINI_API_KEY (user must provide)
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # React UI with drag-and-drop upload
│   │   ├── index.css        # Dark theme styling with glassmorphism
│   │   └── main.jsx         # React entry point
│   └── index.html           # HTML shell with Inter font
├── DOCS/                    # Input documents and sample output
│   ├── Sample Report.pdf    # Inspection report (input)
│   ├── Thermal Images.pdf   # Thermal imaging report (input)
│   └── DDR_Sample_Report.pdf # Reference DDR (generated output)
├── .gitignore
└── README.md
```

---

## ⚙️ Setup & Run

### Prerequisites
- Python 3.10+
- Node.js 18+
- Free Gemini API Key → [Get one here](https://aistudio.google.com/app/apikey)

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in `backend/`:
```env
GEMINI_API_KEY=your_api_key_here
```

Start the server:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API status check |
| `GET` | `/health` | Health check |
| `POST` | `/generate-ddr` | Upload 2 PDFs → Download DDR PDF |
| `POST` | `/preview-ddr` | Upload 2 PDFs → Get DDR as JSON |

---

## 📄 DDR Output Structure (7 Sections)

| # | Section | Description |
|---|---------|-------------|
| 1 | **Property Issue Summary** | 2–3 sentence overview of all issues found |
| 2 | **Area-wise Observations** | Per-room findings with embedded site photos + thermal images |
| 3 | **Probable Root Cause** | Detailed explanation of why issues exist |
| 4 | **Severity Assessment** | High / Medium / Low with color-coded badge + reasoning |
| 5 | **Recommended Actions** | Numbered treatment steps |
| 6 | **Additional Notes** | Extra context, warnings |
| 7 | **Missing or Unclear Info** | Explicit "Not Available" flags for missing data |

---

## 🧠 How the AI Works

### Extraction (PyMuPDF)
- Extracts all text page-by-page with `--- Page X ---` markers
- Extracts every embedded image with metadata (page number, size, format)
- Filters out tiny icons (< 2KB) to keep only meaningful photos

### AI Analysis (Gemini 2.5 Flash)
- Sends up to **30,000 characters** of text from each document
- Samples **8 thermal + 5 inspection images** evenly across pages for visual context
- Uses a **one-shot example** in the prompt to enforce rich, descriptive output format
- Forces `response_mime_type: "application/json"` for guaranteed structured output
- Handles safety-block edge cases gracefully

### PDF Generation (ReportLab)
- Professional branded cover page with property metadata
- Severity badge with color coding (🔴 High / 🟠 Medium / 🟢 Low)
- Images placed **directly under their matching area observation** — not appended at end
- Page-proximity matching with **deduplication** to prevent the same image appearing twice
- Fallback message `"⚠ Image Not Available"` when expected images are missing

---

## 📋 Design Decisions

| Rule | How It's Handled |
|------|------------------|
| Do NOT invent facts | Prompt explicitly prohibits fabrication |
| Missing info → "Not Available" | Section 7 + prompt rule enforces this |
| Conflicting info → mention conflict | Prompt rule: `"Conflict: [describe both versions]"` |
| Simple, client-friendly language | Prompt requests professional but accessible phrasing |
| Generalizes to similar reports | No hardcoded area names; works on any inspection + thermal PDF pair |
| Images under observations | Page-proximity matching places images contextually |
| Missing images flagged | `"⚠ Image Not Available"` shown when refs can't be resolved |

---

## ⚠️ Limitations

- Image matching relies on AI-provided page numbers — occasionally off by 1–2 pages
- Very large PDFs (50+ pages of text) may hit Gemini free-tier token limits
- Gemini free tier has rate limits (15 RPM) — production use would need a paid plan
- Scanned/handwritten PDFs without embedded text won't extract properly (no OCR layer)

## 🚀 Future Improvements

- Add **OCR fallback** (Tesseract) for scanned PDFs
- Support **batch processing** of multiple flats in a single run
- Add **inline thermal overlay analysis** comparing before/after treatment
- Implement **user authentication** and report history dashboard
- Deploy with **WebSocket progress streaming** for real-time status

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | React + Vite + Tailwind CSS | Upload UI with drag-and-drop |
| **Backend** | FastAPI (Python) | REST API orchestration |
| **PDF Extraction** | PyMuPDF (fitz) | Text + image extraction from PDFs |
| **AI Engine** | Google Gemini 2.5 Flash | Multimodal analysis + JSON structuring |
| **PDF Generation** | ReportLab Platypus | Professional PDF layout with images |
| **Image Processing** | Pillow | Resize + format conversion for embedding |

---

*Built by Harsh Jain*
