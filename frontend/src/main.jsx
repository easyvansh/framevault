import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import { listFilms } from "./api/client";
import SearchPage from "./pages/SearchPage";
import CuratorPage from "./pages/CuratorPage";
import LibraryPage from "./pages/LibraryPage";

function App() {
  const [view, setView] = useState("search");
  const [activeFilmId, setActiveFilmId] = useState(null);
  const [films, setFilms] = useState([]);

  async function refreshFilms() {
    const response = await listFilms();
    setFilms(response.data);
  }

  useEffect(() => {
    refreshFilms().catch(() => setFilms([]));
  }, []);

  function openCurator(filmId) {
    setActiveFilmId(filmId);
    setView("curator");
    refreshFilms().catch(() => {});
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => setView("search")}>
          <span className="brand-mark">F</span>
          <span>
            <span className="brand-title">FrameVault</span>
            <span className="brand-subtitle">Cinematography Reference Engine</span>
          </span>
        </button>
        <nav className="nav">
          <button className={view === "search" ? "nav-active" : "nav-button"} onClick={() => setView("search")}>
            Search
          </button>
          {activeFilmId && (
            <button className={view === "curator" ? "nav-active" : "nav-button"} onClick={() => setView("curator")}>
              Curator
            </button>
          )}
          <button className={view === "library" ? "nav-active" : "nav-button"} onClick={() => { refreshFilms(); setView("library"); }}>
            Library
          </button>
        </nav>
      </header>

      <main className="page">
        <section className="workspace">
          {view === "search" && <SearchPage onFilmReady={openCurator} />}
          {view === "curator" && activeFilmId && (
            <CuratorPage filmId={activeFilmId} onBack={() => setView("search")} onDownloaded={refreshFilms} />
          )}
          {view === "library" && <LibraryPage films={films} onOpenFilm={openCurator} onRefresh={refreshFilms} />}
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
