import { useState } from "react";
import { X, Loader2, AlertTriangle, Workflow } from "lucide-react";
import { useCanvasStore } from "@/store/useCanvasStore";
import { generateFlowchartFromCode } from "@/api/codetoflow";

interface Props {
  open: boolean;
  onClose: () => void;
}

const PLACEHOLDER = `n = int(input("Enter a number: "))
if n > 0:
    print("positive")
else:
    print("not positive")`;

export function CodeToFlowchartPanel({ open, onClose }: Props) {
  const [code, setCode] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const loadGeneratedFlowchart = useCanvasStore((s) => s.loadGeneratedFlowchart);

  async function handleGenerate() {
    if (!code.trim()) return;
    setStatus("loading");
    setErrorMessage(null);
    setWarnings([]);
    try {
      const result = await generateFlowchartFromCode(code, "python");
      loadGeneratedFlowchart(result.nodes, result.edges);
      setWarnings(result.warnings);
      setStatus("idle");
      if (result.warnings.length === 0) {
        onClose();
      }
    } catch (err: any) {
      setStatus("error");
      setErrorMessage(err?.response?.data?.detail ?? "Couldn't parse that code. Please check it and try again.");
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="glass-panel flex max-h-[85vh] w-full max-w-xl flex-col rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
          <div className="flex items-center gap-2">
            <Workflow size={18} className="text-violet-400" />
            <h2 className="font-display text-base font-medium text-paper-100">Code → Flowchart</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-paper-100">
            <X size={18} />
          </button>
        </div>

        <div className="px-5 pt-4">
          <p className="text-xs text-paper-500">
            Paste Python code and it'll be added as a new flowchart below your existing canvas.
            Other languages are coming soon.
          </p>
        </div>

        <div className="flex-1 overflow-auto px-5 py-4">
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder={PLACEHOLDER}
            spellCheck={false}
            className="h-64 w-full resize-none rounded-xl border border-white/10 bg-ink-950 p-4 font-mono text-[13px] text-paper-100 placeholder:text-paper-500 outline-none focus:border-violet-500"
          />

          {status === "error" && (
            <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              {errorMessage}
            </div>
          )}

          {warnings.length > 0 && (
            <div className="mt-3 flex flex-col gap-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2">
              {warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-amber-300">
                  <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                  {w}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-white/[0.06] px-5 py-3">
          <button onClick={onClose} className="btn-secondary !px-3 !py-1.5 text-xs">
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={!code.trim() || status === "loading"}
            className="btn-primary !px-3 !py-1.5 text-xs"
          >
            {status === "loading" && <Loader2 size={14} className="animate-spin" />}
            Generate Flowchart
          </button>
        </div>
      </div>
    </div>
  );
}
