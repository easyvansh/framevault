import FrameCard from "./FrameCard";

export default function FrameGrid({ frames, onToggle }) {
  if (!frames.length) {
    return <div className="panel p-8 text-center text-slate-400">No frames found for this film yet.</div>;
  }

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {frames.map((frame) => (
        <FrameCard key={frame.id} frame={frame} onToggle={onToggle} />
      ))}
    </div>
  );
}
