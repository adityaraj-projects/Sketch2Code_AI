import { useState } from "react";
import { X, Mic, Square, Loader2, AlertTriangle, Sparkles, Plus } from "lucide-react";
import { useCanvasStore } from "@/store/useCanvasStore";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";
import { generateFlowchartFromSpeech } from "@/api/voicemode";

interface Props {
  open: boolean;
  onClose: () => void;
}

const EXAMPLES = [
  "Create a flowchart that checks if a number is even or odd",
  "Draw a login flowchart that checks username and password",
  "Make a flowchart to find the largest of three numbers",
];

export function VoiceModePanel({ open, onClose }: Props) {
  const { isSupported, isListening, transcript, error: micError, start, stop, setTranscript } = useSpeechRecognition();
  const loadGeneratedFlowchart = useCanvasStore((s) => s.loadGeneratedFlowchart);

  const [status, setStatus] = useState<"idle" | "generating" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [added, setAdded] = useState(false);

  async function handleGenerate(description: string) {
    if (!description.trim()) return;
    setStatus("generating");
    setErrorMessage(null);
    setGeneratedCode(null);
    setAdded(false);
    try {
      const result = await generateFlowchartFromSpeech(description);
      if (!result.success) {
        setStatus("error");
        setErrorMessage(result.error_message ?? "Couldn't generate a flowchart from that.");
        return;
      }
      loadGeneratedFlowchart(result.nodes, result.edges);
      setWarnings(result.warnings);
      setGeneratedCode(result.generated_code);
      setAdded(true);
      setStatus("idle");
    } catch (err: any) {
      setStatus("error");
      setErrorMessage(err?.response?.data?.detail ?? "Couldn't generate a flowchart. Please try again.");
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="glass-panel flex max-h-[85vh] w-full max-w-lg flex-col rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
          <div className="flex items-center gap-2">
            <Mic size={18} className="text-violet-400" />
            <h2 className="font-display text-base font-medium text-paper-100">Voice Mode</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-paper-100">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-auto px-5 py-6">
          {!isSupported ? (
            <div className="flex flex-col items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-5 text-center">
              <AlertTriangle size={20} className="text-amber-400" />
              <p className="text-sm text-paper-200">
                Voice input isn't supported in this browser — try Chrome or Edge on desktop or Android.
              </p>
              <p className="text-xs text-paper-500">
                You can still type a description below and generate a flowchart from it.
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 py-2">
              <button
                onClick={isListening ? stop : start}
                className={`flex h-16 w-16 items-center justify-center rounded-full transition-all ${
                  isListening ? "bg-red-500 shadow-[0_0_0_8px_rgba(239,68,68,0.15)]" : "bg-violet-500 hover:bg-violet-600"
                }`}
              >
                {isListening ? <Square size={22} className="text-white" /> : <Mic size={24} className="text-white" />}
              </button>
              <p className="text-xs text-paper-500">{isListening ? "Listening… tap to stop" : "Tap to speak"}</p>
            </div>
          )}

          {micError && (
            <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              {micError}
            </div>
          )}

          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Your spoken (or typed) description appears here…"
            className="mt-4 h-20 w-full resize-none rounded-xl border border-white/10 bg-ink-950 p-3 text-sm text-paper-100 placeholder:text-paper-500 outline-none focus:border-violet-500"
          />

          <div className="mt-3 flex flex-wrap gap-1.5">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                onClick={() => setTranscript(ex)}
                className="rounded-full border border-white/10 px-2.5 py-1 text-[11px] text-paper-400 hover:bg-white/[0.05]"
              >
                {ex}
              </button>
            ))}
          </div>

          <button
            onClick={() => handleGenerate(transcript)}
            disabled={!transcript.trim() || status === "generating"}
            className="btn-primary mt-4 w-full !py-2.5"
          >
            {status === "generating" ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            Generate Flowchart
          </button>

          {status === "error" && (
            <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              {errorMessage}
            </div>
          )}

          {added && (
            <div className="mt-3 flex items-start gap-2 rounded-lg border border-mint-400/30 bg-mint-400/10 px-3 py-2 text-sm text-mint-400">
              <Plus size={14} className="mt-0.5 shrink-0" />
              Added to your canvas, below any existing content.
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

          {generatedCode && (
            <details className="mt-4">
              <summary className="cursor-pointer text-xs text-paper-500 hover:text-paper-300">
                Show the code this was generated from
              </summary>
              <pre className="mt-2 overflow-auto rounded-lg border border-white/10 bg-ink-950 p-3 font-mono text-xs text-paper-300">
                {generatedCode}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}
