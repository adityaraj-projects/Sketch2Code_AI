import { api } from "@/api/client";
import type { FlowEdge, FlowNode } from "@/types";

export interface CodeToFlowchartResponse {
  nodes: FlowNode[];
  edges: FlowEdge[];
  warnings: string[];
}

export async function generateFlowchartFromCode(
  code: string,
  language: string
): Promise<CodeToFlowchartResponse> {
  const { data } = await api.post<CodeToFlowchartResponse>("/codetoflow/generate", { code, language });
  return data;
}
