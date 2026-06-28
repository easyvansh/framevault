export default function LibraryPage({ films, onOpenFilm, onRefresh }) {
  return (
    <section className="space-y-6">
      <div className="panel flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:justify-between sm:text-left">
        <div>
          <h1 className="text-3xl font-semibold">Library</h1>
          <p className="mt-2 text-base text-slate-300">Downloaded films, curated frames, and metadata stored locally in your vault.</p>
        </div>
        <button className="button-accent" onClick={onRefresh}>Refresh Vault</button>
      </div>

      {!films.length ? (
        <div className="panel p-8 text-center text-slate-300">No films have been scraped yet. Start with a search to fill the vault.</div>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {films.map((film) => (
            <article className="library-card" key={film.id}>
              {film.thumbnail_url ? (
                <img src={film.thumbnail_url} alt="" loading="lazy" />
              ) : (
                <div className="flex h-40 items-center justify-center bg-slate-900 text-slate-500">No thumbnail</div>
              )}
              <div className="card-content">
                <div>
                  <h2>{film.title}</h2>
                  <p>{film.image_count} frames / {film.downloaded_count} downloaded</p>
                </div>
                <div className="card-footer">
                  <span className="card-badge">Vault film</span>
                  <button className="button-primary" onClick={() => onOpenFilm(film.id)}>Open Curator</button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
