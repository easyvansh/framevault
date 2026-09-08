import { useEffect, useMemo, useState } from "react";
import { analyzeFrame, downloadAll, downloadSelected, getFrameAnalysis, listFrames, setFrameSelected } from "../api/client";
import FrameGrid from "../components/FrameGrid";
import ShotDNA from "../components/ShotDNA";

export default function CuratorPage({ filmId, onBack, onDownloaded }) {
  const [frames, setFrames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [analysisFrame, setAnalysisFrame] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState("");

  const selectedCount = useMemo(() => frames.filter((frame) => frame.selected).length, [frames]);

  async function refreshImages() {
    setLoading(true);
    try {
      const response = await listFrames(filmId);
      setFrames(response.data);
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message || "Could not load frames.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshImages();
  }, [filmId]);

  async function toggleFrame(frame) {
    const nextSelected = !frame.selected;
    setFrames((current) => current.map((item) => (item.id === frame.id ? { ...item, selected: nextSelected } : item)));
    try {
      await setFrameSelected(frame.id, nextSelected);
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message || "Could not update selection.");
      refreshImages();
    }
  }

  async function bulkSelect(selected) {
    const previous = frames;
    setFrames((current) => current.map((frame) => ({ ...frame, selected })));
    try {
      await Promise.all(previous.map((frame) => setFrameSelected(frame.id, selected)));
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message || "Could not update selections.");
      refreshImages();
    }
  }

  async function runDownload(selectedOnly) {
    setDownloading(true);
    setMessage("");
    try {
      const response = selectedOnly ? await downloadSelected(filmId) : await downloadAll(filmId);
      const summary = response.data;
      setMessage(`Downloaded ${summary.downloaded}, skipped ${summary.skipped}, failed ${summary.failed}. Saved metadata to ${summary.metadata_path}.`);
      await refreshImages();
      onDownloaded();
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message || "Download failed.");
    } finally {
      setDownloading(false);
    }
  }

  async function openAnalysis(frame) {
    setAnalysisFrame(frame);
    setAnalysis(null);
    setAnalysisError("");
    setAnalysisLoading(true);
    try {
      const response = await getFrameAnalysis(frame.id);
      setAnalysis(response.data.at(-1) || null);
    } catch (error) {
      setAnalysisError(error.response?.data?.detail || error.message);
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function runAnalysis() {
    setAnalysisLoading(true);
    setAnalysisError("");
    try {
      const response = await analyzeFrame(analysisFrame.id);
      setAnalysis(response.data);
    } catch (error) {
      setAnalysisError(error.response?.data?.detail || error.message || "Analysis failed.");
    } finally {
      setAnalysisLoading(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="panel p-6 text-center">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <button className="button-ghost" onClick={onBack}>
              Back to search
            </button>
            <h1 className="mt-4 text-3xl font-semibold">Preview and Select Frames</h1>
            <p className="mt-2 text-base text-slate-300">
              {frames.length} frames found / {selectedCount} selected. Tap frames to choose your offline highlights.
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2 lg:justify-start">
              <span className="status-chip">Scraped {frames.length}</span>
              <span className="status-chip selected">Selected {selectedCount}</span>
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-3 pt-3 lg:justify-end lg:pt-0">
            <button className="button-secondary" onClick={() => bulkSelect(true)} disabled={!frames.length}>Select All</button>
            <button className="button-secondary" onClick={() => bulkSelect(false)} disabled={!frames.length}>Clear</button>
            <button className="button-primary" onClick={() => runDownload(true)} disabled={!selectedCount || downloading}>
              Download Selected
            </button>
            <button className="button-secondary" onClick={() => runDownload(false)} disabled={!frames.length || downloading}>
              Download All
            </button>
          </div>
        </div>
      </div>

      {message && <div className="status-message">{message}</div>}
      {loading ? (
        <div className="panel p-8 text-center text-slate-400">Loading frames...</div>
      ) : (
        <div className="filmstrip-panel">
          <FrameGrid frames={frames} onToggle={toggleFrame} onAnalyze={openAnalysis} />
        </div>
      )}
      {analysisFrame && <ShotDNA frame={analysisFrame} analysis={analysis} loading={analysisLoading} error={analysisError} onRun={runAnalysis} onClose={() => setAnalysisFrame(null)} />}
    </section>
  );
}
