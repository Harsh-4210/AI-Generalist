import { useState, useCallback } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/* ── Drop Zone Component ─────────────────────────────────────────────── */
function DropZone({ label, subtitle, file, onFile, accept = ".pdf" }) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && f.type === "application/pdf") onFile(f);
  }, [onFile]);

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => document.getElementById(`file-${label}`).click()}
      style={{
        position: "relative",
        border: file
          ? "1.5px solid rgba(48, 209, 88, 0.4)"
          : dragging
          ? "1.5px solid var(--gold)"
          : "1.5px dashed rgba(255,255,255,0.12)",
        borderRadius: "16px",
        padding: "28px 20px",
        textAlign: "center",
        cursor: "pointer",
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        background: file
          ? "rgba(48, 209, 88, 0.06)"
          : dragging
          ? "rgba(212, 168, 67, 0.06)"
          : "var(--glass-bg)",
        backdropFilter: "blur(12px)",
      }}
      onMouseEnter={(e) => {
        if (!file) e.currentTarget.style.borderColor = "rgba(212, 168, 67, 0.5)";
      }}
      onMouseLeave={(e) => {
        if (!file) e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)";
      }}
    >
      <input
        id={`file-${label}`}
        type="file"
        accept={accept}
        style={{ display: "none" }}
        onChange={(e) => e.target.files[0] && onFile(e.target.files[0])}
      />

      {/* Icon */}
      <div style={{
        width: 48, height: 48, borderRadius: 12, margin: "0 auto 12px",
        display: "flex", alignItems: "center", justifyContent: "center",
        background: file ? "rgba(48, 209, 88, 0.12)" : "rgba(255,255,255,0.06)",
        fontSize: 22,
        transition: "all 0.3s ease",
      }}>
        {file ? "✓" : "↑"}
      </div>

      <div style={{
        fontWeight: 600, fontSize: 14, color: "var(--text-primary)", marginBottom: 4,
      }}>
        {label}
      </div>

      <div style={{
        fontSize: 12, color: "var(--text-muted)", lineHeight: 1.5,
      }}>
        {subtitle}
      </div>

      {file && (
        <div style={{
          marginTop: 12, padding: "6px 14px", borderRadius: 8,
          background: "rgba(48, 209, 88, 0.1)", display: "inline-flex",
          alignItems: "center", gap: 6,
          fontSize: 12, fontWeight: 500, color: "var(--success)",
        }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--success)" }} />
          {file.name} ({formatSize(file.size)})
        </div>
      )}
    </div>
  );
}

/* ── Processing Steps ─────────────────────────────────────────────────── */
const STEPS = [
  { label: "Extracting text from Inspection Report", icon: "📄" },
  { label: "Extracting thermal images & data", icon: "🌡️" },
  { label: "Sending data to Gemini AI engine", icon: "🔗" },
  { label: "Analysing moisture patterns & thermal anomalies", icon: "🔬" },
  { label: "Generating structured DDR observations", icon: "🧠" },
  { label: "Embedding images into report sections", icon: "🖼️" },
  { label: "Building professional PDF document", icon: "📋" },
];

/* ── Main App ─────────────────────────────────────────────────────────── */
export default function App() {
  const [inspFile, setInspFile] = useState(null);
  const [thermFile, setThermFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [error, setError] = useState(null);

  const canGenerate = inspFile && thermFile && !loading;

  const generate = async () => {
    if (!canGenerate) return;
    setLoading(true);
    setError(null);
    setPdfUrl(null);
    setStep(0);

    const stepInterval = setInterval(() => {
      setStep((s) => (s < STEPS.length - 1 ? s + 1 : s));
    }, 2800);

    try {
      const form = new FormData();
      form.append("inspection_report", inspFile);
      form.append("thermal_report", thermFile);

      const res = await fetch(`${API_URL}/generate-ddr`, {
        method: "POST",
        body: form,
      });

      clearInterval(stepInterval);

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Generation failed");
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      setStep(STEPS.length - 1);
    } catch (e) {
      clearInterval(stepInterval);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const resetAll = () => {
    setInspFile(null);
    setThermFile(null);
    setPdfUrl(null);
    setError(null);
    setStep(0);
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>

      {/* ── Header ────────────────────────────────────────────────────── */}
      <header style={{
        borderBottom: "1px solid var(--glass-border)",
        backdropFilter: "blur(20px)",
        background: "rgba(28, 28, 30, 0.8)",
        position: "sticky", top: 0, zIndex: 50,
      }}>
        <div style={{
          maxWidth: 960, margin: "0 auto",
          padding: "14px 24px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            {/* Logo */}
            <div style={{
              width: 38, height: 38, borderRadius: 10,
              background: "linear-gradient(135deg, var(--gold), var(--gold-dark))",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontWeight: 800, fontSize: 14, color: "var(--charcoal)",
              letterSpacing: "-0.5px",
            }}>
              UR
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 15, letterSpacing: "-0.3px", color: "var(--text-primary)" }}>
                DDR Report Generator
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 400 }}>
                AI-Powered Diagnostics
              </div>
            </div>
          </div>

          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "5px 12px", borderRadius: 20,
            background: "rgba(48, 209, 88, 0.1)", border: "1px solid rgba(48, 209, 88, 0.2)",
            fontSize: 11, fontWeight: 500, color: "var(--success)",
          }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--success)", animation: "pulse-ring 2s ease infinite" }} />
            System Online
          </div>
        </div>
      </header>

      {/* ── Main Content ──────────────────────────────────────────────── */}
      <main style={{ flex: 1, maxWidth: 960, margin: "0 auto", padding: "40px 24px", width: "100%" }}>

        {/* Hero Section */}
        <div className="animate-fade-in-up" style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{
            display: "inline-flex", padding: "5px 14px", borderRadius: 20,
            background: "rgba(212, 168, 67, 0.1)", border: "1px solid rgba(212, 168, 67, 0.2)",
            marginBottom: 16, fontSize: 12, fontWeight: 500, color: "var(--gold-light)",
          }}>
            AI-Powered Building Diagnostics
          </div>
          <h1 style={{
            fontSize: 32, fontWeight: 800, letterSpacing: "-0.8px",
            lineHeight: 1.2, marginBottom: 10,
            background: "linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          }}>
            Generate Detailed<br />Diagnostic Reports
          </h1>
          <p style={{ fontSize: 14, color: "var(--text-muted)", maxWidth: 520, margin: "0 auto", lineHeight: 1.6 }}>
            Upload your inspection and thermal imaging documents. Our AI engine will extract, merge, and produce a structured client-ready PDF.
          </p>
        </div>

        {/* Upload Card */}
        <div className="animate-fade-in-up-delay-1" style={{
          background: "var(--dark-surface)", borderRadius: 20,
          border: "1px solid var(--glass-border)",
          padding: "32px", marginBottom: 24,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8, fontSize: 14,
              background: "rgba(212, 168, 67, 0.12)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>📁</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>Upload Documents</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Both files are required to generate the report</div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
            <DropZone
              label="Inspection Report"
              subtitle="Site observations & issue photographs"
              file={inspFile}
              onFile={setInspFile}
            />
            <DropZone
              label="Thermal Images Report"
              subtitle="Temperature readings & thermal scans"
              file={thermFile}
              onFile={setThermFile}
            />
          </div>

          <button
            onClick={generate}
            disabled={!canGenerate}
            style={{
              width: "100%",
              padding: "14px 24px",
              borderRadius: 12,
              border: "none",
              fontFamily: "Inter, sans-serif",
              fontWeight: 600,
              fontSize: 15,
              letterSpacing: "-0.2px",
              cursor: canGenerate ? "pointer" : "not-allowed",
              transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
              background: canGenerate
                ? "linear-gradient(135deg, var(--gold), var(--gold-dark))"
                : "var(--dark-card)",
              color: canGenerate ? "var(--charcoal)" : "var(--text-muted)",
              boxShadow: canGenerate ? "0 4px 24px rgba(212, 168, 67, 0.25)" : "none",
              transform: "scale(1)",
            }}
            onMouseEnter={(e) => {
              if (canGenerate) {
                e.currentTarget.style.transform = "scale(1.01)";
                e.currentTarget.style.boxShadow = "0 6px 32px rgba(212, 168, 67, 0.35)";
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "scale(1)";
              if (canGenerate) e.currentTarget.style.boxShadow = "0 4px 24px rgba(212, 168, 67, 0.25)";
            }}
          >
            {loading ? (
              <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
                <span style={{ width: 18, height: 18, border: "2.5px solid rgba(28,28,30,0.3)", borderTopColor: "var(--charcoal)", borderRadius: "50%", animation: "spin 0.8s linear infinite", display: "inline-block" }} />
                Generating Report…
              </span>
            ) : (
              "Generate DDR Report →"
            )}
          </button>
        </div>

        {/* ── Loading State ──────────────────────────────────────────── */}
        {loading && (
          <div className="animate-fade-in-up" style={{
            background: "var(--dark-surface)", borderRadius: 20,
            border: "1px solid var(--glass-border)",
            padding: "28px 32px", marginBottom: 24,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8, fontSize: 14,
                background: "rgba(212, 168, 67, 0.12)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>⚙️</div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>Processing Pipeline</div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {STEPS.map((s, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 12,
                  padding: "8px 12px", borderRadius: 10,
                  background: i === step ? "rgba(212, 168, 67, 0.08)" : "transparent",
                  transition: "all 0.3s ease",
                }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 13,
                    background: i < step
                      ? "rgba(48, 209, 88, 0.15)"
                      : i === step
                      ? "rgba(212, 168, 67, 0.15)"
                      : "rgba(255,255,255,0.04)",
                   transition: "all 0.3s ease",
                  }}>
                    {i < step ? "✓" : s.icon}
                  </div>
                  <span style={{
                    fontSize: 13, fontWeight: i === step ? 600 : 400,
                    color: i < step ? "var(--success)" : i === step ? "var(--gold-light)" : "var(--text-muted)",
                    transition: "all 0.3s ease",
                  }}>
                    {s.label}
                  </span>
                </div>
              ))}
            </div>

            {/* Progress bar */}
            <div style={{
              marginTop: 20, height: 3, borderRadius: 2,
              background: "rgba(255,255,255,0.06)", overflow: "hidden",
            }}>
              <div style={{
                height: "100%", borderRadius: 2,
                background: "linear-gradient(90deg, var(--gold), var(--gold-light))",
                width: `${((step + 1) / STEPS.length) * 100}%`,
                transition: "width 0.6s ease",
              }} />
            </div>
          </div>
        )}

        {/* ── Error State ────────────────────────────────────────────── */}
        {error && (
          <div className="animate-fade-in-up" style={{
            background: "rgba(255, 69, 58, 0.08)", borderRadius: 16,
            border: "1px solid rgba(255, 69, 58, 0.2)",
            padding: "20px 24px", marginBottom: 24,
          }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                background: "rgba(255, 69, 58, 0.15)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 14,
              }}>⚠</div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, color: "var(--error)", marginBottom: 4 }}>
                  Generation Failed
                </div>
                <div style={{ fontSize: 13, color: "rgba(255, 69, 58, 0.8)", lineHeight: 1.5 }}>
                  {error}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
                  Ensure your API key is set and both files are valid PDFs
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Success State ──────────────────────────────────────────── */}
        {pdfUrl && (
          <div className="animate-fade-in-up" style={{
            background: "var(--dark-surface)", borderRadius: 20,
            border: "1px solid rgba(48, 209, 88, 0.2)",
            padding: "36px", textAlign: "center", marginBottom: 24,
          }}>
            <div style={{
              width: 56, height: 56, borderRadius: 16, margin: "0 auto 16px",
              background: "rgba(48, 209, 88, 0.12)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 26,
            }}>✓</div>

            <div style={{ fontWeight: 700, fontSize: 20, marginBottom: 6, letterSpacing: "-0.3px" }}>
              Report Generated Successfully
            </div>
            <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 24 }}>
              Your Detailed Diagnostic Report is ready for download
            </div>

            <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
              <a
                href={pdfUrl}
                download="DDR_Report.pdf"
                style={{
                  display: "inline-flex", alignItems: "center", gap: 8,
                  padding: "12px 28px", borderRadius: 12,
                  background: "linear-gradient(135deg, var(--success), #28a745)",
                  color: "white", fontWeight: 600, fontSize: 14,
                  textDecoration: "none",
                  boxShadow: "0 4px 20px rgba(48, 209, 88, 0.3)",
                  transition: "all 0.3s ease",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.03)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; }}
              >
                ↓ Download PDF
              </a>
              <button
                onClick={resetAll}
                style={{
                  padding: "12px 28px", borderRadius: 12,
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid var(--glass-border)",
                  color: "var(--text-secondary)", fontWeight: 500, fontSize: 14,
                  cursor: "pointer", fontFamily: "Inter, sans-serif",
                  transition: "all 0.3s ease",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.1)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.06)"; }}
              >
                Generate Another
              </button>
            </div>
          </div>
        )}

        {/* ── Pipeline Info Cards ─────────────────────────────────────── */}
        <div className="animate-fade-in-up-delay-2" style={{
          display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12,
          marginTop: 12,
        }}>
          {[
            { icon: "📄", title: "PDF Extraction", desc: "PyMuPDF extracts text and images from both source documents", tag: "Step 1" },
            { icon: "🧠", title: "AI Analysis", desc: "Gemini 2.5 Flash merges, deduplicates, and structures observations", tag: "Step 2" },
            { icon: "📋", title: "Report Generation", desc: "ReportLab builds a branded DDR PDF with embedded images", tag: "Step 3" },
          ].map((item) => (
            <div key={item.title} style={{
              background: "var(--dark-surface)", borderRadius: 16,
              border: "1px solid var(--glass-border)",
              padding: "20px", transition: "all 0.3s ease",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = "rgba(212, 168, 67, 0.3)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--glass-border)"; }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: "rgba(212, 168, 67, 0.1)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 16,
                }}>{item.icon}</div>
                <span style={{
                  fontSize: 10, fontWeight: 600, color: "var(--gold)",
                  padding: "3px 8px", borderRadius: 6,
                  background: "rgba(212, 168, 67, 0.1)",
                  textTransform: "uppercase", letterSpacing: "0.5px",
                }}>{item.tag}</span>
              </div>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{item.title}</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.5 }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </main>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <footer style={{
        borderTop: "1px solid var(--glass-border)",
        padding: "16px 24px",
        textAlign: "center",
      }}>
        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
          © {new Date().getFullYear()} Harsh Jain · AI-Powered DDR Report Generator · Powered by Gemini 2.5 Flash
        </div>
      </footer>
    </div>
  );
}
