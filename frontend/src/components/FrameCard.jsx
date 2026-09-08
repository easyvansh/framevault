export default function FrameCard({ frame, onToggle }) {
  return (
    <article className={`image-card ${frame.selected ? "selected" : ""}`}>
      <button className="block w-full text-left" onClick={() => onToggle(frame)}>
        <img className="aspect-video w-full bg-slate-950 object-cover" src={frame.preview_url || frame.source_url} alt={frame.alt_text || ""} loading="lazy" />
      </button>
      <div className="image-footer">
        <button className={frame.selected ? "button-primary" : "button-secondary"} onClick={() => onToggle(frame)}>
          {frame.selected ? "Selected" : "Select Frame"}
        </button>
        {frame.downloaded && <span className="status-chip selected">Downloaded</span>}
        <a className="source-link" href={frame.source_url} target="_blank" rel="noreferrer">
          Source
        </a>
      </div>
    </article>
  );
}
