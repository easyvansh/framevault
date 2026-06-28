import ImageCard from "./ImageCard";

export default function ImageGrid({ images, onToggle }) {
  if (!images.length) {
    return <div className="panel p-8 text-center text-slate-400">No images found for this film yet.</div>;
  }

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {images.map((image) => (
        <ImageCard key={image.id} image={image} onToggle={onToggle} />
      ))}
    </div>
  );
}
