import { Component, useEffect, useState } from "react";
import { Menu, Search, Library, Upload, FlaskConical, FolderKanban, ScanLine } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { NavLink, Outlet, useLocation, useNavigate, useParams } from "react-router-dom";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { getFrame, getFrameAnalysis, listFilms } from "./api/client";
import FrameVaultLogo from "./components/FrameVaultLogo";
import ShotDNA from "./components/ShotDNA";
import { Alert } from "./components/ui/alert";
import { Button } from "./components/ui/button";
import SearchPage from "./pages/SearchPage";
import CuratorPage from "./pages/CuratorPage";
import LibraryPage from "./pages/LibraryPage";
import IngestPage from "./pages/IngestPage";

const navigation = [
  ["/search", "Search", Search], ["/library", "Library", Library], ["/ingest", "Ingest", Upload],
  ["/analyze", "Analyze", ScanLine], ["/projects", "Projects", FolderKanban], ["/lab", "Lab", FlaskConical],
];

function NavItems({ onSelect }) {
  return navigation.map(([to, label, Icon]) => <NavLink key={to} to={to} onClick={onSelect} className={({ isActive }) => isActive ? "nav-active" : "nav-button"}><Icon size={15} /> {label}</NavLink>);
}

function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  return <div className="app-shell">
    <header className="topbar">
      <NavLink className="brand" to="/"><span className="brand-mark"><FrameVaultLogo className="brand-logo" /></span><span><span className="brand-title">FrameVault</span><span className="brand-subtitle">Cinematography Intelligence</span></span></NavLink>
      <nav className="nav desktop-nav"><NavItems /></nav>
      <DialogPrimitive.Root open={menuOpen} onOpenChange={setMenuOpen}>
        <DialogPrimitive.Trigger asChild><button className="mobile-menu" aria-label="Open navigation"><Menu /></button></DialogPrimitive.Trigger>
        <DialogPrimitive.Portal><DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/70" /><DialogPrimitive.Content className="fixed right-0 top-0 z-50 flex h-full w-72 flex-col gap-3 border-l border-white/10 bg-[#0d0f11] p-6"><DialogPrimitive.Title className="text-xl text-[#f1ddc0]">Navigate</DialogPrimitive.Title><NavItems onSelect={() => setMenuOpen(false)} /></DialogPrimitive.Content></DialogPrimitive.Portal>
      </DialogPrimitive.Root>
    </header>
    <main className="page"><AnimatePresence mode="wait"><motion.section key={location.pathname} className="workspace" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}><Outlet /></motion.section></AnimatePresence></main>
  </div>;
}

function SearchRoute() { const navigate = useNavigate(); return <SearchPage onFilmReady={(id) => navigate(`/films/${id}`)} />; }
function FilmRoute() { const { filmId } = useParams(); const navigate = useNavigate(); return <CuratorPage filmId={Number(filmId)} onBack={() => navigate("/library")} onDownloaded={() => {}} />; }
function IngestRoute() { const navigate = useNavigate(); return <IngestPage onImported={() => navigate("/library")} />; }

function LibraryRoute() {
  const [films, setFilms] = useState([]); const [error, setError] = useState(""); const navigate = useNavigate();
  const refresh = async () => { try { setFilms((await listFilms()).data); setError(""); } catch (err) { setError(err.response?.data?.detail || err.message); } };
  useEffect(() => { refresh(); }, []);
  if (error) return <Alert title="Could not load the library" action={<Button onClick={refresh}>Retry</Button>}>{error}</Alert>;
  return <LibraryPage films={films} onOpenFilm={(id) => navigate(`/films/${id}`)} onRefresh={refresh} />;
}

function FrameRoute() {
  const { frameId } = useParams(); const [frame, setFrame] = useState(null); const [analysis, setAnalysis] = useState(null); const [error, setError] = useState("");
  useEffect(() => { Promise.all([getFrame(frameId), getFrameAnalysis(frameId)]).then(([frameResponse, analysisResponse]) => { setFrame(frameResponse.data); setAnalysis(analysisResponse.data.at(-1) || null); }).catch((err) => setError(err.response?.data?.detail || err.message)); }, [frameId]);
  if (error) return <Alert title="Frame unavailable">{error}</Alert>;
  if (!frame) return <div className="status-message">Loading frame…</div>;
  return <ShotDNA frame={frame} analysis={analysis} loading={false} error="" onRun={() => {}} embedded />;
}

function Upcoming({ title }) { return <section className="panel p-10 text-center"><div className="eyebrow">V2 roadmap</div><h1 className="mt-3 text-4xl">{title}</h1><p className="mt-3 text-stone-400">This workspace is prepared for a later intelligence milestone.</p></section>; }
function NotFound() { return <Alert title="Page not found">The requested FrameVault route does not exist.</Alert>; }

export class ErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  render() { return this.state.error ? <main className="page"><Alert title="FrameVault encountered an error" action={<Button onClick={() => location.reload()}>Reload</Button>}>{this.state.error.message}</Alert></main> : this.props.children; }
}

export const routes = [{ element: <AppShell />, children: [
  { index: true, element: <SearchRoute /> }, { path: "search", element: <SearchRoute /> }, { path: "library", element: <LibraryRoute /> },
  { path: "films/:filmId", element: <FilmRoute /> }, { path: "frames/:frameId", element: <FrameRoute /> }, { path: "ingest", element: <IngestRoute /> },
  { path: "analyze", element: <Upcoming title="Analyze Shot" /> }, { path: "projects", element: <Upcoming title="Projects" /> }, { path: "lab", element: <Upcoming title="FrameVault Lab" /> },
  { path: "*", element: <NotFound /> },
]}];
