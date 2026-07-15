import { api } from "@/api/client";
import type { FlowEdge, FlowNode } from "@/types";

export interface BeautifyResponse {
  nodes: FlowNode[];
  edges: FlowEdge[];
  warnings: string[];
}

export async function beautifyFlowchart(nodes: FlowNode[], edges: FlowEdge[]): Promise<BeautifyResponse> {
  const { data } = await api.post<BeautifyResponse>("/beautifier/beautify", {
    nodes: nodes.map((n) => ({ id: n.id, type: n.type, text: n.text })),
    edges: edges.map((e) => ({ id: e.id, fromNodeId: e.fromNodeId, toNodeId: e.toNodeId, label: e.label ?? null })),
  });
  return data;
}
