import { api } from "@/api/client";
import type { FlowEdge, FlowNode } from "@/types";

export type ExplainMode = "simple" | "line_by_line" | "interview" | "study_notes" | "generate_quiz" | "dry_run" | "custom";

export interface ExplainResponse {
  explanation: string;
  pseudocode: string;
  warnings: string[];
}

export async function explainFlowchart(
  nodes: FlowNode[],
  edges: FlowEdge[],
  mode: ExplainMode,
  customPrompt?: string
): Promise<ExplainResponse> {
  const { data } = await api.post<ExplainResponse>("/explainer/explain", {
    nodes: nodes.map((n) => ({ id: n.id, type: n.type, text: n.text })),
    edges: edges.map((e) => ({ id: e.id, fromNodeId: e.fromNodeId, toNodeId: e.toNodeId, label: e.label ?? null })),
    mode,
    custom_prompt: customPrompt,
  });
  return data;
}
