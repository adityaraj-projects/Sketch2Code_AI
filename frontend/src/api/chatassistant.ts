import { api } from "@/api/client";
import type { FlowEdge, FlowNode } from "@/types";

export interface ChatResponse {
  reply: string;
  intent: string;
  data: Record<string, unknown> | null;
}

export async function sendChatMessage(
  message: string,
  nodes: FlowNode[],
  edges: FlowEdge[]
): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/assistant/chat", {
    message,
    nodes: nodes.map((n) => ({ id: n.id, type: n.type, text: n.text, imageUrl: n.imageUrl ?? null })),
    edges: edges.map((e) => ({ id: e.id, fromNodeId: e.fromNodeId, toNodeId: e.toNodeId, label: e.label ?? null })),
  });
  return data;
}
