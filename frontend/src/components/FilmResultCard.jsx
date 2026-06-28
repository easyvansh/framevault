export default function FilmResultCard({ result, onSelect, loading }) {
  return (
    <article className="result-card">
      {result.thumbnail_url ? (
        <img className="h-44 w-full object-cover" src={result.thumbnail_url} alt="" loading="lazy" />
      ) : (
        <div className="flex h-44 items-center justify-center bg-slate-900 text-sm text-slate-500">No thumbnail</div>
      )}
      <div className="card-content">
        <div>
          <span className="status-chip">FilmGrab Result</span>
          <h2 className="mt-3">{result.title}</h2>
          {result.excerpt && <p className="text-sm text-slate-300">{result.excerpt}</p>}
        </div>
        <div className="flex flex-wrap gap-3">
          <button className="button-primary" disabled={loading} onClick={() => onSelect(result)}>
            {loading ? "Scraping frames..." : "Scrape Frames"}
          </button>
          <a className="button-secondary" href={result.url} target="_blank" rel="noreferrer">
            Open Source
          </a>
        </div>
      </div>
    </article>
  );
}
