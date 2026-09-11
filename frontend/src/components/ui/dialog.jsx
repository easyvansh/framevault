import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogTitle = DialogPrimitive.Title;
export const DialogDescription = DialogPrimitive.Description;

export function DialogContent({ children, className }) {
  return <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md" />
    <DialogPrimitive.Content className={cn("fixed left-1/2 top-1/2 z-50 max-h-[calc(100vh-2rem)] w-[min(760px,calc(100%-2rem))] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl border border-[#d8bf97]/30 bg-[#0d0f11] p-5 shadow-2xl", className)}>
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-full p-2 text-stone-400 hover:bg-white/10 hover:text-white" aria-label="Close"><X size={18} /></DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>;
}
