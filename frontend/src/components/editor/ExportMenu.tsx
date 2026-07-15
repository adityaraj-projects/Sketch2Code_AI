import { useState } from "react";
import { createPortal } from "react-dom";
import type Konva from "konva";
import { Download, Image as ImageIcon, FileCode, FileText, Braces, Loader2, ChevronDown } from "lucide-react";
import { useCanvasStore } from "@/store/useCanvasStore";
import { computeContentBoundingBox } from "@/lib/export/boundingBox";
import { canvasToSvgString } from "@/lib/export/svgExport";
import { buildProjectExportJson } from "@/lib/export/jsonExport";

interface Props {
  stageRef: React.RefObject<Konva.Stage>;
  onOpenCodeGen: () => void;
}

function downloadBlob(content: string | Blob, filename: string, mimeType?: string) {
  const blob = typeof content === "string" ? new Blob([content], { type: mimeType }) : content;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function fileBaseName(projectName: string): string {
  return projectName.trim().replace(/\s+/g, "_").toLowerCase() || "flowchart";
}

export function ExportMenu({ stageRef, onOpenCodeGen }: Props) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const strokes = useCanvasStore((s) => s.strokes);
  const viewport = useCanvasStore((s) => s.viewport);
  const projectName = useCanvasStore((s) => s.projectName);

  function screenBoxFromWorldBox() {
    const worldBox = computeContentBoundingBox(nodes, strokes);
    if (!worldBox) return null;
    const toScreen = (x: number, y: number) => ({
      x: x * viewport.zoom + viewport.x,
      y: y * viewport.zoom + viewport.y,
    });
    const topLeft = toScreen(worldBox.minX, worldBox.minY);
    const bottomRight = toScreen(worldBox.maxX, worldBox.maxY);
    return {
      x: topLeft.x,
      y: topLeft.y,
      width: bottomRight.x - topLeft.x,
      height: bottomRight.y - topLeft.y,
    };
  }

  async function handleExportPng() {
    if (!stageRef.current) return;
    setBusy("png");
    try {
      const box = screenBoxFromWorldBox();
      const stage = stageRef.current;
      const dataUrl = box
        ? stage.toDataURL({ ...box, pixelRatio: 2 })
        : stage.toDataURL({ pixelRatio: 2 });
      const res = await fetch(dataUrl);
      const blob = await res.blob();
      downloadBlob(blob, `${fileBaseName(projectName)}.png`);
    } finally {
      setBusy(null);
      setOpen(false);
    }
  }

  function handleExportSvg() {
    setBusy("svg");
    try {
      const svg = canvasToSvgString(nodes, edges, strokes);
      downloadBlob(svg, `${fileBaseName(projectName)}.svg`, "image/svg+xml");
    } finally {
      setBusy(null);
      setOpen(false);
    }
  }

  async function handleExportPdf() {
    if (!stageRef.current) return;
    setBusy("pdf");
    try {
      const { jsPDF } = await import("jspdf");
      const box = screenBoxFromWorldBox();
      const stage = stageRef.current;
      const dataUrl = box
        ? stage.toDataURL({ ...box, pixelRatio: 2 })
        : stage.toDataURL({ pixelRatio: 2 });

      const img = new window.Image();
      img.src = dataUrl;
      await new Promise((resolve) => (img.onload = resolve));

      const orientation = img.width >= img.height ? "landscape" : "portrait";
      const pdf = new jsPDF({ orientation, unit: "pt", format: [img.width, img.height] });
      pdf.addImage(dataUrl, "PNG", 0, 0, img.width, img.height);
      pdf.save(`${fileBaseName(projectName)}.pdf`);
    } finally {
      setBusy(null);
      setOpen(false);
    }
  }

  function handleExportJson() {
    setBusy("json");
    try {
      const json = buildProjectExportJson(projectName, { nodes, edges, strokes, viewport });
      downloadBlob(JSON.stringify(json, null, 2), `${fileBaseName(projectName)}.json`, "application/json");
    } finally {
      setBusy(null);
      setOpen(false);
    }
  }

  function canvasToMermaidString(nodesList: any[], edgesList: any[]): string {
    let mermaid = "graph TD\n";
    nodesList.forEach((n) => {
      const label = (n.text || "").replace(/"/g, '\\"');
      let shapeStart = "[";
      let shapeEnd = "]";
      if (n.type === "start" || n.type === "end" || n.type === "connector") {
        shapeStart = "([";
        shapeEnd = "])";
      } else if (n.type === "decision") {
        shapeStart = "{";
        shapeEnd = "}";
      } else if (n.type === "input" || n.type === "output") {
        shapeStart = "[/";
        shapeEnd = "/]";
      }
      mermaid += `  ${n.id}${shapeStart}"${label}"${shapeEnd}\n`;
    });
    edgesList.forEach((e) => {
      if (e.label) {
        mermaid += `  ${e.fromNodeId} -- "${e.label}" --> ${e.toNodeId}\n`;
      } else {
        mermaid += `  ${e.fromNodeId} --> ${e.toNodeId}\n`;
      }
    });
    return mermaid;
  }

  function handleExportMermaid() {
    setBusy("mermaid");
    try {
      const mermaid = canvasToMermaidString(nodes, edges);
      downloadBlob(mermaid, `${fileBaseName(projectName)}.mmd`, "text/plain");
    } finally {
      setBusy(null);
      setOpen(false);
    }
  }

  const OPTIONS = [
    { id: "png", label: "PNG Image", icon: ImageIcon, action: handleExportPng },
    { id: "svg", label: "SVG (Vector)", icon: FileCode, action: handleExportSvg },
    { id: "pdf", label: "PDF Document", icon: FileText, action: handleExportPdf },
    { id: "json", label: "Project JSON", icon: Braces, action: handleExportJson },
    { id: "mermaid", label: "Mermaid.js Code", icon: FileCode, action: handleExportMermaid },
  ];

  return (
    <div className="relative">
      <button id="btn-export-trigger" onClick={() => setOpen((v) => !v)} className="btn-secondary !px-3 !py-1.5 text-xs">
        <Download size={14} /> Export <ChevronDown size={12} />
      </button>

      {open && createPortal(
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="glass-panel fixed left-28 top-16 z-50 w-52 overflow-hidden rounded-xl py-1 bg-ink-900 border border-white/10 shadow-2xl">
            {OPTIONS.map(({ id, label, icon: Icon, action }) => (
              <button
                key={id}
                onClick={action}
                disabled={busy !== null}
                className="flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm text-paper-200 hover:bg-white/[0.06] disabled:opacity-50"
              >
                {busy === id ? <Loader2 size={15} className="animate-spin" /> : <Icon size={15} className="text-violet-400" />}
                {label}
              </button>
            ))}
            <div className="my-1 h-px bg-white/10" />
            <button
              onClick={() => {
                setOpen(false);
                onOpenCodeGen();
              }}
              className="flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm text-paper-200 hover:bg-white/[0.06]"
            >
              <FileCode size={15} className="text-mint-400" />
              Source Code…
            </button>
          </div>
        </>,
        document.body
      )}
    </div>
  );
}
