import { useEffect, useRef, useState } from "react";
import type Konva from "konva";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import clsx from "clsx";
import {
  ArrowLeft, Cloud, CloudOff, Loader2, Code2, Workflow, PlayCircle, Sparkles, Gauge, Bug, Bot, Save, Mic,
  MessageSquare, History, Sun, Moon, Palette, ChevronDown, Maximize2, Minimize2, Share2, Download, Wand2,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { CanvasEditor } from "@/canvas/CanvasEditor";
import { useCanvasStore } from "@/store/useCanvasStore";
import { useSettingsStore } from "@/store/useSettingsStore";
import { useAutosave } from "@/hooks/useAutosave";
import { useCollaboration } from "@/hooks/useCollaboration";
import { CodeGenPanel } from "@/components/editor/CodeGenPanel";
import { CodeToFlowchartPanel } from "@/components/editor/CodeToFlowchartPanel";
import { ExecutionPanel } from "@/components/editor/ExecutionPanel";
import { ExplainerPanel } from "@/components/editor/ExplainerPanel";
import { ComplexityPanel } from "@/components/editor/ComplexityPanel";
import { BugDetectorPanel } from "@/components/editor/BugDetectorPanel";
import { BeautifyButton } from "@/components/editor/BeautifyButton";
import { RecognizeButton } from "@/canvas/RecognizeButton";
import { ChatAssistantPanel } from "@/components/editor/ChatAssistantPanel";
import { VoiceModePanel } from "@/components/editor/VoiceModePanel";
import { ExportMenu } from "@/components/editor/ExportMenu";
// import { ShareToggle } from "@/components/editor/ShareToggle";
import { CommentsPanel } from "@/components/editor/CommentsPanel";
import { VersionHistoryPanel } from "@/components/editor/VersionHistoryPanel";
import type { Project } from "@/types";

function SaveStatusIndicator({ status, onSaveNow, manual }: { status: string; onSaveNow: () => void; manual: boolean }) {
  if (status === "saving") {
    return (
      <span className="flex items-center gap-1.5 text-xs text-paper-500">
        <Loader2 size={13} className="animate-spin" /> Saving…
      </span>
    );
  }
  if (status === "error") {
    return (
      <button onClick={onSaveNow} className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300">
        <CloudOff size={13} /> Couldn't save — retry
      </button>
    );
  }
  if (manual) {
    return (
      <button onClick={onSaveNow} className="flex items-center gap-1.5 text-xs text-paper-300 hover:text-paper-100">
        <Save size={13} /> Save now
      </button>
    );
  }
  return (
    <span className="flex items-center gap-1.5 text-xs text-mint-400">
      <Cloud size={13} /> Saved
    </span>
  );
}

function ThemeSelector() {
  const theme = useSettingsStore((s) => s.theme);
  const setTheme = useSettingsStore((s) => s.setTheme);

  return (
    <div className="flex items-center rounded-lg bg-white/[0.04] p-0.5 border border-white/10 shrink-0">
      <button
        onClick={() => setTheme("dark")}
        title="Dark Theme"
        className={clsx(
          "rounded-md p-1 text-[11px] transition-colors",
          theme === "dark" ? "bg-violet-500 text-white" : "text-paper-400 hover:text-paper-100"
        )}
      >
        <Moon size={12} />
      </button>
      <button
        onClick={() => setTheme("light")}
        title="Light Theme"
        className={clsx(
          "rounded-md p-1 text-[11px] transition-colors",
          theme === "light" ? "bg-violet-500 text-white" : "text-paper-400 hover:text-paper-100"
        )}
      >
        <Sun size={12} />
      </button>
      <button
        onClick={() => setTheme("chalkboard")}
        title="Chalkboard Theme"
        className={clsx(
          "rounded-md p-1 text-[11px] transition-colors",
          theme === "chalkboard" ? "bg-violet-500 text-white" : "text-paper-400 hover:text-paper-100"
        )}
      >
        <Palette size={12} />
      </button>
    </div>
  );
}

export default function EditorPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const viewOnly = searchParams.get("viewOnly") === "true" || searchParams.get("classroom") === "true";

  const loadProject = useCanvasStore((s) => s.loadProject);
  const projectName = useCanvasStore((s) => s.projectName);
  const { status: saveStatus, saveNow } = useAutosave();
  const isManualSave = useSettingsStore((s) => s.autosaveInterval === "manual");
  const [codePanelOpen, setCodePanelOpen] = useState(false);
  const [codeToFlowOpen, setCodeToFlowOpen] = useState(false);
  const [executionOpen, setExecutionOpen] = useState(false);
  const [explainerOpen, setExplainerOpen] = useState(false);
  const [complexityOpen, setComplexityOpen] = useState(false);
  const [bugDetectorOpen, setBugDetectorOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [commentsOpen, setCommentsOpen] = useState(false);
  const [versionsOpen, setVersionsOpen] = useState(false);
  const [isShared, setIsShared] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [boardMenuOpen, setBoardMenuOpen] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [timerActive, setTimerActive] = useState(false);
  const [timerMode, setTimerMode] = useState<"stopwatch" | "countdown">("stopwatch");
  const [countdownStart, setCountdownStart] = useState(900); // default 15m
  const stageRef = useRef<Konva.Stage>(null);
  const boardMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (boardMenuRef.current && !boardMenuRef.current.contains(event.target as Node)) {
        setBoardMenuOpen(false);
      }
    }
    if (boardMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [boardMenuOpen]);

  useEffect(() => {
    function handleFullscreenChange() {
      setIsFullscreen(!!document.fullscreenElement);
    }
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  useEffect(() => {
    let interval: any;
    if (timerActive) {
      interval = setInterval(() => {
        setTimerSeconds((prev) => {
          if (timerMode === "countdown") {
            if (prev <= 1) {
              setTimerActive(false);
              window.alert("⏰ Time's up! Great job practicing!");
              return 0;
            }
            return prev - 1;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [timerActive, timerMode]);

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => {
        console.error("Error attempting to enable fullscreen:", err);
      });
    } else {
      document.exitFullscreen();
    }
  }

  function formatTime(secs: number) {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }

  const { data, isLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: async () => (await api.get<Project>(`/projects/${projectId}`)).data,
    enabled: !!projectId,
  });

  const { remoteCursors, participants, connected, sendCursor } = useCollaboration(projectId, isShared);

  useEffect(() => {
    if (data) {
      loadProject(data.id, data.name, data.canvas_data);
      setIsShared(data.is_shared);
    }
  }, [data, loadProject]);

  if (isLoading || !data) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-ink-950">
        <Loader2 className="animate-spin text-violet-500" size={28} />
      </div>
    );
  }

  return (
    <div className="relative h-screen w-screen bg-ink-950">
      <header className="glass-panel border-b border-white/10 absolute left-0 right-0 top-0 z-30 h-14 flex items-center justify-between px-6 rounded-none select-none">
        {viewOnly ? (
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => navigate("/dashboard")}
              className="rounded-lg p-1.5 text-paper-300 hover:bg-white/[0.06] hover:text-paper-100"
            >
              <ArrowLeft size={18} />
            </button>
            <span className="font-display text-sm font-medium text-paper-100">{projectName}</span>
            <span className="inline-flex items-center gap-1 rounded-full bg-violet-500/20 px-2.5 py-0.5 text-xs font-semibold text-violet-300 border border-violet-500/30 animate-pulse">
              Classroom View (Read-Only)
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => navigate("/dashboard")}
              className="rounded-lg p-1.5 text-paper-300 hover:bg-white/[0.06] hover:text-paper-100"
              title="Back to Dashboard"
            >
              <ArrowLeft size={18} />
            </button>
            <span className="font-display text-sm font-medium text-paper-100">{projectName}</span>
            
            {/* Board Options Dropdown Menu */}
            <div className="relative" ref={boardMenuRef}>
              <button
                onClick={() => setBoardMenuOpen(!boardMenuOpen)}
                className="rounded-md px-1.5 py-1 text-xs text-paper-400 hover:bg-white/[0.06] hover:text-paper-100 transition-colors flex items-center gap-1 font-semibold border border-white/10"
                title="Board Menu"
              >
                <span>Menu</span>
                <ChevronDown size={12} />
              </button>
              {boardMenuOpen && (
                <div className="glass-panel absolute left-0 top-full z-50 mt-2 w-60 rounded-xl py-2 shadow-2xl border border-white/10 bg-ink-900 overflow-y-auto max-h-[85vh]">
                  {/* Category 1: Flowchart Operations */}
                    <div className="px-3 py-1">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-paper-500">Flowchart</span>
                      <div className="mt-1 flex flex-col gap-0.5">
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            document.getElementById("btn-beautify-trigger")?.click();
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <Wand2 size={13} className="text-violet-400" />
                          <span>Beautify Layout</span>
                        </button>
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            setExecutionOpen(true);
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <PlayCircle size={13} className="text-mint-400" />
                          <span>Run Simulation</span>
                        </button>
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            setCodeToFlowOpen(true);
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <Workflow size={13} className="text-violet-400" />
                          <span>Code → Flowchart</span>
                        </button>
                      </div>
                    </div>

                    <div className="my-1.5 h-px bg-white/10" />

                    {/* Category 2: AI & Sketching */}
                    <div className="px-3 py-1">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-paper-500">AI Assistants</span>
                      <div className="mt-1 flex flex-col gap-0.5">
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            document.getElementById("btn-recognize-trigger")?.click();
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <Sparkles size={13} className="text-violet-400" />
                          <span>Recognize Sketch</span>
                        </button>
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            setChatOpen(true);
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <Bot size={13} className="text-violet-400" />
                          <span>Ask AI Chatbot</span>
                        </button>
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            setVoiceOpen(true);
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <Mic size={13} className="text-violet-400" />
                          <span>Voice Commands</span>
                        </button>
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            setExplainerOpen(true);
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <Sparkles size={13} className="text-violet-400" />
                          <span>Explain Flowchart</span>
                        </button>
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            setBugDetectorOpen(true);
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <Bug size={13} className="text-red-400" />
                          <span>Bug Detector</span>
                        </button>
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            setComplexityOpen(true);
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <Gauge size={13} className="text-mint-400" />
                          <span>Complexity Analyzer</span>
                        </button>
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            setCodePanelOpen(true);
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <Code2 size={13} className="text-violet-400" />
                          <span>Generate Code</span>
                        </button>
                      </div>
                    </div>

                    <div className="my-1.5 h-px bg-white/10" />

                    {/* Category 3: Collaboration & History */}
                    <div className="px-3 py-1">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-paper-500">Collab & History</span>
                      <div className="mt-1 flex flex-col gap-0.5">
                        {projectId && (
                          <button
                            onClick={() => {
                              setBoardMenuOpen(false);
                              setVersionsOpen(true);
                            }}
                            className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                          >
                            <History size={13} />
                            <span>Version History</span>
                          </button>
                        )}
                        {projectId && (
                          <button
                            onClick={() => {
                              setBoardMenuOpen(false);
                              setCommentsOpen(true);
                            }}
                            className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                          >
                            <MessageSquare size={13} />
                            <span>Comments</span>
                          </button>
                        )}
                        {projectId && (
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(`${window.location.origin}/project/${projectId}?viewOnly=true`);
                              window.alert("🔗 Share link copied to clipboard!");
                              setBoardMenuOpen(false);
                            }}
                            className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                          >
                            <Share2 size={13} className="text-violet-400" />
                            <span>Copy Share Link</span>
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="my-1.5 h-px bg-white/10" />

                    {/* Category 4: Export */}
                    <div className="px-3 py-1">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-paper-500">Export</span>
                      <div className="mt-1 flex flex-col gap-0.5">
                        <button
                          onClick={() => {
                            setBoardMenuOpen(false);
                            document.getElementById("btn-export-trigger")?.click();
                          }}
                          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs text-paper-200 hover:bg-white/[0.06] w-full"
                        >
                          <Download size={13} className="text-mint-400" />
                          <span>Export Board Options</span>
                        </button>
                      </div>
                    </div>
                  </div>
              )}
            </div>
            
            <SaveStatusIndicator status={saveStatus} onSaveNow={saveNow} manual={isManualSave} />
          </div>
        )}

        <div className="flex items-center gap-2.5 shrink-0">
          {/* Practice Timer Widget */}
          <div className="flex items-center gap-1.5 rounded-lg bg-white/[0.04] px-2 py-0.5 border border-white/10 text-paper-200 text-xs shrink-0 select-none">
            <span className="text-[11px] font-mono font-bold tracking-wider text-violet-400">{formatTime(timerSeconds)}</span>
            <button
              onClick={() => setTimerActive(!timerActive)}
              className="text-[10px] text-paper-400 hover:text-paper-100 font-semibold transition-colors px-1"
              title={timerActive ? "Pause" : "Start"}
            >
              {timerActive ? "Pause" : "Start"}
            </button>
            <button
              onClick={() => {
                setTimerActive(false);
                setTimerSeconds(timerMode === "countdown" ? countdownStart : 0);
              }}
              className="text-[10px] text-paper-400 hover:text-paper-100 font-semibold transition-colors px-1"
              title="Reset"
            >
              Reset
            </button>
            <select
              value={timerMode === "countdown" ? (countdownStart === 900 ? "15m" : countdownStart === 1800 ? "30m" : countdownStart === 2700 ? "45m" : "custom") : "stopwatch"}
              onChange={(e) => {
                const val = e.target.value;
                setTimerActive(false);
                if (val === "stopwatch") {
                  setTimerMode("stopwatch");
                  setTimerSeconds(0);
                } else if (val === "custom") {
                  const minsStr = window.prompt("Enter custom timer duration in minutes:", "20");
                  const mins = parseInt(minsStr ?? "");
                  if (mins && mins > 0) {
                    setTimerMode("countdown");
                    setCountdownStart(mins * 60);
                    setTimerSeconds(mins * 60);
                    setTimerActive(true);
                  }
                } else {
                  const mins = parseInt(val);
                  setTimerMode("countdown");
                  setCountdownStart(mins * 60);
                  setTimerSeconds(mins * 60);
                }
              }}
              className="bg-transparent text-[10px] text-paper-300 font-semibold border-none outline-none cursor-pointer hover:text-paper-100 pr-1"
            >
              <option value="stopwatch" className="bg-ink-950">Stopwatch</option>
              <option value="15m" className="bg-ink-950">15 min</option>
              <option value="30m" className="bg-ink-950">30 min</option>
              <option value="45m" className="bg-ink-950">45 min</option>
              <option value="custom" className="bg-ink-950">Custom...</option>
            </select>
          </div>

          <ThemeSelector />
          <button
            onClick={toggleFullscreen}
            className="btn-secondary !px-2 !py-1 text-[11px] h-7 shrink-0 flex items-center gap-1"
            title={isFullscreen ? "Exit Fullscreen (Esc)" : "Full Screen"}
          >
            {isFullscreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
            <span>{isFullscreen ? "Exit" : "Fullscreen"}</span>
          </button>
        </div>

        {/* Hidden Components for Event Trigger Bridging */}
        <div style={{ display: "none" }}>
          <RecognizeButton stageRef={stageRef} />
          <BeautifyButton />
          <ExportMenu stageRef={stageRef} onOpenCodeGen={() => setCodePanelOpen(true)} />
        </div>
      </header>

      <CanvasEditor
        externalStageRef={stageRef}
        remoteCursors={remoteCursors}
        participants={participants}
        isConnected={connected}
        onCursorMove={sendCursor}
        viewOnly={viewOnly}
      />
      <CodeGenPanel open={codePanelOpen} onClose={() => setCodePanelOpen(false)} />
      <CodeToFlowchartPanel open={codeToFlowOpen} onClose={() => setCodeToFlowOpen(false)} />
      <ExecutionPanel open={executionOpen} onClose={() => setExecutionOpen(false)} />
      <ExplainerPanel open={explainerOpen} onClose={() => setExplainerOpen(false)} />
      <ComplexityPanel open={complexityOpen} onClose={() => setComplexityOpen(false)} />
      <BugDetectorPanel open={bugDetectorOpen} onClose={() => setBugDetectorOpen(false)} />
      <ChatAssistantPanel open={chatOpen} onClose={() => setChatOpen(false)} />
      <VoiceModePanel open={voiceOpen} onClose={() => setVoiceOpen(false)} />
      {projectId && <CommentsPanel open={commentsOpen} onClose={() => setCommentsOpen(false)} projectId={projectId} />}
      {projectId && <VersionHistoryPanel open={versionsOpen} onClose={() => setVersionsOpen(false)} projectId={projectId} />}
    </div>
  );
}
