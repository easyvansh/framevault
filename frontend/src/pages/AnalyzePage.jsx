import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeFrame, uploadImages } from "../api/client";

export default function AnalyzePage() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  async function analyze(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true); setError("");
    try {
      const uploaded = await uploadImages([file]);
      const frame = uploaded.data.frames[0];
      await analyzeFrame(frame.id);
      navigate(`/frames/${frame.id}`);
    } catch (reason) {
      setError(reason.response?.data?.detail || reason.message || "The frame could not be analyzed.");
      setBusy(false);
    }
  }
  return <section className="analyze-hero panel">
    <div className="eyebrow">Explainable visual analysis</div>
    <h1>Drop a frame.<br /><em>Understand the shot.</em></h1>
    <p>Measure palette, luminance, contrast, symmetry, composition, sharpness, and exposure with a deterministic analysis pipeline.</p>
    <label className={`drop-zone ${busy ? "is-busy" : ""}`}>
      <span className="drop-icon">＋</span><strong>{busy ? "Reading the image…" : "Choose a frame to analyze"}</strong><small>JPEG, PNG, or WebP · 25 MiB maximum</small>
      <input className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" onChange={analyze} disabled={busy} />
    </label>
    {error && <div className="status-message">{error}</div>}
    <div className="trust-row"><span>Local-first</span><span>Versioned results</span><span>No black-box labels</span></div>
  </section>;
}
