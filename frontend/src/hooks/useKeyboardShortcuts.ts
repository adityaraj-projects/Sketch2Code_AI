import { useEffect } from "react";
import { useCanvasStore } from "@/store/useCanvasStore";
import type { ToolId } from "@/types";

const TOOL_SHORTCUTS: Record<string, ToolId> = {
  v: "select",
  h: "pan",
  r: "rectangle",
  d: "diamond",
  o: "oval",
  p: "parallelogram",
  a: "arrow",
  l: "connector",
  t: "text",
  f: "freehand",
  g: "highlighter",
  e: "eraser",
};

export function useKeyboardShortcuts() {
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement;
      const isTyping = ["INPUT", "TEXTAREA"].includes(target.tagName) || target.isContentEditable;
      if (isTyping) return;

      const store = useCanvasStore.getState();
      const isMeta = e.metaKey || e.ctrlKey;

      if (isMeta && e.key.toLowerCase() === "z" && !e.shiftKey) {
        e.preventDefault();
        store.undo();
        return;
      }
      if (isMeta && (e.key.toLowerCase() === "y" || (e.key.toLowerCase() === "z" && e.shiftKey))) {
        e.preventDefault();
        store.redo();
        return;
      }
      if (isMeta && e.key.toLowerCase() === "c") {
        store.copySelection();
        return;
      }
      if (isMeta && e.key.toLowerCase() === "v") {
        store.pasteClipboard();
        return;
      }
      if (isMeta && e.key.toLowerCase() === "a") {
        e.preventDefault();
        const allIds = [
          ...store.nodes.map((n) => n.id),
          ...store.edges.map((e) => e.id),
          ...store.strokes.map((s) => s.id),
        ];
        store.setSelectedIds(allIds);
        return;
      }
      if (e.key === "Backspace" || e.key === "Delete") {
        store.deleteSelected();
        return;
      }
      if (e.key === "Escape") {
        store.setSelectedIds([]);
        store.setActiveTool("select");
        return;
      }
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) {
        const selectedNodeIds = store.selectedIds.filter((id) =>
          store.nodes.some((n) => n.id === id)
        );
        if (selectedNodeIds.length > 0) {
          e.preventDefault();
          const dx = e.key === "ArrowLeft" ? -5 : e.key === "ArrowRight" ? 5 : 0;
          const dy = e.key === "ArrowUp" ? -5 : e.key === "ArrowDown" ? 5 : 0;
          const multiplier = e.shiftKey ? 3 : 1;
          selectedNodeIds.forEach((id) => {
            const node = store.nodes.find((n) => n.id === id);
            if (node) {
              store.updateNode(id, { x: node.x + dx * multiplier, y: node.y + dy * multiplier });
            }
          });
          return;
        }
      }

      const tool = TOOL_SHORTCUTS[e.key.toLowerCase()];
      if (tool) {
        store.setActiveTool(tool);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
}
