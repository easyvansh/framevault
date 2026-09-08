import { useState } from "react";
import { uploadImages, uploadVideo } from "../api/client";

export default function IngestPage({ onImported }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function importImages(event) {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await uploadImages(files);
      setMessage(`Imported ${response.data.frames.length} frame${response.data.frames.length === 1 ? "" : "s"}.`);
      await onImported();
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message || "Image import failed.");
    } finally {
      event.target.value = "";
      setBusy(false);
    }
  }

  async function importVideo(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await uploadVideo(file);
      setMessage(`Imported video ${response.data.asset.original_name}. Shot extraction is the next processing stage.`);
      await onImported();
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message || "Video import failed.");
    } finally {
      event.target.value = "";
      setBusy(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="panel p-6 text-center">
        <div className="eyebrow">Local media</div>
        <h1 className="mt-2 text-3xl font-semibold">Ingest Your References</h1>
        <p className="mx-auto mt-3 max-w-2xl text-slate-300">
          Add legal or licensed images and video to managed local storage. Files are validated and deduplicated by content.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <label className="panel cursor-pointer p-8 text-center">
          <strong className="block text-xl">Import images</strong>
          <span className="mt-2 block text-slate-400">JPEG, PNG, or WebP · multiple files supported</span>
          <span className="button-primary mt-6 inline-block">Choose images</span>
          <input className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={importImages} disabled={busy} />
        </label>

        <label className="panel cursor-pointer p-8 text-center">
          <strong className="block text-xl">Import video</strong>
          <span className="mt-2 block text-slate-400">MP4, MOV, MKV, or WebM · FFmpeg required</span>
          <span className="button-secondary mt-6 inline-block">Choose video</span>
          <input className="sr-only" type="file" accept="video/mp4,video/quicktime,video/webm,.mkv" onChange={importVideo} disabled={busy} />
        </label>
      </div>

      {busy && <div className="status-message">Importing media…</div>}
      {message && <div className="status-message">{message}</div>}
    </section>
  );
}
