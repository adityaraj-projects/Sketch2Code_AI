import { useEffect, useState } from "react";
import { X, MessageSquare, Trash2, Loader2, Send } from "lucide-react";
import { useCanvasStore } from "@/store/useCanvasStore";
import { useAuthStore } from "@/store/useAuthStore";
import { addComment, deleteComment, fetchComments, type CommentOut } from "@/api/collaboration";

interface Props {
  open: boolean;
  onClose: () => void;
  projectId: string;
}

export function CommentsPanel({ open, onClose, projectId }: Props) {
  const nodes = useCanvasStore((s) => s.nodes);
  const selectedIds = useCanvasStore((s) => s.selectedIds);
  const currentUserId = useAuthStore((s) => s.user?.id);

  const [comments, setComments] = useState<CommentOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);

  async function loadComments() {
    setLoading(true);
    try {
      setComments(await fetchComments(projectId));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (open) loadComments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const selectedNode = selectedIds.length === 1 ? nodes.find((n) => n.id === selectedIds[0]) : undefined;

  async function handleAdd() {
    if (!text.trim()) return;
    setSending(true);
    try {
      if (selectedNode) {
        await addComment(projectId, text, { nodeId: selectedNode.id });
      } else {
        await addComment(projectId, text, { x: 400, y: 400 });
      }
      setText("");
      await loadComments();
    } finally {
      setSending(false);
    }
  }

  async function handleDelete(commentId: string) {
    await deleteComment(projectId, commentId);
    setComments((prev) => prev.filter((c) => c.id !== commentId));
  }

  function labelFor(comment: CommentOut): string {
    if (comment.node_id) {
      const node = nodes.find((n) => n.id === comment.node_id);
      return node ? `On "${node.text || node.type}"` : "On a shape";
    }
    return "On the canvas";
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <div className="glass-panel flex h-full w-full max-w-sm flex-col border-l border-white/10" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
          <div className="flex items-center gap-2">
            <MessageSquare size={18} className="text-violet-400" />
            <h2 className="font-display text-base font-medium text-paper-100">Comments</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-paper-100">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 size={20} className="animate-spin text-violet-400" />
            </div>
          ) : comments.length === 0 ? (
            <p className="py-8 text-center text-sm text-paper-500">No comments yet.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {comments.map((c) => (
                <div key={c.id} className="rounded-xl border border-white/10 bg-ink-950 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-violet-300">{c.author_name}</span>
                    {c.author_id === currentUserId && (
                      <button onClick={() => handleDelete(c.id)} className="text-paper-500 hover:text-red-400">
                        <Trash2 size={13} />
                      </button>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-paper-200">{c.text}</p>
                  <span className="mt-1.5 block text-[11px] text-paper-500">{labelFor(c)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-white/[0.06] px-4 py-3">
          <p className="mb-2 text-xs text-paper-500">
            {selectedNode ? `Commenting on "${selectedNode.text || selectedNode.type}"` : "Select a shape to comment on it directly, or comment generally."}
          </p>
          <div className="flex items-center gap-2">
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAdd()}
              placeholder="Add a comment…"
              className="input-field flex-1 !py-2"
            />
            <button onClick={handleAdd} disabled={sending || !text.trim()} className="btn-primary !px-3 !py-2">
              {sending ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
