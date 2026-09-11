<<<<<<< HEAD
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import "./styles.css";
import SearchPage from "./pages/SearchPage";
import CuratorPage from "./pages/CuratorPage";
import LibraryPage from "./pages/LibraryPage";
import IngestPage from "./pages/IngestPage";
import AnalyzePage from "./pages/AnalyzePage";
import FrameDetailPage from "./pages/FrameDetailPage";
import FrameVaultLogo from "./components/FrameVaultLogo";

const navClass = ({ isActive }) => isActive ? "nav-active" : "nav-button";

function App() {
  const navigate = useNavigate();
  return <div className="app-shell">
    <header className="topbar">
      <button className="brand" onClick={() => navigate("/")}>
        <span className="brand-mark"><FrameVaultLogo className="brand-logo" /></span>
        <span><span className="brand-title">FrameVault</span><span className="brand-subtitle">Cinematography Intelligence</span></span>
      </button>
      <nav className="nav" aria-label="Primary navigation">
        <NavLink to="/" end className={navClass}>Discover</NavLink>
        <NavLink to="/analyze" className={navClass}>Analyze Shot</NavLink>
        <NavLink to="/library" className={navClass}>Library</NavLink>
        <NavLink to="/ingest" className={navClass}>Ingest</NavLink>
      </nav>
    </header>
    <main className="page"><section className="workspace"><Routes>
      <Route path="/" element={<SearchPage onFilmReady={(id) => navigate(`/films/${id}`)} />} />
      <Route path="/films/:filmId" element={<CuratorPage onBack={() => navigate(-1)} onDownloaded={() => {}} />} />
      <Route path="/frames/:frameId" element={<FrameDetailPage />} />
      <Route path="/analyze" element={<AnalyzePage />} />
      <Route path="/library" element={<LibraryPage />} />
      <Route path="/ingest" element={<IngestPage />} />
      <Route path="*" element={<div className="panel p-8 text-center">Page not found.</div>} />
    </Routes></section></main>
  </div>;
}

createRoot(document.getElementById("root")).render(<BrowserRouter><App /></BrowserRouter>);
=======
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./styles.css";
import { ErrorBoundary, routes } from "./App";

const router = createBrowserRouter(routes);
createRoot(document.getElementById("root")).render(<ErrorBoundary><RouterProvider router={router} /></ErrorBoundary>);
>>>>>>> 1b5c36d (updated to v2)
