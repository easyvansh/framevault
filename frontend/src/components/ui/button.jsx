import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const variants = cva("inline-flex min-h-10 items-center justify-center rounded-full px-4 text-sm font-semibold transition disabled:pointer-events-none disabled:opacity-50", {
  variants: {
    variant: {
      default: "border border-white/80 bg-stone-100 text-stone-950 hover:bg-white",
      secondary: "border border-white/15 bg-white/[.07] text-stone-100 hover:bg-white/10",
      ghost: "text-stone-200 hover:bg-white/[.07]",
      accent: "border border-amber-200/30 bg-[#d8bf97] text-stone-950 hover:bg-[#f1ddc0]",
    },
  },
  defaultVariants: { variant: "default" },
});

export function Button({ className, variant, ...props }) {
  return <button className={cn(variants({ variant }), className)} {...props} />;
}
