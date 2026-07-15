import { useNavigate } from "react-router-dom";
import { FolderClock, Plus, Calendar, FileText, ChevronRight, Copy, Pencil, Trash2 } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Sidebar } from "@/components/dashboard/Sidebar";
import type { Project, ProjectSummary } from "@/types";

export default function RecentProjectsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: projects, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: async () => (await api.get<ProjectSummary[]>("/projects")).data,
  });

  async function handleCreate() {
    const { data } = await api.post<Project>("/projects", { name: "Untitled Flowchart" });
    navigate(`/editor/${data.id}`);
  }

  async function handleRename(id: string, name: string) {
    await api.patch(`/projects/${id}/rename`, { name });
    queryClient.invalidateQueries({ queryKey: ["projects"] });
  }

  async function handleDuplicate(id: string) {
    await api.post(`/projects/${id}/duplicate`);
    queryClient.invalidateQueries({ queryKey: ["projects"] });
  }

  async function handleDelete(id: string) {
    await api.delete(`/projects/${id}`);
    queryClient.invalidateQueries({ queryKey: ["projects"] });
  }

  function getTimelineGroup(updatedAtStr: string): "Today" | "Yesterday" | "This Week" | "Older" {
    const date = new Date(updatedAtStr);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const startOfWeek = new Date(today);
    startOfWeek.setDate(startOfWeek.getDate() - 7);

    const targetDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    if (targetDate.getTime() === today.getTime()) {
      return "Today";
    } else if (targetDate.getTime() === yesterday.getTime()) {
      return "Yesterday";
    } else if (targetDate.getTime() >= startOfWeek.getTime()) {
      return "This Week";
    } else {
      return "Older";
    }
  }

  function getRelativeTime(dateStr: string): string {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;

    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // Filter or limit to recently updated projects
  const recentProjects = projects ? projects.slice(0, 15) : [];

  // Group by timeline recency
  const groups: Record<"Today" | "Yesterday" | "This Week" | "Older", ProjectSummary[]> = {
    Today: [],
    Yesterday: [],
    "This Week": [],
    Older: [],
  };

  recentProjects.forEach((p) => {
    const group = getTimelineGroup(p.updated_at);
    groups[group].push(p);
  });

  const timelineKeys: ("Today" | "Yesterday" | "This Week" | "Older")[] = [
    "Today",
    "Yesterday",
    "This Week",
    "Older",
  ];

  return (
    <div className="flex h-screen bg-ink-950">
      <Sidebar />

      <main className="flex-1 overflow-y-auto p-8 select-none">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="font-display text-2xl font-semibold text-paper-100 flex items-center gap-2">
              <FolderClock className="text-violet-400" size={24} /> Recent Activity
            </h1>
            <p className="mt-1 text-sm text-paper-500">
              Chronological timeline of your recent flowchart edits and sketches.
            </p>
          </div>
          <button onClick={handleCreate} className="btn-primary">
            <Plus size={16} /> New Project
          </button>
        </div>

        {isLoading ? (
          <div className="flex flex-col gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-xl bg-ink-900" />
            ))}
          </div>
        ) : recentProjects.length > 0 ? (
          <div className="flex flex-col gap-8">
            {timelineKeys.map((key) => {
              const list = groups[key];
              if (list.length === 0) return null;

              return (
                <div key={key} className="flex flex-col gap-3">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-paper-500">
                    <Calendar size={13} className="text-violet-500/70" />
                    <span>{key}</span>
                  </div>

                  <div className="flex flex-col gap-2.5">
                    {list.map((p) => {
                      const match = p.name.match(/^\[(.*?)\]\s*(.*)$/);
                      const categoryName = match ? match[1].trim() : null;
                      const displayName = match ? match[2].trim() : p.name;

                      return (
                        <div
                          key={p.id}
                          onClick={() => navigate(`/editor/${p.id}`)}
                          className="group relative flex items-center justify-between p-4 rounded-xl border border-white/[0.04] bg-white/[0.01] hover:bg-white/[0.04] hover:border-violet-500/30 transition-all cursor-pointer"
                        >
                          <div className="flex items-center gap-3.5 min-w-0 flex-1">
                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-500/10 border border-violet-500/20 text-violet-400 group-hover:bg-violet-500/20 group-hover:text-white transition-all">
                              <FileText size={18} />
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="truncate text-sm font-medium text-paper-100 flex items-center gap-2">
                                {categoryName && (
                                  <span className="shrink-0 inline-block rounded bg-violet-500/25 px-1.5 py-0.5 text-[9px] font-semibold text-violet-300 border border-violet-500/30">
                                    {categoryName}
                                  </span>
                                )}
                                <span className="truncate">{displayName}</span>
                              </p>
                              <p className="text-xs text-paper-500 mt-0.5">
                                Updated {getRelativeTime(p.updated_at)}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 ml-4 shrink-0" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => {
                                const name = window.prompt("Rename project", p.name);
                                if (name) handleRename(p.id, name);
                              }}
                              className="opacity-0 group-hover:opacity-100 rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-white transition-all"
                              title="Rename"
                            >
                              <Pencil size={14} />
                            </button>
                            <button
                              onClick={() => handleDuplicate(p.id)}
                              className="opacity-0 group-hover:opacity-100 rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-white transition-all"
                              title="Duplicate"
                            >
                              <Copy size={14} />
                            </button>
                            <button
                              onClick={() => {
                                if (window.confirm(`Delete "${p.name}"? This can't be undone.`)) {
                                  handleDelete(p.id);
                                }
                              }}
                              className="opacity-0 group-hover:opacity-100 rounded-lg p-1.5 text-red-500/70 hover:bg-red-500/10 hover:text-red-400 transition-all"
                              title="Delete"
                            >
                              <Trash2 size={14} />
                            </button>
                            <ChevronRight size={16} className="text-paper-500 group-hover:text-paper-300 transition-colors ml-1" />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.02] border border-white/5 text-paper-500">
              <FolderClock size={24} />
            </div>
            <h3 className="font-display text-base font-medium text-paper-200">No recent activity</h3>
            <p className="mt-1 text-sm text-paper-500 max-w-xs">
              Draw a new flowchart or duplicate a template to see it here!
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
