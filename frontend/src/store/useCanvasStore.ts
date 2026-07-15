import { create } from "zustand";
import { nanoid } from "@/lib/id";
import type { CanvasData, FlowEdge, FlowNode, FreehandStroke, ToolId, Viewport } from "@/types";

interface HistorySnapshot {
  nodes: FlowNode[];
  edges: FlowEdge[];
  strokes: FreehandStroke[];
}

interface CanvasState {
  projectId: string | null;
  projectName: string;
  nodes: FlowNode[];
  edges: FlowEdge[];
  strokes: FreehandStroke[];
  viewport: Viewport;

  activeTool: ToolId;
  selectedIds: string[];
  isDirty: boolean;
  executingNodeId: string | null;

  past: HistorySnapshot[];
  future: HistorySnapshot[];

  // lifecycle
  loadProject: (projectId: string, name: string, data: CanvasData) => void;
  markSaved: () => void;

  // tool & selection
  setActiveTool: (tool: ToolId) => void;
  setSelectedIds: (ids: string[]) => void;
  setExecutingNodeId: (id: string | null) => void;

  // mutation (each of these snapshots history first)
  addNode: (node: FlowNode) => void;
  updateNode: (id: string, patch: Partial<FlowNode>) => void;
  deleteNodes: (ids: string[]) => void;
  addEdge: (edge: FlowEdge) => void;
  updateEdge: (id: string, patch: Partial<FlowEdge>) => void;
  deleteEdges: (ids: string[]) => void;
  addStroke: (stroke: FreehandStroke) => void;
  deleteStroke: (id: string) => void;
  deleteSelected: () => void;
  setViewport: (viewport: Viewport) => void;

  // clipboard
  copySelection: () => void;
  pasteClipboard: () => void;

  // AI flowchart recognition (Feature 1) — replaces recognized raw strokes
  // with clean editable nodes/edges on the same canvas.
  applyRecognitionResult: (nodes: FlowNode[], edges: FlowEdge[], consumedStrokeIds: string[]) => void;

  // Code -> Flowchart (Feature 3) — adds a freshly generated diagram onto
  // the canvas, offset below any existing content rather than overwriting it.
  loadGeneratedFlowchart: (nodes: FlowNode[], edges: FlowEdge[]) => void;

  // Flowchart Beautifier (Feature 9) — replaces all clean nodes/edges with
  // a freshly auto-laid-out version of the same structure. Freehand
  // strokes are left untouched.
  replaceNodesAndEdges: (nodes: FlowNode[], edges: FlowEdge[]) => void;

  // Realtime Collaboration (Feature 14) — applies a remote peer's canvas
  // state directly, without pushing to local undo history (a remote
  // change isn't something the local user should "undo" out from under
  // their collaborator) and without marking the project dirty locally
  // (the peer who made the change is responsible for persisting it).
  applyRemoteSnapshot: (nodes: FlowNode[], edges: FlowEdge[], strokes: FreehandStroke[]) => void;

  // history
  undo: () => void;
  redo: () => void;

  serialize: () => CanvasData;
}

const MAX_HISTORY = 60;
let clipboard: HistorySnapshot | null = null;

function snapshotOf(state: CanvasState): HistorySnapshot {
  return {
    nodes: structuredClone(state.nodes),
    edges: structuredClone(state.edges),
    strokes: structuredClone(state.strokes),
  };
}

export const useCanvasStore = create<CanvasState>((set, get) => ({
  projectId: null,
  projectName: "Untitled Flowchart",
  nodes: [],
  edges: [],
  strokes: [],
  viewport: { x: 0, y: 0, zoom: 1 },

  activeTool: "select",
  selectedIds: [],
  isDirty: false,
  executingNodeId: null,

  past: [],
  future: [],

  loadProject: (projectId, name, data) =>
    set({
      projectId,
      projectName: name,
      nodes: data.nodes ?? [],
      edges: data.edges ?? [],
      strokes: data.strokes ?? [],
      viewport: data.viewport ?? { x: 0, y: 0, zoom: 1 },
      past: [],
      future: [],
      isDirty: false,
    }),

  markSaved: () => set({ isDirty: false }),

  setActiveTool: (tool) => set({ activeTool: tool, selectedIds: [] }),
  setSelectedIds: (ids) => set({ selectedIds: ids }),
  setExecutingNodeId: (id) => set({ executingNodeId: id }),

  addNode: (node) =>
    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      nodes: [...state.nodes, node],
      isDirty: true,
    })),

  updateNode: (id, patch) =>
    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      nodes: state.nodes.map((n) => (n.id === id ? { ...n, ...patch } : n)),
      isDirty: true,
    })),

  deleteNodes: (ids) =>
    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      nodes: state.nodes.filter((n) => !ids.includes(n.id)),
      edges: state.edges.filter((e) => !ids.includes(e.fromNodeId) && !ids.includes(e.toNodeId)),
      selectedIds: [],
      isDirty: true,
    })),

  addEdge: (edge) =>
    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      edges: [...state.edges, edge],
      isDirty: true,
    })),

  updateEdge: (id, patch) =>
    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      edges: state.edges.map((e) => (e.id === id ? { ...e, ...patch } : e)),
      isDirty: true,
    })),

  deleteEdges: (ids) =>
    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      edges: state.edges.filter((e) => !ids.includes(e.id)),
      isDirty: true,
    })),

  addStroke: (stroke) =>
    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      strokes: [...state.strokes, stroke],
      isDirty: true,
    })),

  deleteStroke: (id) =>
    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      strokes: state.strokes.filter((s) => s.id !== id),
      isDirty: true,
    })),

  deleteSelected: () =>
    set((state) => {
      const ids = state.selectedIds;
      if (ids.length === 0) return {};
      
      const newNodes = state.nodes.filter((n) => !ids.includes(n.id));
      const newEdges = state.edges.filter(
        (e) => !ids.includes(e.id) && !ids.includes(e.fromNodeId) && !ids.includes(e.toNodeId)
      );
      
      const newStrokes = state.strokes.filter((s) => !ids.includes(s.id));

      return {
        past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
        future: [],
        nodes: newNodes,
        edges: newEdges,
        strokes: newStrokes,
        selectedIds: [],
        isDirty: true,
      };
    }),

  // Viewport changes (pan/zoom) are intentionally excluded from undo history —
  // undoing a zoom/pan is not what users expect from Ctrl+Z.
  setViewport: (viewport) => set({ viewport }),

  copySelection: () => {
    const state = get();
    const nodes = state.nodes.filter((n) => state.selectedIds.includes(n.id));
    const nodeIds = new Set(nodes.map((n) => n.id));
    const edges = state.edges.filter((e) => nodeIds.has(e.fromNodeId) && nodeIds.has(e.toNodeId));
    clipboard = { nodes: structuredClone(nodes), edges: structuredClone(edges), strokes: [] };
  },

  pasteClipboard: () => {
    if (!clipboard || clipboard.nodes.length === 0) return;
    const idMap = new Map<string, string>();
    const offset = 32;

    const newNodes = clipboard.nodes.map((n) => {
      const newId = nanoid();
      idMap.set(n.id, newId);
      return { ...n, id: newId, x: n.x + offset, y: n.y + offset };
    });
    const newEdges = clipboard.edges.map((e) => ({
      ...e,
      id: nanoid(),
      fromNodeId: idMap.get(e.fromNodeId)!,
      toNodeId: idMap.get(e.toNodeId)!,
      points: e.points.map((p, i) => (i % 2 === 0 ? p + offset : p + offset)),
    }));

    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      nodes: [...state.nodes, ...newNodes],
      edges: [...state.edges, ...newEdges],
      selectedIds: newNodes.map((n) => n.id),
      isDirty: true,
    }));
  },

  applyRecognitionResult: (newNodes, newEdges, consumedStrokeIds) =>
    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      nodes: [...state.nodes, ...newNodes],
      edges: [...state.edges, ...newEdges],
      strokes: state.strokes.filter((s) => !consumedStrokeIds.includes(s.id)),
      selectedIds: newNodes.map((n) => n.id),
      isDirty: true,
    })),

  loadGeneratedFlowchart: (newNodes, newEdges) =>
    set((state) => {
      // Place the new diagram below whatever's already on the canvas
      // instead of overwriting it, so this is never destructive.
      const offsetX = 0;
      const offsetY =
        state.nodes.length > 0 ? Math.max(...state.nodes.map((n) => n.y + n.height)) + 120 : 0;

      const idMap = new Map<string, string>();
      const offsetNodes = newNodes.map((n) => {
        const newId = nanoid();
        idMap.set(n.id, newId);
        return { ...n, id: newId, x: n.x + offsetX, y: n.y + offsetY };
      });
      const offsetEdges = newEdges.map((e) => ({
        ...e,
        id: nanoid(),
        fromNodeId: idMap.get(e.fromNodeId) ?? e.fromNodeId,
        toNodeId: idMap.get(e.toNodeId) ?? e.toNodeId,
        points: [
          e.points[0] + offsetX, e.points[1] + offsetY,
          e.points[2] + offsetX, e.points[3] + offsetY,
        ],
      }));

      return {
        past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
        future: [],
        nodes: [...state.nodes, ...offsetNodes],
        edges: [...state.edges, ...offsetEdges],
        selectedIds: offsetNodes.map((n) => n.id),
        isDirty: true,
      };
    }),

  replaceNodesAndEdges: (newNodes, newEdges) =>
    set((state) => ({
      past: [...state.past.slice(-MAX_HISTORY), snapshotOf(state)],
      future: [],
      nodes: newNodes,
      edges: newEdges,
      selectedIds: [],
      isDirty: true,
    })),

  applyRemoteSnapshot: (nodes, edges, strokes) => set({ nodes, edges, strokes }),

  undo: () =>
    set((state) => {
      if (state.past.length === 0) return state;
      const previous = state.past[state.past.length - 1];
      return {
        past: state.past.slice(0, -1),
        future: [snapshotOf(state), ...state.future].slice(0, MAX_HISTORY),
        nodes: previous.nodes,
        edges: previous.edges,
        strokes: previous.strokes,
        isDirty: true,
      };
    }),

  redo: () =>
    set((state) => {
      if (state.future.length === 0) return state;
      const next = state.future[0];
      return {
        past: [...state.past, snapshotOf(state)].slice(-MAX_HISTORY),
        future: state.future.slice(1),
        nodes: next.nodes,
        edges: next.edges,
        strokes: next.strokes,
        isDirty: true,
      };
    }),

  serialize: () => {
    const state = get();
    return {
      nodes: state.nodes,
      edges: state.edges,
      strokes: state.strokes,
      viewport: state.viewport,
    };
  },
}));
