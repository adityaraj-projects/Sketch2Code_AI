import { api } from "@/api/client";

export interface AdminUser {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  is_email_verified: boolean;
  auth_provider: string;
  project_count: number;
  created_at: string;
}

export interface AdminProject {
  id: string;
  name: string;
  owner_name: string;
  owner_email: string;
  is_shared: boolean;
  updated_at: string;
  created_at: string;
}

export interface AdminAnalytics {
  total_users: number;
  total_projects: number;
  shared_projects: number;
  total_comments: number;
  total_versions: number;
  signups_by_day: [string, number][];
  projects_by_day: [string, number][];
  avg_projects_per_user: number;
}

export async function fetchAdminUsers(): Promise<AdminUser[]> {
  const { data } = await api.get<AdminUser[]>("/admin/users");
  return data;
}

export async function setAdminUserActive(userId: string, isActive: boolean): Promise<AdminUser> {
  const { data } = await api.patch<AdminUser>(`/admin/users/${userId}/active`, { is_active: isActive });
  return data;
}

export async function fetchAdminProjects(): Promise<AdminProject[]> {
  const { data } = await api.get<AdminProject[]>("/admin/projects");
  return data;
}

export async function adminDeleteProject(projectId: string): Promise<void> {
  await api.delete(`/admin/projects/${projectId}`);
}

export async function fetchAdminAnalytics(): Promise<AdminAnalytics> {
  const { data } = await api.get<AdminAnalytics>("/admin/analytics");
  return data;
}
