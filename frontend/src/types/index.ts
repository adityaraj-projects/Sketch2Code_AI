export interface User {
  id: string;
  full_name: string;
  email: string;
  is_email_verified: boolean;
  auth_provider: "local" | "google";
  is_admin: boolean;
  created_at: string;
}

export type NodeType =
  | "start"
  | "end"
  | "process"
  | "decision"
  | "input"
  | "output"
  | "connector"
  | "text"
  | "image";

export interface FlowNode {
  id: string;
  type: NodeType;
  x: number;
  y: number;
  width: number;
  height: number;
  text: string;
  fill: string;
  stroke: string;
  imageUrl?: string;
}

export interface FlowEdge {
  id: string;
  fromNodeId: string;
  toNodeId: string;
  points: number[];
  stroke: string;
  label?: string;
}

export interface FreehandStroke {
  id: string;
  tool: "pen" | "highlighter" | "eraser";
  points: number[];
  pressures: number[];
  color: string;
  width: number;
}

export interface Viewport {
  x: number;
  y: number;
  zoom: number;
}

export interface CanvasData {
  nodes: FlowNode[];
  edges: FlowEdge[];
  strokes: FreehandStroke[];
  viewport: Viewport;
}

export interface Project {
  id: string;
  name: string;
  canvas_data: CanvasData;
  thumbnail_url: string | null;
  is_shared: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  thumbnail_url: string | null;
  updated_at: string;
}

export type ToolId =
  | "select"
  | "pan"
  | "rectangle"
  | "diamond"
  | "oval"
  | "parallelogram"
  | "arrow"
  | "connector"
  | "text"
  | "freehand"
  | "highlighter"
  | "eraser";

export interface RecognizeResponse {
  nodes: FlowNode[];
  edges: FlowEdge[];
  consumed_stroke_ids: string[];
  unrecognized_stroke_ids: string[];
  ocr_warning: string | null;
}
