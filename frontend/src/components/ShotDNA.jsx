import { resolveMediaUrl } from "../api/client";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "./ui/dialog";

const percent = (value) => `${Math.round(value * 100)}%`;

function Content({ frame, analysis, loading, error, onRun, embedded }) {
  const data = analysis?.results;
  return <>
        <div className="shot-dna-header">
          <div><div className="eyebrow">Measured signals</div>{embedded ? <h2>Shot DNA</h2> : <><DialogTitle>Shot DNA</DialogTitle><DialogDescription className="sr-only">Classical visual analysis for this frame</DialogDescription></>}</div>
        </div>
        <img className="shot-dna-image" src={resolveMediaUrl(frame.preview_url || frame.source_url)} alt={frame.alt_text || "Analyzed frame"} />
        {loading && <div className="status-message">Analyzing frame…</div>}
        {error && <div className="status-message">{error}</div>}
        {!loading && !data && <button className="button-primary" onClick={onRun}>Analyze this frame</button>}
        {data && <>
          <div className="shot-dna-grid">
            <article><span>Brightness</span><strong>{percent(data.luminance.brightness)}</strong></article>
            <article><span>Contrast</span><strong>{percent(data.luminance.contrast)}</strong></article>
            <article><span>Saturation</span><strong>{percent(data.color.saturation)}</strong></article>
            <article><span>Symmetry</span><strong>{percent(data.composition.symmetry)}</strong></article>
            <article><span>Edge density</span><strong>{percent(data.composition.edge_density)}</strong></article>
            <article><span>Aspect ratio</span><strong>{data.dimensions.aspect_ratio}:1</strong></article>
          </div>
          <div className="palette-row">
            {data.color.palette.map((color) => <div key={color.hex} title={`${color.hex} · ${percent(color.weight)}`} style={{ backgroundColor: color.hex }} />)}
          </div>
          <p className="shot-dna-note">
            Visual center: {percent(data.composition.visual_center.x)} across, {percent(data.composition.visual_center.y)} down · Sharpness score: {Math.round(data.quality.sharpness)}
          </p>
          <p className="shot-dna-note">Analyzer {analysis.analyzer_name} · version {analysis.analyzer_version} · {analysis.execution_ms.toFixed(1)} ms</p>
        </>}
  </>;
}

export default function ShotDNA({ frame, analysis, loading, error, onClose, onRun, embedded = false }) {
  if (embedded) return <section className="shot-dna-panel shot-dna-embedded"><Content {...{ frame, analysis, loading, error, onRun, embedded }} /></section>;
  return <Dialog open onOpenChange={(open) => { if (!open) onClose(); }}><DialogContent className="shot-dna-panel"><Content {...{ frame, analysis, loading, error, onRun }} /></DialogContent></Dialog>;
}
