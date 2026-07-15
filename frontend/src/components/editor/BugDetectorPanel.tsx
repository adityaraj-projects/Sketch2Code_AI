import { useState } from "react";
import { X, Loader2, AlertTriangle, ShieldAlert, CheckCircle2, Bug } from "lucide-react";
import clsx from "clsx";
import { useCanvasStore } from "@/store/useCanvasStore";
import { scanForBugs, type Finding } from "@/api/bugdetector";

interface Props {
  open: boolean;
  onClose: () => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  structure: "Structure",
  missing_arrow: "Missing Arrow",
  disconnected_node: "Disconnected Shape",
  invalid_decision: "Invalid Decision",
  infinite_loop: "Infinite Loop / Dead End",
};

export function BugDetectorPanel({ open, onClose }: Props) {
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const setSelectedIds = useCanvasStore((s) => s.setSelectedIds);

  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [findings, setFindings] = useState<Finding[] | null>(null);
  const [counts, setCounts] = useState<{ errors: number; warnings: number }>({ errors: 0, warnings: 0 });

  async function handleScan() {
    setStatus("loading");
    setErrorMessage(null);
    try {
      const result = await scanForBugs(nodes, edges);
      setFindings(result.findings);
      setCounts({ errors: result.error_count, warnings: result.warning_count });
      setStatus("idle");
    } catch (err: any) {
      setStatus("error");
      setErrorMessage(err?.response?.data?.detail ?? "Couldn't scan the flowchart. Please try again.");
    }
  }

  function handleFindingClick(finding: Finding) {
    if (finding.node_ids.length > 0) {
      setSelectedIds(finding.node_ids);
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
            <Bug size={18} className="text-violet-400" />
            <h2 className="font-display text-base font-medium text-paper-100">Bug Detector</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-paper-100">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-auto px-5 py-5">
          {status === "idle" && findings === null && (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <ShieldAlert size={22} className="text-paper-500" />
              <p className="text-sm text-paper-500">
                Scan for missing arrows, disconnected shapes, invalid decisions, and infinite loops.
              </p>
              <button onClick={handleScan} className="btn-primary !px-4 !py-2 text-sm">
                Scan Flowchart
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

          {status === "idle" && findings !== null && (
            <div className="flex flex-col gap-4">
              <div className="flex gap-3">
                <div className="flex-1 rounded-xl border border-red-500/30 bg-red-500/[0.08] p-3 text-center">
                  <p className="font-display text-xl font-semibold text-red-300">{counts.errors}</p>
                  <span className="text-xs text-paper-500">Errors</span>
                </div>
                <div className="flex-1 rounded-xl border border-amber-500/30 bg-amber-500/[0.08] p-3 text-center">
                  <p className="font-display text-xl font-semibold text-amber-300">{counts.warnings}</p>
                  <span className="text-xs text-paper-500">Warnings</span>
                </div>
              </div>

              {findings.length === 0 ? (
                <div className="flex flex-col items-center gap-2 rounded-xl border border-mint-400/30 bg-mint-400/[0.06] py-8 text-center">
                  <CheckCircle2 size={24} className="text-mint-400" />
                  <p className="text-sm text-paper-200">No issues found — this flowchart looks structurally sound.</p>
                </div>
              ) : (
                <ul className="flex flex-col gap-2">
                  {findings.map((f, i) => (
                    <li key={i}>
                      <button
                        onClick={() => handleFindingClick(f)}
                        className={clsx(
                          "w-full rounded-lg border px-3 py-2.5 text-left transition-colors hover:bg-white/[0.04]",
                          f.severity === "error" ? "border-red-500/30 bg-red-500/[0.05]" : "border-amber-500/30 bg-amber-500/[0.05]"
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <AlertTriangle size={13} className={f.severity === "error" ? "text-red-400" : "text-amber-400"} />
                          <span className="label-eyebrow !text-[10px]">
                            {CATEGORY_LABELS[f.category] ?? f.category}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-paper-200">{f.message}</p>
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              <button onClick={handleScan} className="btn-secondary self-start !px-3 !py-1.5 text-xs">
                Re-scan
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
