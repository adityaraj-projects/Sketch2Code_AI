import { useState } from "react";
import { X, Loader2, AlertTriangle, Gauge, Lightbulb } from "lucide-react";
import { useCanvasStore } from "@/store/useCanvasStore";
import { analyzeComplexity, type ComplexityResponse } from "@/api/complexity";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function ComplexityPanel({ open, onClose }: Props) {
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);

  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<ComplexityResponse | null>(null);

  async function handleAnalyze() {
    const hasStart = nodes.some((n) => n.type === "start");
    if (!hasStart) {
      setStatus("error");
      setErrorMessage("Add a Start shape to your flowchart first.");
      return;
    }
    setStatus("loading");
    setErrorMessage(null);
    try {
      const data = await analyzeComplexity(nodes, edges);
      setResult(data);
      setStatus("idle");
    } catch (err: any) {
      setStatus("error");
      setErrorMessage(err?.response?.data?.detail ?? "Couldn't analyze complexity. Please try again.");
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <div
        className="glass-panel flex h-full w-full max-w-lg flex-col border-l border-white/10"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
          <div className="flex items-center gap-2">
            <Gauge size={18} className="text-violet-400" />
            <h2 className="font-display text-base font-medium text-paper-100">Time & Space Complexity</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-paper-100">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-auto px-5 py-5">
          {status === "idle" && !result && (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <Gauge size={22} className="text-paper-500" />
              <p className="text-sm text-paper-500">Analyze your flowchart's Big-O time and space complexity.</p>
              <button onClick={handleAnalyze} className="btn-primary !px-4 !py-2 text-sm">
                Analyze
              </button>
            </div>
          )}

          {status === "loading" && (
            <div className="flex h-full items-center justify-center">
              <Loader2 size={22} className="animate-spin text-violet-400" />
            </div>
          )}

          {status === "error" && (
            <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              {errorMessage}
            </div>
          )}

          {status === "idle" && result && (
            <div className="flex flex-col gap-5">
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-violet-500/30 bg-violet-500/[0.08] p-4 text-center">
                  <span className="label-eyebrow">Time</span>
                  <p className="mt-1 font-display text-2xl font-semibold text-paper-100">{result.time_complexity}</p>
                </div>
                <div className="rounded-xl border border-mint-400/30 bg-mint-400/[0.08] p-4 text-center">
                  <span className="label-eyebrow !text-mint-400">Space</span>
                  <p className="mt-1 font-display text-2xl font-semibold text-paper-100">{result.space_complexity}</p>
                </div>
              </div>

              {result.confidence === "estimated" && (
                <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
                  <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                  This is an estimate — one or more loops didn't match a recognizable growth pattern.
                </div>
              )}

              <div>
                <span className="label-eyebrow">Reasoning</span>
                <ul className="mt-2 flex flex-col gap-1.5">
                  {result.reasoning.map((r, i) => (
                    <li key={i} className="rounded-lg border border-white/10 bg-ink-950 px-3 py-2 text-xs text-paper-300">
                      {r}
                    </li>
                  ))}
                </ul>
              </div>

              {result.suggestions.length > 0 && (
                <div>
                  <span className="label-eyebrow">Optimization ideas</span>
                  <ul className="mt-2 flex flex-col gap-1.5">
                    {result.suggestions.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 rounded-lg border border-white/10 bg-ink-950 px-3 py-2 text-xs text-paper-300">
                        <Lightbulb size={13} className="mt-0.5 shrink-0 text-violet-400" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.narrative && (
                <div>
                  <span className="label-eyebrow">AI summary</span>
                  <p className="mt-2 whitespace-pre-wrap rounded-lg border border-white/10 bg-ink-950 px-3 py-2.5 text-sm leading-relaxed text-paper-200">
                    {result.narrative}
                  </p>
                </div>
              )}
              {!result.narrative && result.narrative_unavailable_reason && (
                <p className="text-xs text-paper-500">
                  AI summary unavailable: {result.narrative_unavailable_reason}
                </p>
              )}

              <button onClick={handleAnalyze} className="btn-secondary self-start !px-3 !py-1.5 text-xs">
                Re-analyze
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
