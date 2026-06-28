export default function ImageCard({ image, onToggle }) {
  return (
    <article className={`image-card ${image.selected ? "selected" : ""}`}>
      <button className="block w-full text-left" onClick={() => onToggle(image)}>
        <img className="aspect-video w-full bg-slate-950 object-cover" src={image.preview_url || image.source_url} alt={image.alt_text || ""} loading="lazy" />
      </button>
      <div className="image-footer">
        <button className={image.selected ? "button-primary" : "button-secondary"} onClick={() => onToggle(image)}>
          {image.selected ? "Selected" : "Select Frame"}
        </button>
        {image.downloaded && <span className="status-chip selected">Downloaded</span>}
        <a className="source-link" href={image.source_url} target="_blank" rel="noreferrer">
          Source
        </a>
      </div>
    </article>
  );
}
