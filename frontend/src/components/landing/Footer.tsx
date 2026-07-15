import { PenLine } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-white/[0.06] py-12">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 px-6 md:flex-row">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-500">
            <PenLine size={14} className="text-white" />
          </div>
          <span className="font-display text-sm font-medium text-paper-100">Sketch2Code AI</span>
        </div>
        <p className="text-xs text-paper-500">
          © {new Date().getFullYear()} Sketch2Code AI. From hand drawn logic to production code.
        </p>
      </div>
    </footer>
  );
}
