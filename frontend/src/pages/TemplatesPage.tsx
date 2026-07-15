import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, LayoutTemplate, Sparkles } from "lucide-react";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { api } from "@/api/client";
import { fetchTemplates, loadTemplate } from "@/api/templates";
import type { Project } from "@/types";

export default function TemplatesPage() {
  const navigate = useNavigate();
  const [creatingId, setCreatingId] = useState<string | null>(null);

  const { data: templates, isLoading } = useQuery({
    queryKey: ["templates"],
    queryFn: fetchTemplates,
  });

  const categories = Array.from(new Set((templates ?? []).map((t) => t.category)));

  async function handleUseTemplate(templateId: string, name: string) {
    setCreatingId(templateId);
    try {
      const loaded = await loadTemplate(templateId);
      const { data: project } = await api.post<Project>("/projects", { name });
      await api.put(`/projects/${project.id}/autosave`, {
        canvas_data: {
          nodes: loaded.nodes,
          edges: loaded.edges,
          strokes: [],
          viewport: { x: 0, y: 0, zoom: 1 },
        },
      });
      navigate(`/editor/${project.id}`);
    } finally {
      setCreatingId(null);
    }
  }

  return (
    <div className="flex h-screen bg-ink-950">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="mb-8">
          <h1 className="font-display text-2xl font-semibold text-paper-100">Templates</h1>
          <p className="mt-1 text-sm text-paper-500">
            Start from a ready-made flowchart instead of a blank canvas.
          </p>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-24">
            <Loader2 size={22} className="animate-spin text-violet-400" />
          </div>
        ) : (
          categories.map((category) => (
            <section key={category} className="mb-10">
              <h2 className="mb-4 font-display text-lg font-medium text-paper-100">{category}</h2>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
                {templates!
                  .filter((t) => t.category === category)
                  .map((t) => (
                    <button
                      key={t.id}
                      onClick={() => handleUseTemplate(t.id, t.name)}
                      disabled={creatingId !== null}
                      className="group flex flex-col items-start rounded-2xl border border-white/[0.06] bg-ink-900 p-5 text-left transition-all hover:border-violet-500/40 hover:shadow-glow-violet disabled:opacity-50"
                    >
                      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-violet-500/15">
                        {creatingId === t.id ? (
                          <Loader2 size={16} className="animate-spin text-violet-400" />
                        ) : (
                          <LayoutTemplate size={16} className="text-violet-400" />
                        )}
                      </div>
                      <p className="font-display text-sm font-medium text-paper-100">{t.name}</p>
                      <p className="mt-1.5 text-xs text-paper-500">{t.description}</p>
                      {!t.executable && (
                        <span
                          className="label-eyebrow mt-3 inline-flex items-center gap-1 !text-[10px]"
                          title="This diagram's structure is real, but it uses array/conceptual steps this tool's simulator can't run step-by-step yet."
                        >
                          <Sparkles size={10} /> Diagram only
                        </span>
                      )}
                    </button>
                  ))}
              </div>
            </section>
          ))
        )}
      </main>
    </div>
  );
}
