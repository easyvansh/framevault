import { useState } from "react";
import { Link } from "react-router-dom";
import { extractVideoShots, uploadImages, uploadVideo } from "../api/client";

export default function IngestPage() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [shots, setShots] = useState([]);
  const [threshold, setThreshold] = useState(0.3);

  async function importImages(event) {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;
    setBusy(true); setMessage(""); setShots([]);
    try {
      const response = await uploadImages(files);
      setMessage(`Imported ${response.data.frames.length} frame${response.data.frames.length === 1 ? "" : "s"}. Open Local Uploads in the Library to inspect them.`);
    } catch (error) { setMessage(error.response?.data?.detail || error.message || "Image import failed."); }
    finally { event.target.value = ""; setBusy(false); }
  }

  async function importVideo(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true); setMessage(""); setShots([]);
    try {
      const response = await uploadVideo(file);
      setMessage(`Detecting cuts in ${response.data.asset.original_name}…`);
      const result = await extractVideoShots(response.data.asset.id, threshold);
      setShots(result.data.shots);
      setMessage(`Processed ${response.data.asset.original_name}: ${result.data.shots.length} shots and keyframes ready.`);
    } catch (error) { setMessage(error.response?.data?.detail || error.message || "Video processing failed."); }
    finally { event.target.value = ""; setBusy(false); }
  }

  return <section className="space-y-6">
    <div className="panel p-6 text-center"><div className="eyebrow">Build your visual corpus</div><h1 className="mt-2 text-3xl font-semibold">Ingest Media</h1><p className="mx-auto mt-3 max-w-2xl text-slate-300">Bring licensed images and footage into managed local storage. FrameVault validates, fingerprints, and preserves the origin of every asset.</p></div>
    <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
      <label className="ingest-card panel"><span className="ingest-number">01</span><strong>Still references</strong><p>Import a set of frames for curation and Shot DNA analysis.</p><span className="button-primary">Choose images</span><input className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={importImages} disabled={busy} /></label>
      <div className="ingest-card panel"><span className="ingest-number">02</span><strong>Motion references</strong><p>Detect scene changes and extract a representative midpoint keyframe from every shot.</p><label className="threshold-control">Cut threshold <input type="range" min="0.1" max="0.8" step="0.05" value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} /><b>{threshold.toFixed(2)}</b></label><label className="button-secondary">Choose video<input className="sr-only" type="file" accept="video/mp4,video/quicktime,video/webm,.mkv" onChange={importVideo} disabled={busy} /></label></div>
    </div>
    {busy && <div className="status-message">Importing and processing media…</div>}
    {message && <div className="status-message">{message}</div>}
    {!!shots.length && <div className="panel p-6"><div className="eyebrow">Detected sequence</div><h2 className="mt-2 text-2xl font-semibold">{shots.length} shots ready to inspect</h2><div className="shot-timeline">{shots.map((shot) => <Link to={`/frames/${shot.keyframe_frame_id}`} key={shot.id}><strong>Shot {shot.shot_index + 1}</strong><span>{(shot.start_ms / 1000).toFixed(1)}s – {(shot.end_ms / 1000).toFixed(1)}s</span></Link>)}</div></div>}
  </section>;
}
