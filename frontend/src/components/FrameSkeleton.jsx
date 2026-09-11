import { Skeleton } from "./ui/skeleton";

export default function FrameSkeleton() {
  return <div className="overflow-hidden rounded-2xl border border-white/[.07] bg-black/30"><Skeleton className="aspect-video rounded-none" /><div className="space-y-2 p-4"><Skeleton className="h-4 w-2/3" /><Skeleton className="h-3 w-1/3" /></div></div>;
}
