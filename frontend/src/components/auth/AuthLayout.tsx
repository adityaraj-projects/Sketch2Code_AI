import { Link } from "react-router-dom";
import { PenLine } from "lucide-react";
import type { ReactNode } from "react";

export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-ink-950 bg-sketch-glow px-4">
      <div className="absolute inset-0 bg-grid-pattern bg-[length:32px_32px] opacity-40" />

      <div className="relative z-10 w-full max-w-sm">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500">
            <PenLine size={16} className="text-white" />
          </div>
          <span className="font-display text-lg font-semibold text-paper-100">Sketch2Code AI</span>
        </Link>

        <div className="glass-panel rounded-2xl p-8">
          <h1 className="font-display text-xl font-semibold text-paper-100">{title}</h1>
          <p className="mt-1 text-sm text-paper-500">{subtitle}</p>
          <div className="mt-6">{children}</div>
        </div>

        {footer && <div className="mt-6 text-center text-sm text-paper-500">{footer}</div>}
      </div>
    </div>
  );
}
