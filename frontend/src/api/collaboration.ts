import { api } from "@/api/client";

export interface CommentOut {
  id: string;
  author_id: string;
  author_name: string;
  node_id: string | null;
  x: number | null;
  y: number | null;
  text: string;
  created_at: string;
}

export interface VersionSummary {
  id: string;
  label: string;
  created_by_name: string;
  created_at: string;
}

export async function fetchComments(projectId: string): Promise<CommentOut[]> {
  const { data } = await api.get<CommentOut[]>(`/projects/${projectId}/comments`);
  return data;
}

export async function addComment(
  projectId: string,
  text: string,
  opts: { nodeId?: string; x?: number; y?: number }
): Promise<CommentOut> {
  const { data } = await api.post<CommentOut>(`/projects/${projectId}/comments`, {
    text,
    node_id: opts.nodeId ?? null,
    x: opts.x ?? null,
    y: opts.y ?? null,
  });
  return data;
}

export async function deleteComment(projectId: string, commentId: string): Promise<void> {
  await api.delete(`/projects/${projectId}/comments/${commentId}`);
}

export async function fetchVersions(projectId: string): Promise<VersionSummary[]> {
  const { data } = await api.get<VersionSummary[]>(`/projects/${projectId}/versions`);
  return data;
}

export async function saveVersion(projectId: string, label?: string): Promise<VersionSummary> {
  const { data } = await api.post<VersionSummary>(`/projects/${projectId}/versions`, { label: label ?? null });
  return data;
}

export async function restoreVersion(projectId: string, versionId: string): Promise<void> {
  await api.post(`/projects/${projectId}/versions/${versionId}/restore`);
}

export async function setProjectSharing(projectId: string, isShared: boolean): Promise<void> {
  await api.patch(`/projects/${projectId}/share`, { is_shared: isShared });
}
