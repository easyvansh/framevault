import { useState } from "react";
import { scrapeFilm, searchFilmGrab } from "../api/client";
import FilmResultCard from "../components/FilmResultCard";
import FrameVaultLogo from "../components/FrameVaultLogo";

export default function SearchPage({ onFilmReady }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scrapingUrl, setScrapingUrl] = useState(null);
  const [message, setMessage] = useState("");

  async function handleSearch(event) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    setLoading(true);
    setMessage("");
    setResults([]);
    try {
      const response = await searchFilmGrab(trimmed);
      setResults(response.data);
      if (!response.data.length) setMessage("No FilmGrab results found.");
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message || "Search failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleScrape(result) {
    setScrapingUrl(result.url);
    setMessage("");
    try {
      const response = await scrapeFilm({
        url: result.url,
        title: result.title,
        thumbnail_url: result.thumbnail_url,
      });
      onFilmReady(response.data.film.id);
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message || "Scrape failed.");
    } finally {
      setScrapingUrl(null);
    }
  }

  return (
    <section>
      <div className="hero">
        <div className="hero-inner">
          <div className="hero-logo-wrap">
            <FrameVaultLogo className="hero-logo" />
          </div>
          <div className="eyebrow">FrameVault</div>
          <h1 className="hero-title">
            Your <em>Cinematography</em> Reference. Organized. Offline.
          </h1>
          <p className="hero-copy">
            Search FilmGrab, preview stills, select the frames that matter, and download a clean local archive with metadata.
          </p>

          <form className="search-panel" onSubmit={handleSearch}>
            <label className="sr-only" htmlFor="filmgrab-search">Search FilmGrab</label>
            <input
              id="filmgrab-search"
              className="search-input"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search film, director, cinematographer..."
            />
            <button className="button-primary" disabled={loading}>
              {loading ? "Searching..." : "Search"}
            </button>
          </form>

          <div className="quick-actions">
            <div className="quick-action"><strong>Search</strong><span>Film, artist, mood</span></div>
            <div className="quick-action"><strong>Preview</strong><span>Scraped stills</span></div>
            <div className="quick-action"><strong>Select</strong><span>Curate frames</span></div>
            <div className="quick-action"><strong>Download</strong><span>Offline metadata</span></div>
          </div>
        </div>
      </div>

      {message && <div className="status-message">{message}</div>}

      {(results.length > 0 || (!message && !loading)) && (
        <div className="results-section">
          <h2 className="section-heading">{results.length ? "FilmGrab Results" : "Ready to Search"}</h2>
          {!results.length && !message && !loading && (
            <div className="empty-state">Try Blade Runner, Roger Deakins, Wong Kar Wai, noir, or Dune.</div>
          )}
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {results.map((result) => (
              <FilmResultCard key={result.url} result={result} onSelect={handleScrape} loading={scrapingUrl === result.url} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
