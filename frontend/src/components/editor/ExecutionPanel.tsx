import { useEffect, useRef, useState } from "react";
import {
  X, Play, Pause, SkipBack, SkipForward, RotateCcw, Loader2, AlertTriangle, PlayCircle,
} from "lucide-react";
import { useCanvasStore } from "@/store/useCanvasStore";
import { runExecution, type ExecutionResponse } from "@/api/execution";

interface Props {
  open: boolean;
  onClose: () => void;
}

const PLAY_INTERVAL_MS = 700;

export function ExecutionPanel({ open, onClose }: Props) {
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const setExecutingNodeId = useCanvasStore((s) => s.setExecutingNodeId);

  const [inputValuesText, setInputValuesText] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [trace, setTrace] = useState<ExecutionResponse | null>(null);
  const [stepIndex, setStepIndex] = useState(-1); // -1 = not started
  const [isPlaying, setIsPlaying] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    if (!open) {
      setIsPlaying(false);
      setExecutingNodeId(null);
    }
  }, [open, setExecutingNodeId]);

  useEffect(() => {
    if (trace && stepIndex >= 0 && stepIndex < trace.steps.length) {
      setExecutingNodeId(trace.steps[stepIndex].node_id);
    }
  }, [stepIndex, trace, setExecutingNodeId]);

  useEffect(() => {
    if (isPlaying && trace) {
      intervalRef.current = setInterval(() => {
        setStepIndex((i) => {
          if (i + 1 >= trace.steps.length) {
            setIsPlaying(false);
            return i;
          }
          return i + 1;
        });
      }, PLAY_INTERVAL_MS);
      return () => clearInterval(intervalRef.current);
    }
  }, [isPlaying, trace]);

  async function handleRun() {
    const hasStart = nodes.some((n) => n.type === "start");
    if (!hasStart) {
      setStatus("error");
      setErrorMessage("Add a Start shape before running the simulator.");
      return;
    }
    setStatus("loading");
    setErrorMessage(null);
    setIsPlaying(false);

    const inputValues = inputValuesText
      .split(/[,\n]/)
      .map((v) => v.trim())
      .filter((v) => v.length > 0);

    try {
      const result = await runExecution(nodes, edges, inputValues);
      setTrace(result);
      setStepIndex(-1);
      setStatus("ready");
    } catch (err: any) {
      setStatus("error");
      setErrorMessage(err?.response?.data?.detail ?? "Couldn't run the simulator. Please try again.");
    }
  }

  function handleReset() {
    setIsPlaying(false);
    setStepIndex(-1);
    setExecutingNodeId(null);
  }

  function stepForward() {
    if (!trace) return;
    setStepIndex((i) => Math.min(i + 1, trace.steps.length - 1));
  }

  function stepBack() {
    setStepIndex((i) => Math.max(i - 1, -1));
    if (stepIndex - 1 < 0) setExecutingNodeId(null);
  }

  if (!open) return null;

  const currentStep = trace && stepIndex >= 0 ? trace.steps[stepIndex] : null;
  const visibleConsole = currentStep
    ? trace!.steps.slice(0, stepIndex + 1).filter((s) => s.output !== null).map((s) => s.output as string)
    : [];
  const atEnd = trace ? stepIndex >= trace.steps.length - 1 : false;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <div
        className="glass-panel flex h-full w-full max-w-md flex-col border-l border-white/10"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
          <div className="flex items-center gap-2">
            <PlayCircle size={18} className="text-mint-400" />
            <h2 className="font-display text-base font-medium text-paper-100">Execution Simulator</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-paper-100">
            <X size={18} />
          </button>
        </div>

        <div className="border-b border-white/[0.06] px-5 py-4">
          <label className="mb-1.5 block text-xs text-paper-500">
            Input values (comma or newline separated, used in the order your flowchart reads them)
          </label>
          <textarea
            value={inputValuesText}
            onChange={(e) => setInputValuesText(e.target.value)}
            placeholder="e.g. 7, 3"
            className="h-14 w-full resize-none rounded-lg border border-white/10 bg-ink-950 p-2.5 font-mono text-xs text-paper-100 placeholder:text-paper-500 outline-none focus:border-violet-500"
          />
          <button onClick={handleRun} disabled={status === "loading"} className="btn-primary mt-3 w-full !py-2 text-sm">
            {status === "loading" ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
            Run
          </button>
        </div>

        {status === "error" && (
          <div className="mx-5 mt-4 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
            <AlertTriangle size={14} className="mt-0.5 shrink-0" />
            {errorMessage}
          </div>
        )}

        {trace && (
          <>
            {trace.status !== "completed" && stepIndex >= trace.steps.length - 1 && (
              <div className="mx-5 mt-4 flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-300">
                <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                {trace.error_message}
              </div>
            )}

            <div className="flex-1 overflow-auto px-5 py-4">
              <div className="mb-4">
                <span className="label-eyebrow">Current step</span>
                <p className="mt-1.5 rounded-lg border border-white/10 bg-ink-950 px-3 py-2 font-mono text-sm text-paper-100">
                  {currentStep ? currentStep.label : "Not started — press play or step forward"}
                </p>
              </div>

              <div className="mb-4">
                <span className="label-eyebrow">Variables</span>
                <div className="mt-1.5 overflow-hidden rounded-lg border border-white/10">
                  {currentStep && Object.keys(currentStep.variables).length > 0 ? (
                    <table className="w-full text-left text-xs">
                      <tbody>
                        {Object.entries(currentStep.variables).map(([name, value]) => (
                          <tr key={name} className="border-b border-white/[0.06] last:border-0">
                            <td className="px-3 py-1.5 font-mono text-violet-300">{name}</td>
                            <td className="px-3 py-1.5 font-mono text-paper-100">{JSON.stringify(value)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="px-3 py-2 text-xs text-paper-500">No variables yet</p>
                  )}
                </div>
              </div>

              <div>
                <span className="label-eyebrow">Console output</span>
                <div className="mt-1.5 h-24 overflow-auto rounded-lg border border-white/10 bg-ink-950 p-2.5 font-mono text-xs text-mint-400">
                  {visibleConsole.length > 0 ? visibleConsole.map((line, i) => <div key={i}>{line}</div>) : (
                    <span className="text-paper-500">(no output yet)</span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-center gap-2 border-t border-white/[0.06] px-5 py-3">
              <button onClick={handleReset} title="Reset" className="rounded-lg p-2 text-paper-300 hover:bg-white/[0.06]">
                <RotateCcw size={16} />
              </button>
              <button onClick={stepBack} disabled={stepIndex < 0} title="Step back" className="rounded-lg p-2 text-paper-300 hover:bg-white/[0.06] disabled:opacity-30">
                <SkipBack size={16} />
              </button>
              <button
                onClick={() => setIsPlaying((p) => !p)}
                disabled={atEnd && !isPlaying}
                className="btn-primary !px-4 !py-2"
              >
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              </button>
              <button onClick={stepForward} disabled={atEnd} title="Step forward" className="rounded-lg p-2 text-paper-300 hover:bg-white/[0.06] disabled:opacity-30">
                <SkipForward size={16} />
              </button>
              <span className="ml-2 font-mono text-xs text-paper-500">
                {stepIndex + 1} / {trace.steps.length}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
