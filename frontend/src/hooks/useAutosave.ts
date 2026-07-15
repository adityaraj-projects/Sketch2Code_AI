import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/api/client";
import { useCanvasStore } from "@/store/useCanvasStore";
import { useSettingsStore } from "@/store/useSettingsStore";

export type SaveStatus = "idle" | "saving" | "saved" | "error";

/**
 * Watches the canvas store for changes and pushes a debounced PUT to the
 * backend, using the interval from Settings (or skipping auto-save
 * entirely in "manual" mode — in which case `saveNow` is the only way
 * changes reach the server). Also does a best-effort synchronous save on
 * tab close so a mid-edit refresh doesn't lose work.
 */
export function useAutosave() {
  const [status, setStatus] = useState<SaveStatus>("idle");
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const projectId = useCanvasStore((s) => s.projectId);
  const isDirty = useCanvasStore((s) => s.isDirty);
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const strokes = useCanvasStore((s) => s.strokes);
  const autosaveInterval = useSettingsStore((s) => s.autosaveInterval);

  const saveNow = useCallback(async () => {
    const state = useCanvasStore.getState();
    if (!state.projectId) return;
    setStatus("saving");
    try {
      const canvas_data = state.serialize();
      await api.put(`/projects/${state.projectId}/autosave`, { canvas_data });
      useCanvasStore.getState().markSaved();
      setStatus("saved");
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    if (!projectId || !isDirty) return;
    if (autosaveInterval === "manual") return;

    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(saveNow, autosaveInterval);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, isDirty, nodes, edges, strokes, autosaveInterval]);

  useEffect(() => {
    const handler = () => {
      const state = useCanvasStore.getState();
      if (state.projectId && state.isDirty) {
        navigator.sendBeacon?.(
          `/api/projects/${state.projectId}/autosave`,
          new Blob([JSON.stringify({ canvas_data: state.serialize() })], {
            type: "application/json",
          })
        );
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, []);

  return { status, saveNow };
}
