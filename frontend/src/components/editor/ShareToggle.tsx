import { useState } from "react";
import { Share2, Check, Loader2, Copy } from "lucide-react";
import { setProjectSharing } from "@/api/collaboration";

interface Props {
  projectId: string;
  isShared: boolean;
  onChanged: (isShared: boolean) => void;
}

export function ShareToggle({ projectId, isShared, onChanged }: Props) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleToggle() {
    setBusy(true);
    try {
      const next = !isShared;
      await setProjectSharing(projectId, next);
      onChanged(next);
    } finally {
      setBusy(false);
    }
  }

  function handleCopyLink() {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className={`btn-secondary !px-3 !py-1.5 text-xs ${isShared ? "!border-mint-400/30 !text-mint-400" : ""}`}
      >
        <Share2 size={14} /> {isShared ? "Shared" : "Share"}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="glass-panel absolute right-0 top-full z-20 mt-2 w-64 rounded-xl p-4">
            <p className="text-sm text-paper-100">Collaborative access</p>
            <p className="mt-1 text-xs text-paper-500">
              {isShared
                ? "Anyone signed in with this link can view, edit, and comment in real time."
                : "Only you can access this project right now."}
            </p>
            <button onClick={handleToggle} disabled={busy} className="btn-primary mt-3 w-full !py-1.5 text-xs">
              {busy ? <Loader2 size={13} className="animate-spin" /> : isShared ? <Check size={13} /> : <Share2 size={13} />}
              {isShared ? "Turn off sharing" : "Enable sharing"}
            </button>
            {isShared && (
              <button onClick={handleCopyLink} className="btn-secondary mt-2 w-full !py-1.5 text-xs">
                <Copy size={13} /> {copied ? "Copied!" : "Copy link"}
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
