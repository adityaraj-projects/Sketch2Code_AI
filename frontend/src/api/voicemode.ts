import { api } from "@/api/client";
import type { FlowEdge, FlowNode } from "@/types";

export interface VoiceModeResponse {
  success: boolean;
  nodes: FlowNode[];
  edges: FlowEdge[];
  warnings: string[];
  generated_code: string;
  error_message: string | null;
}

export async function generateFlowchartFromSpeech(description: string): Promise<VoiceModeResponse> {
  const { data } = await api.post<VoiceModeResponse>("/voicemode/generate", { description });
  return data;
}
