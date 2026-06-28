import { useEffect, useMemo, useState } from "react";
import { downloadAll, downloadSelected, listImages, setImageSelected } from "../api/client";
import ImageGrid from "../components/ImageGrid";

export default function CuratorPage({ filmId, onBack, onDownloaded }) {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [downloading, setDownloading] = useState(false);

  const selectedCount = useMemo(() => images.filter((image) => image.selected).length, [images]);

  async function refreshImages() {
    setLoading(true);
    try {
      const response = await listImages(filmId);
      setImages(response.data);
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message || "Could not load images.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshImages();
  }, [filmId]);

  async function toggleImage(image) {
    const nextSelected = !image.selected;
    setImages((current) => current.map((item) => (item.id === image.id ? { ...item, selected: nextSelected } : item)));
    try {
      await setImageSelected(image.id, nextSelected);
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message || "Could not update selection.");
      refreshImages();
    }
  }

  async function bulkSelect(selected) {
    const previous = images;
    setImages((current) => current.map((image) => ({ ...image, selected })));
    try {
      await Promise.all(previous.map((image) => setImageSelected(image.id, selected)));
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
              {images.length} frames found / {selectedCount} selected. Tap frames to choose your offline highlights.
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2 lg:justify-start">
              <span className="status-chip">Scraped {images.length}</span>
              <span className="status-chip selected">Selected {selectedCount}</span>
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-3 pt-3 lg:justify-end lg:pt-0">
            <button className="button-secondary" onClick={() => bulkSelect(true)} disabled={!images.length}>Select All</button>
            <button className="button-secondary" onClick={() => bulkSelect(false)} disabled={!images.length}>Clear</button>
            <button className="button-primary" onClick={() => runDownload(true)} disabled={!selectedCount || downloading}>
              Download Selected
            </button>
            <button className="button-secondary" onClick={() => runDownload(false)} disabled={!images.length || downloading}>
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
          <ImageGrid images={images} onToggle={toggleImage} />
        </div>
      )}
    </section>
  );
}
