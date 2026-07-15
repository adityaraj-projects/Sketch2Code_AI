import type { Participant, RemoteCursor } from "@/hooks/useCollaboration";
import type { Viewport } from "@/types";
import { MousePointer2 } from "lucide-react";

export function PresenceBar({ participants, connected }: { participants: Participant[]; connected: boolean }) {
  if (!connected || participants.length <= 1) return null;

  return (
    <div className="glass-panel absolute right-4 top-4 z-20 flex items-center gap-1.5 rounded-full px-2.5 py-1.5">
      {participants.slice(0, 5).map((p) => (
        <div
          key={p.user_id}
          title={p.user_name}
          className="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-medium text-white ring-2 ring-ink-900"
          style={{ backgroundColor: p.color }}
        >
          {p.user_name.charAt(0).toUpperCase()}
        </div>
      ))}
      {participants.length > 5 && (
        <span className="pl-1 text-xs text-paper-400">+{participants.length - 5}</span>
      )}
    </div>
  );
}

export function RemoteCursorsOverlay({
  cursors,
  viewport,
}: {
  cursors: Record<string, RemoteCursor>;
  viewport: Viewport;
}) {
  return (
    <div className="pointer-events-none absolute inset-0 z-10 overflow-hidden">
      {Object.values(cursors).map((cursor) => {
        const screenX = cursor.x * viewport.zoom + viewport.x;
        const screenY = cursor.y * viewport.zoom + viewport.y;
        return (
          <div
            key={cursor.userId}
            className="absolute transition-transform duration-75 ease-out"
            style={{ transform: `translate(${screenX}px, ${screenY}px)` }}
          >
            <MousePointer2 size={18} style={{ color: cursor.color }} fill={cursor.color} />
            <span
              className="ml-4 -mt-1 inline-block rounded-md px-1.5 py-0.5 text-[10px] font-medium text-white"
              style={{ backgroundColor: cursor.color }}
            >
              {cursor.userName}
            </span>
          </div>
        );
      })}
    </div>
  );
}
