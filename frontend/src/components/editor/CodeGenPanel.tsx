import { useEffect, useState } from "react";
import { X, Copy, Download, Loader2, AlertTriangle, Check, Code2 } from "lucide-react";
import clsx from "clsx";
import { useCanvasStore } from "@/store/useCanvasStore";
import { generateCodeFromFlowchart } from "@/api/codegen";
import { LANGUAGE_LABELS, LANGUAGE_ORDER } from "@/lib/languages";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function CodeGenPanel({ open, onClose }: Props) {
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const projectName = useCanvasStore((s) => s.projectName);

  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");
  const [fileExtension, setFileExtension] = useState("py");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function runGeneration(lang: string) {
    const hasStart = nodes.some((n) => n.type === "start");
    if (!hasStart) {
      setStatus("error");
      setErrorMessage("Add a Start shape to your flowchart before generating code.");
      setCode("");
      return;
    }

    setStatus("loading");
    setErrorMessage(null);
    try {
      const result = await generateCodeFromFlowchart(nodes, edges, lang);
      setCode(result.code);
      setFileExtension(result.file_extension);
      setWarnings(result.warnings);
      setStatus("idle");
    } catch (err: any) {
      setStatus("error");
      setErrorMessage(err?.response?.data?.detail ?? "Couldn't generate code. Please try again.");
    }
  }

  useEffect(() => {
    if (open) runGeneration(language);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function handleLanguageChange(lang: string) {
    setLanguage(lang);
    runGeneration(lang);
  }

  function handleCopy() {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  function handleDownload() {
    const blob = new Blob([code], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${projectName.replace(/\s+/g, "_").toLowerCase()}.${fileExtension}`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <div
        className="glass-panel flex h-full w-full max-w-2xl flex-col border-l border-white/10"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
          <div className="flex items-center gap-2">
            <Code2 size={18} className="text-violet-400" />
            <h2 className="font-display text-base font-medium text-paper-100">Generated Code</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-paper-100">
            <X size={18} />
          </button>
        </div>

        <div className="flex flex-wrap gap-1.5 border-b border-white/[0.06] px-5 py-3">
          {LANGUAGE_ORDER.map((lang) => (
            <button
              key={lang}
              onClick={() => handleLanguageChange(lang)}
              className={clsx(
                "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                language === lang
                  ? "bg-violet-500 text-white"
                  : "bg-white/[0.04] text-paper-300 hover:bg-white/[0.08] hover:text-paper-100"
              )}
            >
              {LANGUAGE_LABELS[lang]}
            </button>
          ))}
        </div>

        {warnings.length > 0 && status !== "error" && (
          <div className="flex flex-col gap-1.5 border-b border-white/[0.06] bg-amber-500/[0.06] px-5 py-3">
            {warnings.map((w, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-amber-300">
                <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                {w}
              </div>
            ))}
          </div>
        )}

        <div className="relative flex-1 overflow-auto">
          {status === "loading" && (
            <div className="flex h-full items-center justify-center">
              <Loader2 size={22} className="animate-spin text-violet-400" />
            </div>
          )}
          {status === "error" && (
            <div className="flex h-full flex-col items-center justify-center gap-2 px-8 text-center">
              <AlertTriangle size={22} className="text-amber-400" />
              <p className="text-sm text-paper-300">{errorMessage}</p>
            </div>
          )}
          {status === "idle" && code && (
            <pre className="h-full overflow-auto p-5 font-mono text-[13px] leading-relaxed text-paper-200">
              {code.split("\n").map((line, i) => (
                <div key={i} className="flex">
                  <span className="mr-4 w-6 shrink-0 select-none text-right text-paper-500">{i + 1}</span>
                  <span className="whitespace-pre">{line}</span>
                </div>
              ))}
            </pre>
          )}
        </div>

        {status === "idle" && code && (
          <div className="flex items-center justify-end gap-2 border-t border-white/[0.06] px-5 py-3">
            <button onClick={handleCopy} className="btn-secondary !px-3 !py-1.5 text-xs">
              {copied ? <Check size={14} className="text-mint-400" /> : <Copy size={14} />}
              {copied ? "Copied" : "Copy"}
            </button>
            <button onClick={handleDownload} className="btn-primary !px-3 !py-1.5 text-xs">
              <Download size={14} /> Download
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
