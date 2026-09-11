import { cn } from "../../lib/utils";

export function Badge({ className, children }) {
  return <span className={cn("inline-flex rounded-full border border-[#d8bf97]/25 bg-[#d8bf97]/10 px-3 py-1 text-xs font-bold uppercase tracking-wide text-[#f1ddc0]", className)}>{children}</span>;
}
