import { api } from "@/api/client";
import type { FlowEdge, FlowNode } from "@/types";

export interface TraceStep {
  step_index: number;
  node_id: string;
  node_type: string;
  label: string;
  variables: Record<string, unknown>;
  output: string | null;
  branch_taken: string | null;
}

export interface ExecutionResponse {
  steps: TraceStep[];
  final_variables: Record<string, unknown>;
  console_output: string[];
  status: "completed" | "error" | "step_limit";
  error_message: string | null;
  error_node_id: string | null;
  warnings: string[];
}

export async function runExecution(
  nodes: FlowNode[],
  edges: FlowEdge[],
  inputValues: string[]
): Promise<ExecutionResponse> {
  const { data } = await api.post<ExecutionResponse>("/execution/run", {
    nodes: nodes.map((n) => ({ id: n.id, type: n.type, text: n.text })),
    edges: edges.map((e) => ({ id: e.id, fromNodeId: e.fromNodeId, toNodeId: e.toNodeId, label: e.label ?? null })),
    input_values: inputValues,
  });
  return data;
}
