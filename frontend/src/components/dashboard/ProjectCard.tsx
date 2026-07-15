import { useNavigate } from "react-router-dom";
import { MoreVertical, Trash2, Copy, Pencil } from "lucide-react";
import { useState } from "react";
import type { ProjectSummary } from "@/types";

interface Props {
  project: ProjectSummary;
  onRename: (id: string, name: string) => void;
  onDuplicate: (id: string) => void;
  onDelete: (id: string) => void;
}

export function ProjectCard({ project, onRename, onDuplicate, onDelete }: Props) {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const match = project.name.match(/^\[(.*?)\]\s*(.*)$/);
  const categoryName = match ? match[1].trim() : null;
  const displayName = match ? match[2].trim() : project.name;

  return (
    <div
      className="group relative cursor-pointer overflow-hidden rounded-2xl border border-white/[0.06] bg-ink-900 transition-all hover:border-violet-500/40 hover:shadow-glow-violet"
      onClick={() => navigate(`/editor/${project.id}`)}
    >
      <div className="flex h-36 items-center justify-center bg-grid-pattern bg-[length:20px_20px] bg-ink-950/60">
        {project.thumbnail_url ? (
          <img src={project.thumbnail_url} alt="" className="h-full w-full object-cover" />
        ) : (
          <span className="font-display text-3xl text-white/10">S2C</span>
        )}
      </div>

      <div className="flex items-center justify-between gap-2 p-3">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-paper-100 flex items-center gap-1.5">
            {categoryName && (
              <span className="shrink-0 inline-block rounded bg-violet-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-violet-300 border border-violet-500/25">
                {categoryName}
              </span>
            )}
            <span className="truncate">{displayName}</span>
          </p>
          <p className="text-xs text-paper-500 mt-0.5">
            {new Date(project.updated_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            })}
          </p>
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation();
            setMenuOpen((v) => !v);
          }}
          className="rounded-lg p-1.5 text-paper-500 hover:bg-white/[0.06] hover:text-paper-100"
        >
          <MoreVertical size={15} />
        </button>
      </div>

      {menuOpen && (
        <div
          className="glass-panel absolute bottom-14 right-3 z-10 w-40 overflow-hidden rounded-xl py-1"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => {
              const name = window.prompt("Rename project", project.name);
              if (name) onRename(project.id, name);
              setMenuOpen(false);
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-paper-300 hover:bg-white/[0.06]"
          >
            <Pencil size={14} /> Rename
          </button>
          <button
            onClick={() => {
              onDuplicate(project.id);
              setMenuOpen(false);
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-paper-300 hover:bg-white/[0.06]"
          >
            <Copy size={14} /> Duplicate
          </button>
          <button
            onClick={() => {
              if (window.confirm(`Delete "${project.name}"? This can't be undone.`)) {
                onDelete(project.id);
              }
              setMenuOpen(false);
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-400 hover:bg-red-500/10"
          >
            <Trash2 size={14} /> Delete
          </button>
        </div>
      )}
    </div>
  );
}
