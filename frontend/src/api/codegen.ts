import { api } from "@/api/client";
import type { FlowEdge, FlowNode } from "@/types";

export interface CodegenResponse {
  code: string;
  language: string;
  file_extension: string;
  warnings: string[];
}

export async function fetchSupportedLanguages(): Promise<string[]> {
  const { data } = await api.get<{ languages: string[] }>("/codegen/languages");
  return data.languages;
}

export async function generateCodeFromFlowchart(
  nodes: FlowNode[],
  edges: FlowEdge[],
  language: string
): Promise<CodegenResponse> {
  const { data } = await api.post<CodegenResponse>("/codegen/generate", {
    nodes: nodes.map((n) => ({ id: n.id, type: n.type, text: n.text })),
    edges: edges.map((e) => ({ id: e.id, fromNodeId: e.fromNodeId, toNodeId: e.toNodeId, label: e.label ?? null })),
    language,
  });
  return data;
}
