import { useEffect, useRef, useState, useCallback } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { useCanvasStore } from "@/store/useCanvasStore";

export interface RemoteCursor {
  userId: string;
  userName: string;
  color: string;
  x: number;
  y: number;
}

export interface Participant {
  user_id: string;
  user_name: string;
  color: string;
}

const CURSOR_THROTTLE_MS = 60;
const CANVAS_SYNC_DEBOUNCE_MS = 400;

/**
 * Connects to this project's live collaboration session. Canvas sync here
 * is deliberately simple last-write-wins broadcast (whoever's change
 * arrives last "wins" on every other client) rather than an operational-
 * transform/CRDT merge — the same concurrency model this app's autosave
 * already uses, just propagated live instead of only on reload.
 */
export function useCollaboration(projectId: string | undefined, enabled: boolean) {
  const [remoteCursors, setRemoteCursors] = useState<Record<string, RemoteCursor>>({});
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [connected, setConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const lastCursorSentRef = useRef(0);
  const applyingRemoteRef = useRef(false);
  const syncTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const accessToken = useAuthStore((s) => s.accessToken);
  const applyRemoteSnapshot = useCanvasStore((s) => s.applyRemoteSnapshot);

  useEffect(() => {
    if (!enabled || !projectId || !accessToken) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/ws/projects/${projectId}?token=${accessToken}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "presence") {
        setParticipants(message.participants);
        setRemoteCursors((prev) => {
          const stillPresent = new Set(message.participants.map((p: Participant) => p.user_id));
          const next: Record<string, RemoteCursor> = {};
          for (const [id, cursor] of Object.entries(prev)) {
            if (stillPresent.has(id)) next[id] = cursor;
          }
          return next;
        });
      } else if (message.type === "cursor") {
        setRemoteCursors((prev) => ({
          ...prev,
          [message.user_id]: {
            userId: message.user_id,
            userName: message.user_name,
            color: message.color,
            x: message.x,
            y: message.y,
          },
        }));
      } else if (message.type === "canvas_op") {
        const snapshot = message.op;
        applyingRemoteRef.current = true;
        applyRemoteSnapshot(snapshot.nodes, snapshot.edges, snapshot.strokes);
        applyingRemoteRef.current = false;
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, enabled, accessToken]);

  const sendCursor = useCallback((x: number, y: number) => {
    const now = Date.now();
    if (now - lastCursorSentRef.current < CURSOR_THROTTLE_MS) return;
    lastCursorSentRef.current = now;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "cursor", x, y }));
    }
  }, []);

  useEffect(() => {
    if (!enabled || !connected) return;
    const unsubscribe = useCanvasStore.subscribe((state, prevState) => {
      if (applyingRemoteRef.current) return;
      if (state.nodes === prevState.nodes && state.edges === prevState.edges && state.strokes === prevState.strokes) {
        return;
      }
      if (syncTimeoutRef.current) clearTimeout(syncTimeoutRef.current);
      syncTimeoutRef.current = setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const { nodes, edges, strokes } = useCanvasStore.getState();
          wsRef.current.send(JSON.stringify({ type: "canvas_op", op: { nodes, edges, strokes } }));
        }
      }, CANVAS_SYNC_DEBOUNCE_MS);
    });
    return () => {
      unsubscribe();
      if (syncTimeoutRef.current) clearTimeout(syncTimeoutRef.current);
    };
  }, [enabled, connected]);

  return { remoteCursors, participants, connected, sendCursor };
}
