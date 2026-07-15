import { Link } from "react-router-dom";
import { PenLine } from "lucide-react";

export function Navbar() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.06] bg-ink-950/70 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-500">
            <PenLine size={14} className="text-white" />
          </div>
          <span className="font-display text-[15px] font-semibold text-paper-100">
            Sketch2Code AI
          </span>
        </Link>

        <nav className="hidden items-center gap-8 text-sm text-paper-300 md:flex">
          <a href="#features" className="hover:text-paper-100">Features</a>
          <a href="#pricing" className="hover:text-paper-100">Pricing</a>
          <a href="#testimonials" className="hover:text-paper-100">Testimonials</a>
        </nav>

        <div className="flex items-center gap-3">
          <Link to="/login" className="text-sm text-paper-300 hover:text-paper-100">
            Log in
          </Link>
          <Link to="/signup" className="btn-primary !px-4 !py-2 text-sm">
            Start drawing
          </Link>
        </div>
      </div>
    </header>
  );
}
