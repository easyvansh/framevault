import { cn } from "../../lib/utils";

export function Skeleton({ className }) {
  return <div className={cn("animate-pulse rounded-xl bg-white/[.07]", className)} aria-hidden="true" />;
}
