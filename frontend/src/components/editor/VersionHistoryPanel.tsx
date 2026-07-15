import { useEffect, useState } from "react";
import { X, History, RotateCcw, Loader2, Save } from "lucide-react";
import { fetchVersions, restoreVersion, saveVersion, type VersionSummary } from "@/api/collaboration";
import { api } from "@/api/client";
import { useCanvasStore } from "@/store/useCanvasStore";

interface Props {
  open: boolean;
  onClose: () => void;
  projectId: string;
}

export function VersionHistoryPanel({ open, onClose, projectId }: Props) {
  const [versions, setVersions] = useState<VersionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [restoringId, setRestoringId] = useState<string | null>(null);
  const loadProject = useCanvasStore((s) => s.loadProject);
  const projectName = useCanvasStore((s) => s.projectName);

  async function load() {
    setLoading(true);
    try {
      setVersions(await fetchVersions(projectId));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (open) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  async function handleSaveVersion() {
    const label = window.prompt("Label for this checkpoint (optional)", "");
    setSaving(true);
    try {
      await saveVersion(projectId, label || undefined);
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function handleRestore(versionId: string) {
    if (!window.confirm("Restore this version? Your current canvas will be replaced (a checkpoint of the current state is saved first, so you can undo this by restoring again).")) {
      return;
    }
    setRestoringId(versionId);
    try {
      await restoreVersion(projectId, versionId);
      const { data } = await api.get(`/projects/${projectId}`);
      loadProject(data.id, data.name, data.canvas_data);
      await load();
    } finally {
      setRestoringId(null);
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <div className="glass-panel flex h-full w-full max-w-sm flex-col border-l border-white/10" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
          <div className="flex items-center gap-2">
            <History size={18} className="text-violet-400" />
            <h2 className="font-display text-base font-medium text-paper-100">Version History</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-paper-100">
            <X size={18} />
          </button>
        </div>

        <div className="border-b border-white/[0.06] px-5 py-3">
          <button onClick={handleSaveVersion} disabled={saving} className="btn-primary w-full !py-2 text-sm">
            {saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
            Save current state as a checkpoint
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 size={20} className="animate-spin text-violet-400" />
            </div>
          ) : versions.length === 0 ? (
            <p className="py-8 text-center text-sm text-paper-500">
              No checkpoints yet for "{projectName}" — save one above.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {versions.map((v) => (
                <div key={v.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-ink-950 p-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm text-paper-100">{v.label}</p>
                    <p className="text-xs text-paper-500">
                      {v.created_by_name} · {new Date(v.created_at).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                  <button
                    onClick={() => handleRestore(v.id)}
                    disabled={restoringId !== null}
                    title="Restore this version"
                    className="ml-2 shrink-0 rounded-lg p-2 text-paper-400 hover:bg-white/[0.06] hover:text-violet-300"
                  >
                    {restoringId === v.id ? <Loader2 size={15} className="animate-spin" /> : <RotateCcw size={15} />}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
