import { api } from "@/api/client";
import type { FlowEdge, FlowNode } from "@/types";

export interface ComplexityResponse {
  time_complexity: string;
  space_complexity: string;
  reasoning: string[];
  suggestions: string[];
  confidence: "high" | "estimated";
  narrative: string | null;
  narrative_unavailable_reason: string | null;
  warnings: string[];
}

export async function analyzeComplexity(nodes: FlowNode[], edges: FlowEdge[]): Promise<ComplexityResponse> {
  const { data } = await api.post<ComplexityResponse>("/complexity/analyze", {
    nodes: nodes.map((n) => ({ id: n.id, type: n.type, text: n.text })),
    edges: edges.map((e) => ({ id: e.id, fromNodeId: e.fromNodeId, toNodeId: e.toNodeId, label: e.label ?? null })),
    include_ai_narrative: true,
  });
  return data;
}
