import { useState } from "react";
import type Konva from "konva";
import { Wand2, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";
import { useCanvasStore } from "@/store/useCanvasStore";
import { recognizeFlowchart } from "@/api/recognition";

interface Props {
  stageRef: React.RefObject<Konva.Stage>;
}

const PIXEL_RATIO = 2;

export function RecognizeButton({ stageRef }: Props) {
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);
  const strokes = useCanvasStore((s) => s.strokes);
  const viewport = useCanvasStore((s) => s.viewport);
  const applyRecognitionResult = useCanvasStore((s) => s.applyRecognitionResult);

  const penStrokes = strokes.filter((s) => s.tool === "pen");

  async function handleRecognize() {
    if (penStrokes.length === 0 || !stageRef.current) return;
    setStatus("loading");
    setMessage(null);

    try {
      const dataUrl = stageRef.current.toDataURL({ pixelRatio: PIXEL_RATIO });
      const result = await recognizeFlowchart(penStrokes, {
        dataUrl,
        viewport,
        pixelRatio: PIXEL_RATIO,
      });

      if (result.nodes.length === 0) {
        setStatus("error");
        setMessage("Couldn't recognize any flowchart symbols in the sketch yet.");
        return;
      }

      applyRecognitionResult(result.nodes, result.edges, result.consumed_stroke_ids);
      setStatus("done");
      setMessage(
        result.ocr_warning ??
          `Recognized ${result.nodes.length} shape${result.nodes.length === 1 ? "" : "s"} and ${result.edges.length} connector${result.edges.length === 1 ? "" : "s"}.`
      );
    } catch (err: any) {
      setStatus("error");
      const rawDetail = err?.response?.data?.detail ?? err?.message ?? "";
      if (rawDetail.toLowerCase().includes("429") || rawDetail.toLowerCase().includes("quota")) {
        setMessage("Gemini AI API rate limit reached (Quota Exceeded). Please wait a minute and click Recognize Sketch again!");
      } else {
        setMessage(rawDetail || "Recognition failed. Please try again.");
      }
    } finally {
      setTimeout(() => setStatus((s) => (s === "loading" ? "idle" : s)), 0);
      setTimeout(() => setMessage(null), 5000);
    }
  }

  return (
    <div className="relative flex flex-col items-center">
      <button
        id="btn-recognize-trigger"
        onClick={handleRecognize}
        disabled={penStrokes.length === 0 || status === "loading"}
        className="btn-secondary !px-3 !py-1.5 text-xs flex items-center gap-1.5 disabled:opacity-40"
      >
        {status === "loading" ? (
          <Loader2 size={14} className="animate-spin text-violet-400" />
        ) : (
          <Wand2 size={14} className="text-violet-400" />
        )}
        Recognize Sketch
      </button>

      {message && (
        <div
          className={`glass-panel absolute top-full right-0 z-40 mt-2 flex w-64 items-start gap-2 rounded-xl p-3 text-xs shadow-glass border border-white/10 ${
            status === "error" ? "bg-red-950/90 text-amber-300 border-red-500/20" : "bg-ink-900/90 text-mint-400 border-mint-500/20"
          }`}
        >
          {status === "error" ? (
            <AlertTriangle size={14} className="mt-0.5 shrink-0 text-amber-400" />
          ) : (
            <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-mint-400" />
          )}
          <span>{message}</span>
        </div>
      )}
    </div>
  );
}
