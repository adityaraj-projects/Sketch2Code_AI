import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Users, LayoutGrid, Gauge, ShieldOff, ShieldCheck, Trash2, ShieldAlert } from "lucide-react";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { SimpleBarChart } from "@/components/admin/SimpleBarChart";
import {
  adminDeleteProject,
  fetchAdminAnalytics,
  fetchAdminProjects,
  fetchAdminUsers,
  setAdminUserActive,
} from "@/api/admin";
import { useAuthStore } from "@/store/useAuthStore";

type Tab = "overview" | "users" | "projects";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-white/10 bg-ink-900 p-4">
      <p className="font-display text-2xl font-semibold text-paper-100">{value}</p>
      <p className="mt-1 text-xs text-paper-500">{label}</p>
    </div>
  );
}

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("overview");
  const currentUserId = useAuthStore((s) => s.user?.id);
  const queryClient = useQueryClient();

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ["admin", "analytics"],
    queryFn: fetchAdminAnalytics,
    enabled: tab === "overview",
  });
  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ["admin", "users"],
    queryFn: fetchAdminUsers,
    enabled: tab === "users",
  });
  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ["admin", "projects"],
    queryFn: fetchAdminProjects,
    enabled: tab === "projects",
  });

  async function handleToggleActive(userId: string, current: boolean) {
    await setAdminUserActive(userId, !current);
    queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
  }

  async function handleDeleteProject(projectId: string, name: string) {
    if (!window.confirm(`Delete "${name}"? This can't be undone.`)) return;
    await adminDeleteProject(projectId);
    queryClient.invalidateQueries({ queryKey: ["admin", "projects"] });
  }

  return (
    <div className="flex h-screen bg-ink-950">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="mb-6 flex items-center gap-2">
          <ShieldAlert size={22} className="text-violet-400" />
          <h1 className="font-display text-2xl font-semibold text-paper-100">Admin Panel</h1>
        </div>

        <div className="mb-6 flex gap-1.5">
          {([
            { id: "overview", label: "Overview", icon: Gauge },
            { id: "users", label: "Users", icon: Users },
            { id: "projects", label: "Projects", icon: LayoutGrid },
          ] as const).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm ${
                tab === t.id ? "bg-violet-500 text-white" : "bg-white/[0.04] text-paper-300 hover:bg-white/[0.08]"
              }`}
            >
              <t.icon size={14} /> {t.label}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <div>
            {analyticsLoading || !analytics ? (
              <div className="flex justify-center py-16"><Loader2 size={22} className="animate-spin text-violet-400" /></div>
            ) : (
              <div className="flex flex-col gap-6">
                <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
                  <StatCard label="Total Users" value={analytics.total_users} />
                  <StatCard label="Total Projects" value={analytics.total_projects} />
                  <StatCard label="Shared Projects" value={analytics.shared_projects} />
                  <StatCard label="Comments" value={analytics.total_comments} />
                  <StatCard label="Avg Projects / User" value={analytics.avg_projects_per_user} />
                </div>
                <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                  <div className="glass-panel rounded-2xl p-5">
                    <h3 className="mb-3 text-sm font-medium text-paper-100">Signups — last 30 days</h3>
                    <SimpleBarChart data={analytics.signups_by_day} color="#7C5CFF" />
                  </div>
                  <div className="glass-panel rounded-2xl p-5">
                    <h3 className="mb-3 text-sm font-medium text-paper-100">Projects created — last 30 days</h3>
                    <SimpleBarChart data={analytics.projects_by_day} color="#2EE6A6" />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "users" && (
          <div className="glass-panel overflow-hidden rounded-2xl">
            {usersLoading || !users ? (
              <div className="flex justify-center py-16"><Loader2 size={22} className="animate-spin text-violet-400" /></div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-xs text-paper-500">
                    <th className="px-4 py-3 font-medium">Name</th>
                    <th className="px-4 py-3 font-medium">Email</th>
                    <th className="px-4 py-3 font-medium">Projects</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Joined</th>
                    <th className="px-4 py-3 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-white/[0.04] last:border-0">
                      <td className="px-4 py-3 text-paper-100">
                        {u.full_name} {u.is_admin && <span className="ml-1.5 rounded bg-violet-500/20 px-1.5 py-0.5 text-[10px] text-violet-300">admin</span>}
                      </td>
                      <td className="px-4 py-3 text-paper-400">{u.email}</td>
                      <td className="px-4 py-3 text-paper-400">{u.project_count}</td>
                      <td className="px-4 py-3">
                        <span className={u.is_active ? "text-mint-400" : "text-red-400"}>
                          {u.is_active ? "Active" : "Suspended"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-paper-500">{new Date(u.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3 text-right">
                        {u.id !== currentUserId && (
                          <button
                            onClick={() => handleToggleActive(u.id, u.is_active)}
                            className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06]"
                            title={u.is_active ? "Suspend user" : "Reactivate user"}
                          >
                            {u.is_active ? <ShieldOff size={15} /> : <ShieldCheck size={15} />}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {tab === "projects" && (
          <div className="glass-panel overflow-hidden rounded-2xl">
            {projectsLoading || !projects ? (
              <div className="flex justify-center py-16"><Loader2 size={22} className="animate-spin text-violet-400" /></div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-xs text-paper-500">
                    <th className="px-4 py-3 font-medium">Project</th>
                    <th className="px-4 py-3 font-medium">Owner</th>
                    <th className="px-4 py-3 font-medium">Shared</th>
                    <th className="px-4 py-3 font-medium">Updated</th>
                    <th className="px-4 py-3 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr key={p.id} className="border-b border-white/[0.04] last:border-0">
                      <td className="px-4 py-3 text-paper-100">{p.name}</td>
                      <td className="px-4 py-3 text-paper-400">{p.owner_name} ({p.owner_email})</td>
                      <td className="px-4 py-3 text-paper-400">{p.is_shared ? "Yes" : "No"}</td>
                      <td className="px-4 py-3 text-paper-500">{new Date(p.updated_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleDeleteProject(p.id, p.name)}
                          className="rounded-lg p-1.5 text-paper-400 hover:bg-red-500/10 hover:text-red-400"
                          title="Delete project"
                        >
                          <Trash2 size={15} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
