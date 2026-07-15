import { api } from "@/api/client";
import type { FlowEdge, FlowNode } from "@/types";

export interface TemplateSummary {
  id: string;
  name: string;
  category: string;
  description: string;
  executable: boolean;
}

export interface TemplateLoadResponse {
  template: TemplateSummary;
  nodes: FlowNode[];
  edges: FlowEdge[];
  warnings: string[];
}

export async function fetchTemplates(): Promise<TemplateSummary[]> {
  const { data } = await api.get<{ templates: TemplateSummary[] }>("/templates");
  return data.templates;
}

export async function loadTemplate(templateId: string): Promise<TemplateLoadResponse> {
  const { data } = await api.get<TemplateLoadResponse>(`/templates/${templateId}/load`);
  return data;
}
