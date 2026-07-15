import { api } from "@/api/client";
import type { FlowEdge, FlowNode } from "@/types";

export interface Finding {
  severity: "error" | "warning";
  category: string;
  message: string;
  node_ids: string[];
}

export interface BugDetectResponse {
  findings: Finding[];
  error_count: number;
  warning_count: number;
}

export async function scanForBugs(nodes: FlowNode[], edges: FlowEdge[]): Promise<BugDetectResponse> {
  const { data } = await api.post<BugDetectResponse>("/bugdetector/scan", {
    nodes: nodes.map((n) => ({ id: n.id, type: n.type, text: n.text })),
    edges: edges.map((e) => ({ id: e.id, fromNodeId: e.fromNodeId, toNodeId: e.toNodeId, label: e.label ?? null })),
  });
  return data;
}
