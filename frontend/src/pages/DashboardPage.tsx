import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Folder } from "lucide-react";
import clsx from "clsx";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { ProjectCard } from "@/components/dashboard/ProjectCard";
import type { Project, ProjectSummary } from "@/types";

export default function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState("All");

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

  const categories = ["All"];
  projects?.forEach((p) => {
    const match = p.name.match(/^\[(.*?)\]/);
    if (match) {
      const cat = match[1].trim();
      if (!categories.includes(cat)) {
        categories.push(cat);
      }
    }
  });

  const filteredProjects = projects?.filter((p) => {
    if (selectedCategory === "All") return true;
    const match = p.name.match(/^\[(.*?)\]/);
    return match && match[1].trim() === selectedCategory;
  }) || [];

  return (
    <div className="flex h-screen bg-ink-950">
      <Sidebar />

      <main className="flex-1 overflow-y-auto p-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="font-display text-2xl font-semibold text-paper-100">My Projects</h1>
            <p className="mt-1 text-sm text-paper-500">
              Pick up where you left off, or start a new flowchart. Use brackets in your project name (e.g. <i>[Algorithms] Binary Search</i>) to group them in folders.
            </p>
          </div>
          <button onClick={handleCreate} className="btn-primary">
            <Plus size={16} /> New Project
          </button>
        </div>

        {projects && projects.length > 0 && categories.length > 1 && (
          <div className="mb-6 flex flex-wrap items-center gap-2 border-b border-white/[0.04] pb-4">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={clsx(
                  "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors border",
                  selectedCategory === cat
                    ? "bg-violet-500 text-white border-violet-500 shadow-glow-violet/30"
                    : "bg-white/[0.02] text-paper-400 border-white/5 hover:bg-white/[0.06] hover:text-paper-100"
                )}
              >
                <Folder size={12} className={selectedCategory === cat ? "text-white" : "text-paper-500"} />
                {cat}
              </button>
            ))}
          </div>
        )}

        {isLoading ? (
          <div className="grid grid-cols-2 gap-5 md:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-52 animate-pulse rounded-2xl bg-ink-900" />
            ))}
          </div>
        ) : filteredProjects.length > 0 ? (
          <div className="grid grid-cols-2 gap-5 md:grid-cols-3 lg:grid-cols-4">
            {filteredProjects.map((p) => (
              <ProjectCard
                key={p.id}
                project={p}
                onRename={handleRename}
                onDuplicate={handleDuplicate}
                onDelete={handleDelete}
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 py-24 text-center">
            <p className="font-display text-lg text-paper-100">No projects in this category</p>
            <p className="mt-1 text-sm text-paper-500">
              Draw your first flowchart and Sketch2Code AI will take it from here.
            </p>
            <button onClick={handleCreate} className="btn-primary mt-5">
              <Plus size={16} /> Create new project
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
