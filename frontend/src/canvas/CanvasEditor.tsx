import { useCallback, useRef, useState, useEffect } from "react";
import clsx from "clsx";
import { Stage, Layer, Rect, Transformer, Group } from "react-konva";
import type Konva from "konva";
import { useCanvasStore } from "@/store/useCanvasStore";
import { useSettingsStore } from "@/store/useSettingsStore";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { NodeShape } from "@/canvas/shapes/NodeShape";
import { EdgeShape } from "@/canvas/shapes/EdgeShape";
import { StrokeShape } from "@/canvas/shapes/StrokeShape";
import { Toolbar } from "@/canvas/Toolbar";
import { MiniMap } from "@/canvas/MiniMap";
import { PresenceBar, RemoteCursorsOverlay } from "@/components/editor/PresenceLayer";
import type { Participant, RemoteCursor } from "@/hooks/useCollaboration";
import { nanoid } from "@/lib/id";
import type { FlowNode, NodeType, FreehandStroke } from "@/types";

const DEFAULT_SIZE: Record<string, { w: number; h: number }> = {
  rectangle: { w: 160, h: 72 },
  diamond: { w: 160, h: 100 },
  oval: { w: 140, h: 64 },
  parallelogram: { w: 160, h: 72 },
  text: { w: 160, h: 40 },
};

const NODE_TYPE_MAP: Record<string, NodeType> = {
  rectangle: "process",
  diamond: "decision",
  oval: "start",
  parallelogram: "input",
  text: "text",
};

const MIN_ZOOM = 0.15;
const MAX_ZOOM = 3;

export function CanvasEditor({
  externalStageRef,
  remoteCursors,
  participants,
  isConnected,
  onCursorMove,
  viewOnly = false,
}: {
  externalStageRef?: React.RefObject<Konva.Stage>;
  remoteCursors?: Record<string, RemoteCursor>;
  participants?: Participant[];
  isConnected?: boolean;
  onCursorMove?: (x: number, y: number) => void;
  viewOnly?: boolean;
} = {}) {
  useKeyboardShortcuts();

  const internalStageRef = useRef<Konva.Stage>(null);
  const stageRef = externalStageRef ?? internalStageRef;
  const transformerRef = useRef<Konva.Transformer>(null);
  const isDrawingStroke = useRef(false);
  const currentStrokePoints = useRef<number[]>([]);
  const currentStrokePressures = useRef<number[]>([]);
  const currentStrokeId = useRef<string>("");
  const drawStart = useRef<{ x: number; y: number } | null>(null);
  const [previewRect, setPreviewRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  const [connectingFromId, setConnectingFromId] = useState<string | null>(null);
  const [activeStroke, setActiveStroke] = useState<FreehandStroke | null>(null);
  const [penColor, setPenColor] = useState<string>("default");
  const [penWidth, setPenWidth] = useState<number>(3);
  const [eraserWidth, setEraserWidth] = useState<number>(22);
  const snapToGrid = useSettingsStore((s) => s.snapToGrid);
  const gridSize = useSettingsStore((s) => s.gridSize);
  const showGrid = useSettingsStore((s) => s.showGrid);
  const theme = useSettingsStore((s) => s.theme);

  const defaultPenColor =
    theme === "light"
      ? "#1E293B"
      : theme === "chalkboard"
      ? "#FFFFFF"
      : "#EDEBE6";

  const snap = useCallback(
    (value: number) => (snapToGrid ? Math.round(value / gridSize) * gridSize : value),
    [snapToGrid, gridSize]
  );

  const {
    nodes,
    edges,
    strokes,
    viewport,
    activeTool,
    selectedIds,
    executingNodeId,
    setViewport,
    setSelectedIds,
    addNode,
    updateNode,
    addEdge,
    updateEdge,
    addStroke,
    setActiveTool,
  } = useCanvasStore();

  const toWorld = useCallback(
    (pos: { x: number; y: number }) => ({
      x: (pos.x - viewport.x) / viewport.zoom,
      y: (pos.y - viewport.y) / viewport.zoom,
    }),
    [viewport]
  );

  const handleWheel = (e: Konva.KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();
    const stage = stageRef.current;
    if (!stage) return;
    const pointer = stage.getPointerPosition();
    if (!pointer) return;

    const scaleBy = 1.05;
    const oldZoom = viewport.zoom;
    const direction = e.evt.deltaY > 0 ? -1 : 1;
    const newZoom = Math.min(
      MAX_ZOOM,
      Math.max(MIN_ZOOM, direction > 0 ? oldZoom * scaleBy : oldZoom / scaleBy)
    );

    const worldPoint = {
      x: (pointer.x - viewport.x) / oldZoom,
      y: (pointer.y - viewport.y) / oldZoom,
    };

    setViewport({
      zoom: newZoom,
      x: pointer.x - worldPoint.x * newZoom,
      y: pointer.y - worldPoint.y * newZoom,
    });
  };

  useEffect(() => {
    function handleGlobalPaste(e: ClipboardEvent) {
      if (viewOnly) return;
      const items = e.clipboardData?.items;
      if (!items) return;
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.indexOf("image") !== -1) {
          const file = item.getAsFile();
          if (!file) continue;
          const reader = new FileReader();
          reader.onload = (event) => {
            const base64 = event.target?.result as string;
            if (base64) {
              const stage = stageRef.current;
              let x = 200;
              let y = 200;
              if (stage) {
                const pointer = stage.getPointerPosition() || { x: window.innerWidth / 2, y: window.innerHeight / 2 };
                const world = toWorld(pointer);
                x = world.x - 150;
                y = world.y - 100;
              }
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
                addNode({
                  id: nanoid(),
                  type: "image",
                  x,
                  y,
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
          e.preventDefault();
          break;
        }
      }
    }
    window.addEventListener("paste", handleGlobalPaste);
    return () => window.removeEventListener("paste", handleGlobalPaste);
  }, [addNode, toWorld, viewport, viewOnly]);

  useEffect(() => {
    if (viewOnly) return;
    const stage = stageRef.current;
    if (!stage || !transformerRef.current) return;

    const selectedNodes = selectedIds
      .map((id) => stage.findOne(`#${id}`))
      .filter(Boolean) as Konva.Node[];

    transformerRef.current.nodes(selectedNodes);
    transformerRef.current.getLayer()?.batchDraw();
  }, [selectedIds, nodes, stageRef, viewOnly]);

  useEffect(() => {
    if (viewOnly) return;
    const stage = stageRef.current;
    if (!stage) return;

    function handleTransformEnd(e: any) {
      const target = e.target;
      const id = target.id();
      if (!id) return;
      const w = Math.round(target.width() * target.scaleX());
      const h = Math.round(target.height() * target.scaleY());
      target.scaleX(1);
      target.scaleY(1);
      updateNode(id, {
        x: Math.round(target.x()),
        y: Math.round(target.y()),
        width: w,
        height: h,
      });
    }

    stage.on("transformend", handleTransformEnd);
    return () => {
      stage.off("transformend", handleTransformEnd);
    };
  }, [stageRef, updateNode, viewOnly]);

  function createNodeAt(type: string, x: number, y: number, w: number, h: number) {
    const node: FlowNode = {
      id: nanoid(),
      type: NODE_TYPE_MAP[type] ?? "process",
      x: snap(x),
      y: snap(y),
      width: w,
      height: h,
      text: "",
      fill: "#1B1E29",
      stroke: "#7C5CFF",
    };
    addNode(node);
    setSelectedIds([node.id]);
    setActiveTool("select");
  }

  function handleStageMouseDown(e: Konva.KonvaEventObject<PointerEvent>) {
    if (viewOnly) return;
    const stage = stageRef.current;
    if (!stage) return;
    const clickedOnEmpty = e.target === stage;
    const pointer = stage.getPointerPosition();
    if (!pointer) return;
    const world = toWorld(pointer);

    if (["rectangle", "diamond", "oval", "parallelogram", "text"].includes(activeTool)) {
      drawStart.current = world;
      setPreviewRect({ x: world.x, y: world.y, w: 0, h: 0 });
      return;
    }

    if (activeTool === "freehand" || activeTool === "highlighter" || activeTool === "eraser") {
      isDrawingStroke.current = true;
      currentStrokeId.current = nanoid();
      const pressure = e.evt.pressure || 0.5;
      currentStrokePoints.current = [world.x, world.y];
      currentStrokePressures.current = [pressure];

      const strokeColorValue = activeTool === "highlighter" ? "#2EE6A6" : activeTool === "eraser" ? "transparent" : (penColor === "default" ? defaultPenColor : penColor);
      const strokeWidthValue = activeTool === "eraser" ? eraserWidth : activeTool === "highlighter" ? penWidth * 2.5 : penWidth;

      setActiveStroke({
        id: currentStrokeId.current,
        tool: activeTool === "freehand" ? "pen" : (activeTool as "pen" | "highlighter" | "eraser"),
        points: [...currentStrokePoints.current],
        pressures: [...currentStrokePressures.current],
        color: strokeColorValue,
        width: strokeWidthValue,
      });
      return;
    }

    if (clickedOnEmpty && activeTool === "select") {
      setSelectedIds([]);
    }
  }

  function handleStageMouseMove(e: Konva.KonvaEventObject<PointerEvent>) {
    const stage = stageRef.current;
    if (!stage) return;
    const pointer = stage.getPointerPosition();
    if (!pointer) return;
    const world = toWorld(pointer);
    onCursorMove?.(world.x, world.y);

    if (viewOnly) return;

    if (drawStart.current) {
      setPreviewRect({
        x: Math.min(drawStart.current.x, world.x),
        y: Math.min(drawStart.current.y, world.y),
        w: Math.abs(world.x - drawStart.current.x),
        h: Math.abs(world.y - drawStart.current.y),
      });
    }

    if (isDrawingStroke.current) {
      if (e.evt.buttons === 0) {
        handleStageMouseUp();
        return;
      }
      const pressure = e.evt.pressure || 0.5;
      currentStrokePoints.current.push(world.x, world.y);
      currentStrokePressures.current.push(pressure);
      
      const strokeColorValue = activeTool === "highlighter" ? "#2EE6A6" : activeTool === "eraser" ? "transparent" : (penColor === "default" ? defaultPenColor : penColor);
      const strokeWidthValue = activeTool === "eraser" ? eraserWidth : activeTool === "highlighter" ? penWidth * 2.5 : penWidth;
      
      setActiveStroke({
        id: currentStrokeId.current,
        tool: activeTool === "freehand" ? "pen" : (activeTool as "pen" | "highlighter" | "eraser"),
        points: [...currentStrokePoints.current],
        pressures: [...currentStrokePressures.current],
        color: strokeColorValue,
        width: strokeWidthValue,
      });
    }
  }

  function handleStageMouseUp() {
    if (viewOnly) return;

    if (drawStart.current && previewRect) {
      const size = DEFAULT_SIZE[activeTool] ?? { w: 160, h: 72 };
      const w = previewRect.w > 20 ? previewRect.w : size.w;
      const h = previewRect.h > 20 ? previewRect.h : size.h;
      createNodeAt(activeTool, previewRect.x, previewRect.y, w, h);
    }
    drawStart.current = null;
    setPreviewRect(null);

    if (isDrawingStroke.current) {
      const strokeColorValue = activeTool === "highlighter" ? "#2EE6A6" : activeTool === "eraser" ? "transparent" : (penColor === "default" ? defaultPenColor : penColor);
      const strokeWidthValue = activeTool === "eraser" ? eraserWidth : activeTool === "highlighter" ? penWidth * 2.5 : penWidth;

      addStroke({
        id: currentStrokeId.current,
        tool: activeTool === "freehand" ? "pen" : (activeTool as "pen" | "highlighter" | "eraser"),
        points: currentStrokePoints.current,
        pressures: currentStrokePressures.current,
        color: strokeColorValue,
        width: strokeWidthValue,
      });
      isDrawingStroke.current = false;
      currentStrokePoints.current = [];
      currentStrokePressures.current = [];
      setActiveStroke(null);
    }
  }

  const handleStageMouseUpRef = useRef(handleStageMouseUp);
  handleStageMouseUpRef.current = handleStageMouseUp;

  useEffect(() => {
    function handleGlobalPointerUp() {
      if (isDrawingStroke.current) {
        handleStageMouseUpRef.current();
      }
    }
    window.addEventListener("pointerup", handleGlobalPointerUp);
    return () => window.removeEventListener("pointerup", handleGlobalPointerUp);
  }, []);

  function handleNodeSelect(nodeId: string, e?: Konva.KonvaEventObject<Event>) {
    if (viewOnly) return;
    if (activeTool === "connector" || activeTool === "arrow") {
      if (!connectingFromId) {
        setConnectingFromId(nodeId);
      } else if (connectingFromId !== nodeId) {
        const fromNode = nodes.find((n) => n.id === connectingFromId);
        const toNode = nodes.find((n) => n.id === nodeId);
        if (fromNode && toNode) {
          addEdge({
            id: nanoid(),
            fromNodeId: fromNode.id,
            toNodeId: toNode.id,
            points: [
              fromNode.x + fromNode.width / 2,
              fromNode.y + fromNode.height / 2,
              toNode.x + toNode.width / 2,
              toNode.y + toNode.height / 2,
            ],
            stroke: "#7C5CFF",
          });
        }
        setConnectingFromId(null);
        setActiveTool("select");
      }
      return;
    }

    const isShift = (e?.evt as MouseEvent)?.shiftKey;
    if (isShift) {
      setSelectedIds(
        selectedIds.includes(nodeId)
          ? selectedIds.filter((id) => id !== nodeId)
          : [...selectedIds, nodeId]
      );
    } else {
      setSelectedIds([nodeId]);
    }
  }

  const isPanning = activeTool === "pan";

  const bgClass =
    theme === "light"
      ? "bg-slate-100"
      : theme === "chalkboard"
      ? "bg-[#0b3c25]"
      : "bg-ink-950";

  const gridStyle = showGrid
    ? {
        backgroundImage:
          theme === "light"
            ? "linear-gradient(to right, rgba(0,0,0,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(0,0,0,0.06) 1px, transparent 1px)"
            : theme === "chalkboard"
            ? "linear-gradient(to right, rgba(255,255,255,0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.08) 1px, transparent 1px)"
            : "linear-gradient(to right, rgba(237,235,230,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(237,235,230,0.04) 1px, transparent 1px)",
        backgroundSize: "32px 32px",
      }
    : {};

  return (
    <div
      className={`relative h-full w-full overflow-hidden select-none touch-none ${bgClass}`}
      style={{ ...gridStyle, touchAction: "none" }}
    >
      {!viewOnly && <Toolbar />}
      <MiniMap nodes={nodes} viewport={viewport} />
      {participants && <PresenceBar participants={participants} connected={!!isConnected} />}
      {remoteCursors && <RemoteCursorsOverlay cursors={remoteCursors} viewport={viewport} />}

      <Stage
        ref={stageRef}
        width={window.innerWidth}
        height={window.innerHeight}
        x={viewport.x}
        y={viewport.y}
        scaleX={viewport.zoom}
        scaleY={viewport.zoom}
        draggable={isPanning}
        onDragEnd={(e) => setViewport({ ...viewport, x: e.target.x(), y: e.target.y() })}
        onWheel={handleWheel}
        onPointerDown={handleStageMouseDown}
        onPointerMove={handleStageMouseMove}
        onPointerUp={handleStageMouseUp}
        style={{ touchAction: "none" }}
      >
        {/* Layer 1: Background Freehand Strokes */}
        <Layer>
          {strokes.map((stroke) => (
            <StrokeShape key={stroke.id} stroke={stroke} />
          ))}
          {activeStroke && (
            <StrokeShape stroke={activeStroke} />
          )}
        </Layer>

        {/* Layer 2: Interactive Flowchart Nodes, Edges, and Selections */}
        <Layer>
          {edges.map((edge) => (
            <EdgeShape
              key={edge.id}
              edge={edge}
              isSelected={selectedIds.includes(edge.id)}
              theme={theme}
              onSelect={() => setSelectedIds([edge.id])}
              onDblClick={() => {
                const label = window.prompt(
                  "Connector label (e.g. Yes / No) — helps code generation pick the right branch",
                  edge.label ?? ""
                );
                if (label !== null) updateEdge(edge.id, { label: label.trim() || undefined });
              }}
            />
          ))}

          {nodes.map((node) => (
            <NodeShape
              key={node.id}
              node={node}
              isSelected={selectedIds.includes(node.id)}
              isExecuting={executingNodeId === node.id}
              theme={theme}
              viewOnly={viewOnly}
              onSelect={(e?: any) => handleNodeSelect(node.id, e)}
              onDragEnd={(x, y) => updateNode(node.id, { x: snap(x), y: snap(y) })}
              onDblClick={() => {
                const text = window.prompt("Node text", node.text) ?? node.text;
                updateNode(node.id, { text });
              }}
            />
          ))}

          {previewRect && (
            <Group>
              <Rect
                x={previewRect.x}
                y={previewRect.y}
                width={previewRect.w}
                height={previewRect.h}
                stroke="#7C5CFF"
                dash={[6, 4]}
                strokeWidth={1.5}
                fill="rgba(124,92,255,0.08)"
              />
            </Group>
          )}

          {!viewOnly && <Transformer ref={transformerRef} rotateEnabled={false} />}
        </Layer>
      </Stage>

      {connectingFromId && (
        <div className="pointer-events-none absolute bottom-6 left-1/2 -translate-x-1/2 rounded-full bg-violet-500 px-4 py-2 text-sm text-white shadow-glow-violet">
          Click a target node to connect
        </div>
      )}

      {(() => {
        const selectedNode = selectedIds.length === 1 ? nodes.find((n) => n.id === selectedIds[0]) : null;
        if (!selectedNode || viewOnly) return null;
        
        const COLOR_OPTIONS = [
          { key: "default", label: "Default", bg: "bg-[#7C5CFF]" },
          { key: "blue", label: "Blue", bg: "bg-[#3B82F6]" },
          { key: "green", label: "Green", bg: "bg-[#10B981]" },
          { key: "yellow", label: "Yellow", bg: "bg-[#F59E0B]" },
          { key: "red", label: "Red", bg: "bg-[#EF4444]" },
          { key: "purple", label: "Purple", bg: "bg-[#8B5CF6]" },
        ];

        return (
          <div className="absolute bottom-6 left-1/2 z-20 -translate-x-1/2 flex items-center gap-3 rounded-full border border-white/10 bg-ink-900/90 px-4 py-2 shadow-2xl backdrop-blur-md">
            <span className="text-xs text-paper-300 mr-1 font-medium">Shape Style:</span>
            {COLOR_OPTIONS.map((opt) => {
              const isCurrent = (selectedNode.fill || "default").toLowerCase() === opt.key;
              return (
                <button
                  key={opt.key}
                  onClick={() => updateNode(selectedNode.id, { fill: opt.key, stroke: opt.key })}
                  title={opt.label}
                  className={clsx(
                    "h-5 w-5 rounded-full transition-all hover:scale-125 focus:outline-none relative",
                    opt.bg,
                    isCurrent ? "ring-2 ring-white ring-offset-2 ring-offset-ink-950 scale-110" : ""
                  )}
                />
              );
            })}
          </div>
        );
      })()}

      {/* Freehand Pen / Highlighter Style Panel */}
      {!viewOnly && (activeTool === "freehand" || activeTool === "highlighter") && (
        <div className="absolute bottom-6 left-1/2 z-20 -translate-x-1/2 flex items-center gap-4 rounded-full border border-white/10 bg-ink-900/90 px-4 py-2 shadow-2xl backdrop-blur-md">
          {/* Colors */}
          {activeTool === "freehand" && (
            <div className="flex items-center gap-1.5 border-r border-white/10 pr-3">
              <span className="text-xs text-paper-300 mr-1 font-medium">Color:</span>
              {[
                { key: "default", label: "Default", bg: "bg-paper-200 border border-white/20" },
                { key: "#FFFFFF", label: "White", bg: "bg-[#FFFFFF] border border-white/25" },
                { key: "#1E293B", label: "Ink", bg: "bg-[#1E293B] border border-white/10" },
                { key: "#EF4444", label: "Red", bg: "bg-[#EF4444]" },
                { key: "#F97316", label: "Orange", bg: "bg-[#F97316]" },
                { key: "#FBBF24", label: "Yellow", bg: "bg-[#FBBF24]" },
                { key: "#10B981", label: "Green", bg: "bg-[#10B981]" },
                { key: "#34D399", label: "Mint", bg: "bg-[#34D399]" },
                { key: "#3B82F6", label: "Blue", bg: "bg-[#3B82F6]" },
                { key: "#8B5CF6", label: "Purple", bg: "bg-[#8B5CF6]" },
                { key: "#EC4899", label: "Pink", bg: "bg-[#EC4899]" },
              ].map((opt) => {
                const isCurrent = penColor === opt.key;
                return (
                  <button
                    key={opt.key}
                    onClick={() => setPenColor(opt.key)}
                    title={opt.label}
                    className={clsx(
                      "h-4 w-4 rounded-full transition-all hover:scale-125 focus:outline-none",
                      opt.bg,
                      isCurrent ? "ring-2 ring-white ring-offset-1 ring-offset-ink-950 scale-110" : ""
                    )}
                  />
                );
              })}
            </div>
          )}

          {/* Thickness Slider */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-paper-300 font-medium shrink-0">Thickness:</span>
            <input
              type="range"
              min="1"
              max="24"
              value={penWidth}
              onChange={(e) => setPenWidth(Number(e.target.value))}
              className="w-24 accent-violet-500 cursor-pointer h-1 rounded-lg bg-white/20 appearance-none"
            />
            <span className="text-[10px] font-mono text-paper-300 w-6 text-right font-semibold">{penWidth}px</span>
          </div>
        </div>
      )}

      {/* Eraser Size Panel */}
      {!viewOnly && activeTool === "eraser" && (
        <div className="absolute bottom-6 left-1/2 z-20 -translate-x-1/2 flex items-center gap-3 rounded-full border border-white/10 bg-ink-900/90 px-4 py-2 shadow-2xl backdrop-blur-md">
          <span className="text-xs text-paper-300 font-medium shrink-0">Eraser Size:</span>
          <input
            type="range"
            min="5"
            max="100"
            value={eraserWidth}
            onChange={(e) => setEraserWidth(Number(e.target.value))}
            className="w-32 accent-violet-500 cursor-pointer h-1 rounded-lg bg-white/20 appearance-none"
          />
          <span className="text-[10px] font-mono text-paper-300 w-8 text-right font-semibold">{eraserWidth}px</span>
        </div>
      )}
    </div>
  );
}
