import {
  MousePointer2,
  Hand,
  Square,
  Diamond,
  Circle,
  Type,
  ArrowRight,
  Waypoints,
  Pencil,
  Highlighter,
  Eraser,
  Undo2,
  Redo2,
  LogIn,
  Image as ImageIcon,
  LayoutGrid,
} from "lucide-react";
import { nanoid } from "@/lib/id";
import clsx from "clsx";
import { useCanvasStore } from "@/store/useCanvasStore";
import { useSettingsStore } from "@/store/useSettingsStore";
import type { ToolId } from "@/types";

const TOOLS: { id: ToolId; icon: typeof MousePointer2; label: string; shortcut: string }[] = [
  { id: "select", icon: MousePointer2, label: "Select", shortcut: "V" },
  { id: "pan", icon: Hand, label: "Pan", shortcut: "H" },
  { id: "rectangle", icon: Square, label: "Process", shortcut: "R" },
  { id: "diamond", icon: Diamond, label: "Decision", shortcut: "D" },
  { id: "oval", icon: Circle, label: "Start / End", shortcut: "O" },
  { id: "parallelogram", icon: LogIn, label: "Input / Output", shortcut: "P" },
  { id: "arrow", icon: ArrowRight, label: "Arrow", shortcut: "A" },
  { id: "connector", icon: Waypoints, label: "Connector", shortcut: "L" },
  { id: "text", icon: Type, label: "Text", shortcut: "T" },
  { id: "freehand", icon: Pencil, label: "Freehand", shortcut: "F" },
  { id: "highlighter", icon: Highlighter, label: "Highlighter", shortcut: "G" },
  { id: "eraser", icon: Eraser, label: "Eraser", shortcut: "E" },
];

export function Toolbar() {
  const activeTool = useCanvasStore((s) => s.activeTool);
  const setActiveTool = useCanvasStore((s) => s.setActiveTool);
  const undo = useCanvasStore((s) => s.undo);
  const redo = useCanvasStore((s) => s.redo);
  const canUndo = useCanvasStore((s) => s.past.length > 0);
  const canRedo = useCanvasStore((s) => s.future.length > 0);

  const showGrid = useSettingsStore((s) => s.showGrid);
  const setShowGrid = useSettingsStore((s) => s.setShowGrid);
  const setSnapToGrid = useSettingsStore((s) => s.setSnapToGrid);

  const navigationTools = TOOLS.slice(0, 2);
  const shapeTools = [...TOOLS.slice(2, 6), TOOLS.find(t => t.id === "text")].filter(Boolean) as typeof TOOLS;
  const connectionTools = TOOLS.slice(6, 8);
  const sketchTools = TOOLS.slice(9, 12);

  const renderToolButton = ({ id, icon: Icon, label, shortcut }: typeof TOOLS[0]) => (
    <button
      key={id}
      title={`${label} (${shortcut})`}
      onClick={() => setActiveTool(id)}
      className={clsx(
        "group relative flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-200",
        activeTool === id
          ? "bg-violet-600 text-white shadow-glow-violet scale-105"
          : "text-paper-300 hover:bg-white/[0.06] hover:text-paper-100 hover:scale-105"
      )}
    >
      <Icon size={16} strokeWidth={1.75} />
    </button>
  );

  return (
    <div className="glass-panel border-r border-white/10 absolute left-0 top-14 bottom-0 z-20 w-16 flex flex-col items-center justify-between py-3 rounded-none select-none">
      {/* Top Section: Tools Grouped */}
      <div className="flex flex-col items-center gap-2.5 w-full overflow-y-auto scrollbar-none px-2">
        {/* Section 1: Navigation */}
        <div className="flex flex-col gap-1 w-full items-center">
          {navigationTools.map(renderToolButton)}
        </div>

        <div className="w-8 h-px bg-white/10" />

        {/* Section 2: Shapes */}
        <div className="flex flex-col gap-1 w-full items-center">
          {shapeTools.map(renderToolButton)}
        </div>

        <div className="w-8 h-px bg-white/10" />

        {/* Section 3: Connectors */}
        <div className="flex flex-col gap-1 w-full items-center">
          {connectionTools.map(renderToolButton)}
        </div>

        <div className="w-8 h-px bg-white/10" />

        {/* Section 4: Sketching */}
        <div className="flex flex-col gap-1 w-full items-center">
          {sketchTools.map(renderToolButton)}
        </div>

        <div className="w-8 h-px bg-white/10" />

        {/* Section 5: Utilities */}
        <div className="flex flex-col gap-1.5 w-full items-center">
          <button
            title="Upload Image (Paste or Click)"
            onClick={() => {
              const fileInput = document.createElement("input");
              fileInput.type = "file";
              fileInput.accept = "image/*";
              fileInput.onchange = (e: any) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (event) => {
                  const base64 = event.target?.result as string;
                  if (base64) {
                    const img = new window.Image();
                    img.src = base64;
                    img.onload = () => {
                      let w = img.width;
                      let h = img.height;
                      const maxW = 400;
                      if (w > maxW) {
                        h = (maxW / w) * h;
                        w = maxW;
                      }
                      const store = useCanvasStore.getState();
                      store.addNode({
                        id: nanoid(),
                        type: "image",
                        x: 150,
                        y: 150,
                        width: w,
                        height: h,
                        text: "",
                        fill: "transparent",
                        stroke: "transparent",
                        imageUrl: base64,
                      });
                    };
                  }
                };
                reader.readAsDataURL(file);
              };
              fileInput.click();
            }}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-paper-300 transition-all duration-200 hover:bg-white/[0.06] hover:text-paper-100 hover:scale-105"
          >
            <ImageIcon size={16} strokeWidth={1.75} />
          </button>

          <button
            title={showGrid ? "Hide Grid Background" : "Show Grid Background"}
            onClick={() => {
              setShowGrid(!showGrid);
              setSnapToGrid(!showGrid);
            }}
            className={clsx(
              "flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-200 hover:scale-105",
              showGrid
                ? "bg-violet-500/20 text-violet-300 border border-violet-500/30"
                : "text-paper-300 hover:bg-white/[0.06] hover:text-paper-100"
            )}
          >
            <LayoutGrid size={16} strokeWidth={1.75} />
          </button>
        </div>
      </div>

      {/* Bottom Section: Actions */}
      <div className="flex flex-col items-center gap-1 w-full px-2">
        <div className="w-8 h-px bg-white/10 mb-1" />
        <button
          title="Undo (Ctrl+Z)"
          onClick={undo}
          disabled={!canUndo}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-paper-300 transition-all duration-200 hover:bg-white/[0.06] hover:text-paper-100 disabled:opacity-30 disabled:hover:bg-transparent"
        >
          <Undo2 size={16} strokeWidth={1.75} />
        </button>
        <button
          title="Redo (Ctrl+Shift+Z)"
          onClick={redo}
          disabled={!canRedo}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-paper-300 transition-all duration-200 hover:bg-white/[0.06] hover:text-paper-100 disabled:opacity-30 disabled:hover:bg-transparent"
        >
          <Redo2 size={16} strokeWidth={1.75} />
        </button>
      </div>
    </div>
  );
}
