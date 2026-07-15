import { useRef, useState, useEffect } from "react";
import { X, Send, Loader2, Bot, User, Wand2, Copy, Check } from "lucide-react";
import { useCanvasStore } from "@/store/useCanvasStore";
import { sendChatMessage } from "@/api/chatassistant";
import type { FlowEdge, FlowNode } from "@/types";

interface Props {
  open: boolean;
  onClose: () => void;
}

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  intent?: string;
  data?: Record<string, unknown> | null;
}

const SUGGESTIONS = ["Any bugs in this?", "What's the time complexity?", "Generate this in Python", "Clean up the layout"];

export function ChatAssistantPanel({ open, onClose }: Props) {
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const replaceNodesAndEdges = useCanvasStore((s) => s.replaceNodesAndEdges);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const message = (text ?? input).trim();
    if (!message || sending) return;

    setMessages((prev) => [...prev, { role: "user", text: message }]);
    setInput("");
    setSending(true);
    try {
      const result = await sendChatMessage(message, nodes, edges);
      setMessages((prev) => [...prev, { role: "assistant", text: result.reply, intent: result.intent, data: result.data }]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: err?.response?.data?.detail ?? "Something went wrong. Please try again." },
      ]);
    } finally {
      setSending(false);
    }
  }

  function handleApplyBeautify(data: Record<string, unknown>) {
    replaceNodesAndEdges(data.nodes as FlowNode[], data.edges as FlowEdge[]);
  }

  function handleCopyCode(code: string, index: number) {
    navigator.clipboard.writeText(code);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 1500);
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <div
        className="glass-panel flex h-full w-full max-w-md flex-col border-l border-white/10"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
          <div className="flex items-center gap-2">
            <Bot size={18} className="text-violet-400" />
            <h2 className="font-display text-base font-medium text-paper-100">AI Assistant</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-paper-400 hover:bg-white/[0.06] hover:text-paper-100">
            <X size={18} />
          </button>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-5">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
              <Bot size={26} className="text-paper-500" />
              <p className="text-sm text-paper-500">
                Ask me to check for bugs, explain the logic, analyze complexity, generate code, or clean up the layout.
              </p>
              <div className="flex flex-wrap justify-center gap-1.5">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSend(s)}
                    className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-paper-300 hover:bg-white/[0.05]"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-col gap-4">
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-2.5 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
                <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${m.role === "user" ? "bg-white/[0.08]" : "bg-violet-500/20"}`}>
                  {m.role === "user" ? <User size={14} className="text-paper-300" /> : <Bot size={14} className="text-violet-400" />}
                </div>
                <div className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${m.role === "user" ? "bg-violet-500 text-white" : "bg-ink-950 text-paper-200 border border-white/10"}`}>
                  <div className="whitespace-pre-wrap">{m.text}</div>

                  {m.intent === "beautify" && m.data && (
                    <button
                      onClick={() => handleApplyBeautify(m.data!)}
                      className="btn-primary mt-3 !px-3 !py-1.5 text-xs"
                    >
                      <Wand2 size={13} /> Apply to canvas
                    </button>
                  )}
                  {m.intent === "generate_code" && m.data && (
                    <button
                      onClick={() => handleCopyCode(m.data!.code as string, i)}
                      className="btn-secondary mt-3 !px-3 !py-1.5 text-xs"
                    >
                      {copiedIndex === i ? <Check size={13} className="text-mint-400" /> : <Copy size={13} />}
                      {copiedIndex === i ? "Copied" : "Copy code"}
                    </button>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex items-center gap-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-500/20">
                  <Bot size={14} className="text-violet-400" />
                </div>
                <Loader2 size={16} className="animate-spin text-paper-500" />
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 border-t border-white/[0.06] px-4 py-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about this flowchart…"
            className="input-field flex-1 !py-2"
          />
          <button onClick={() => handleSend()} disabled={sending || !input.trim()} className="btn-primary !px-3 !py-2">
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
