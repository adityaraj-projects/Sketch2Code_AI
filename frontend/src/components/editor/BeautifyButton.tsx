import { useState } from "react";
import { Wand2, Loader2 } from "lucide-react";
import { useCanvasStore } from "@/store/useCanvasStore";
import { beautifyFlowchart } from "@/api/beautifier";

export function BeautifyButton() {
  const [busy, setBusy] = useState(false);
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const replaceNodesAndEdges = useCanvasStore((s) => s.replaceNodesAndEdges);

  async function handleBeautify() {
    if (nodes.length === 0) return;
    const hasStart = nodes.some((n) => n.type === "start");
    if (!hasStart) {
      window.alert("Add a Start shape before beautifying — the layout is rebuilt from your flowchart's structure.");
      return;
    }
    if (!window.confirm("This re-arranges every shape into a clean layout based on your flowchart's logic. Undo (Ctrl+Z) works afterward if you don't like it. Continue?")) {
      return;
    }

    setBusy(true);
    try {
      const result = await beautifyFlowchart(nodes, edges);
      replaceNodesAndEdges(result.nodes, result.edges);
      if (result.warnings.length > 0) {
        window.alert(`Beautified, with a few notes:\n\n${result.warnings.join("\n")}`);
      }
    } catch (err: any) {
      window.alert(err?.response?.data?.detail ?? "Couldn't beautify this flowchart. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <button id="btn-beautify-trigger" onClick={handleBeautify} disabled={busy} className="btn-secondary !px-3 !py-1.5 text-xs">
      {busy ? <Loader2 size={14} className="animate-spin" /> : <Wand2 size={14} />}
      Beautify
    </button>
  );
}
