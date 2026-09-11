import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listFilms } from "../api/client";

export default function LibraryPage() {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  async function refresh() { setLoading(true); try { setFilms((await listFilms()).data); } finally { setLoading(false); } }
  useEffect(() => { refresh(); }, []);
  return <section className="space-y-6">
    <div className="panel flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:justify-between sm:text-left">
      <div><div className="eyebrow">Your visual archive</div><h1 className="mt-2 text-3xl font-semibold">Library</h1><p className="mt-2 text-slate-300">Sources, uploads, extracted keyframes, and analysis-ready frames.</p></div>
      <button className="button-accent" onClick={refresh}>Refresh Vault</button>
    </div>
    {loading ? <div className="status-message">Loading your vault…</div> : !films.length ? <div className="empty-state">Your vault is empty. Ingest a reference to begin.</div> :
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">{films.map((film) => <article className="library-card" key={film.id}>
        {film.thumbnail_url ? <img src={film.thumbnail_url} alt="" loading="lazy" /> : <div className="library-placeholder">FV</div>}
        <div className="card-content"><div><h2>{film.title}</h2><p>{film.image_count} frames · {film.downloaded_count} downloaded</p></div><div className="card-footer"><span className="card-badge">Collection</span><button className="button-primary" onClick={() => navigate(`/films/${film.id}`)}>Explore</button></div></div>
      </article>)}</div>}
  </section>;
}
