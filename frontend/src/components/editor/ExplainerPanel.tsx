import { useState } from "react";
import { X, Loader2, AlertTriangle, Sparkles, Download } from "lucide-react";
import clsx from "clsx";
import { useCanvasStore } from "@/store/useCanvasStore";
import { explainFlowchart, type ExplainMode } from "@/api/explainer";

interface Props {
  open: boolean;
  onClose: () => void;
}

const MODES: { id: ExplainMode; label: string }[] = [
  { id: "simple", label: "Simple (Beginner)" },
  { id: "line_by_line", label: "Line by Line" },
  { id: "interview", label: "Interview Style" },
  { id: "study_notes", label: "Study Notes (Prof)" },
  { id: "generate_quiz", label: "Generate Quiz (MCQ)" },
  { id: "dry_run", label: "Dry-Run Trace" },
  { id: "custom", label: "Custom Topic" },
];

export function ExplainerPanel({ open, onClose }: Props) {
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);

  const [mode, setMode] = useState<ExplainMode>("simple");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [customPrompt, setCustomPrompt] = useState("");

  async function handleExplain(selectedMode: ExplainMode) {
    setMode(selectedMode);
    setStatus("loading");
    setErrorMessage(null);
    try {
      const result = await explainFlowchart(nodes, edges, selectedMode, selectedMode === "custom" ? customPrompt : undefined);
      setExplanation(result.explanation);
      setWarnings(result.warnings);
      setStatus("idle");
    } catch (err: any) {
      setStatus("error");
      setErrorMessage(
        err?.response?.data?.detail ??
          "Couldn't generate an explanation. Make sure AI_PROVIDER and an API key are configured in the backend .env."
      );
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
            <Sparkles size={18} className="text-violet-400" />
            <h2 className="font-display text-base font-medium text-paper-100">AI Explainer</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-paper-100">
            <X size={18} />
          </button>
        </div>

        <div className="flex flex-wrap gap-1 px-5 py-3 border-b border-white/[0.06] bg-white/[0.01]">
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => {
                setMode(m.id);
                setExplanation(null);
                if (m.id !== "custom") {
                  handleExplain(m.id);
                }
              }}
              className={clsx(
                "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors border",
                mode === m.id
                  ? "bg-violet-500 text-white border-violet-500"
                  : "bg-white/[0.02] text-paper-300 border-white/5 hover:bg-white/[0.08] hover:text-paper-100"
              )}
            >
              {m.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-auto px-5 py-5">
          {mode === "custom" && (
            <div className="mb-4 flex flex-col gap-2 rounded-xl border border-white/5 bg-white/[0.02] p-4">
              <label className="text-xs text-paper-400 font-medium">
                Enter any topic or prompt to analyze this flowchart logic (e.g. Nested loops, Recursion trace, Indexing behavior):
              </label>
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="How does recursion call stack work here? / Explain variables indexing / Run dry-run for input list..."
                className="h-16 w-full resize-none rounded-lg border border-white/10 bg-ink-950 p-2.5 text-xs text-paper-100 placeholder:text-paper-500 outline-none focus:border-violet-500"
              />
              <button
                onClick={() => handleExplain("custom")}
                disabled={status === "loading" || !customPrompt.trim()}
                className="btn-primary mt-2 self-end py-1.5 px-4 text-xs font-semibold"
              >
                {status === "loading" ? "Analyzing..." : "Analyze Topic"}
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
          {status === "idle" && !explanation && (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
              <Sparkles size={22} className="text-paper-500" />
              <p className="text-sm text-paper-500">
                {mode === "custom"
                  ? "Enter your custom query above to analyze specific logic concepts."
                  : "Pick an explanation style above to have the AI walk through your flowchart."}
              </p>
            </div>
          )}
          {status === "idle" && explanation && (
            <div className="flex flex-col gap-4">
              <div className="whitespace-pre-wrap text-sm leading-relaxed text-paper-200 bg-white/[0.02] border border-white/[0.04] p-4 rounded-xl">{explanation}</div>
              <button
                onClick={() => {
                  const isQuiz = mode === "generate_quiz";
                  const isDryRun = mode === "dry_run";
                  const filename = isQuiz
                    ? "student_quiz.md"
                    : isDryRun
                    ? "dry_run_trace.md"
                    : `study_notes_${mode}.md`;
                  const blob = new Blob([explanation], { type: "text/markdown" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = filename;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="btn-primary flex items-center justify-center gap-2 self-start py-2 px-4 text-xs font-semibold"
              >
                <Download size={14} /> {mode === "generate_quiz" ? "Download Student Quiz (.md)" : mode === "dry_run" ? "Download Dry-Run Sheet (.md)" : "Download Study Notes (.md)"}
              </button>
            </div>
          )}

          {warnings.length > 0 && (
            <div className="mt-4 flex flex-col gap-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2">
              {warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-amber-300">
                  <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                  {w}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
