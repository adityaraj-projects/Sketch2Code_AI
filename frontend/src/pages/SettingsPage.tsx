import { Sidebar } from "@/components/dashboard/Sidebar";
import { useSettingsStore, type AutosaveInterval } from "@/store/useSettingsStore";
import clsx from "clsx";

const AUTOSAVE_OPTIONS: { value: AutosaveInterval; label: string }[] = [
  { value: 1000, label: "1 second" },
  { value: 2000, label: "2 seconds" },
  { value: 5000, label: "5 seconds" },
  { value: 10000, label: "10 seconds" },
  { value: "manual", label: "Manual only" },
];

const SHORTCUTS: { keys: string; action: string }[] = [
  { keys: "V", action: "Select tool" },
  { keys: "H", action: "Pan tool" },
  { keys: "R", action: "Process (rectangle)" },
  { keys: "D", action: "Decision (diamond)" },
  { keys: "O", action: "Start / End (oval)" },
  { keys: "P", action: "Input / Output (parallelogram)" },
  { keys: "A", action: "Arrow" },
  { keys: "L", action: "Connector" },
  { keys: "T", action: "Text" },
  { keys: "F", action: "Freehand pen" },
  { keys: "G", action: "Highlighter" },
  { keys: "E", action: "Eraser" },
  { keys: "Ctrl/Cmd + Z", action: "Undo" },
  { keys: "Ctrl/Cmd + Shift + Z", action: "Redo" },
  { keys: "Ctrl/Cmd + C / V", action: "Copy / Paste selection" },
  { keys: "Delete / Backspace", action: "Delete selection" },
  { keys: "Escape", action: "Deselect / back to Select tool" },
];

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={clsx(
        "relative h-6 w-11 shrink-0 rounded-full transition-colors",
        checked ? "bg-violet-500" : "bg-white/10"
      )}
    >
      <span
        className={clsx(
          "absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform",
          checked ? "translate-x-[22px]" : "translate-x-0.5"
        )}
      />
    </button>
  );
}

function SettingRow({ title, description, control }: { title: string; description: string; control: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-white/[0.06] py-4 last:border-0">
      <div>
        <p className="text-sm text-paper-100">{title}</p>
        <p className="mt-0.5 text-xs text-paper-500">{description}</p>
      </div>
      {control}
    </div>
  );
}

export default function SettingsPage() {
  const {
    autosaveInterval, setAutosaveInterval,
    snapToGrid, setSnapToGrid,
    showGrid, setShowGrid,
    reduceMotion, setReduceMotion,
  } = useSettingsStore();

  return (
    <div className="flex h-screen bg-ink-950">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="mb-8">
          <h1 className="font-display text-2xl font-semibold text-paper-100">Settings</h1>
          <p className="mt-1 text-sm text-paper-500">
            These preferences are saved on this device and apply across all your projects.
          </p>
        </div>

        <div className="max-w-2xl space-y-8">
          <section className="glass-panel rounded-2xl p-6">
            <h2 className="font-display text-base font-medium text-paper-100">Autosave</h2>
            <SettingRow
              title="Save interval"
              description="How often edits are saved to the server while you work. Manual mode adds a Save button in the editor instead."
              control={
                <select
                  value={autosaveInterval}
                  onChange={(e) => {
                    const v = e.target.value;
                    setAutosaveInterval(v === "manual" ? "manual" : (Number(v) as AutosaveInterval));
                  }}
                  className="input-field w-40 !py-1.5 text-xs"
                >
                  {AUTOSAVE_OPTIONS.map((o) => (
                    <option key={String(o.value)} value={o.value}>{o.label}</option>
                  ))}
                </select>
              }
            />
          </section>

          <section className="glass-panel rounded-2xl p-6">
            <h2 className="font-display text-base font-medium text-paper-100">Editor</h2>
            <SettingRow
              title="Snap to grid"
              description="Shapes snap to a 20px grid when you draw or drag them."
              control={<Toggle checked={snapToGrid} onChange={setSnapToGrid} />}
            />
            <SettingRow
              title="Show grid background"
              description="Toggle the dotted grid pattern behind your flowchart."
              control={<Toggle checked={showGrid} onChange={setShowGrid} />}
            />
            <SettingRow
              title="Reduce motion"
              description="Turns off animations across the app, independent of your system setting."
              control={<Toggle checked={reduceMotion} onChange={setReduceMotion} />}
            />
          </section>

          <section className="glass-panel rounded-2xl p-6">
            <h2 className="mb-2 font-display text-base font-medium text-paper-100">Keyboard shortcuts</h2>
            <div className="grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-2">
              {SHORTCUTS.map((s) => (
                <div key={s.keys} className="flex items-center justify-between border-b border-white/[0.04] py-1.5 text-sm last:border-0">
                  <span className="text-paper-300">{s.action}</span>
                  <kbd className="rounded-md border border-white/10 bg-ink-950 px-2 py-0.5 font-mono text-xs text-paper-200">
                    {s.keys}
                  </kbd>
                </div>
              ))}
            </div>
          </section>

          <section className="glass-panel rounded-2xl p-6">
            <h2 className="font-display text-base font-medium text-paper-100">Interface language</h2>
            <p className="mt-2 text-sm text-paper-500">
              English only for now — a multi-language interface isn't built yet, so there's
              no language switch here rather than one that doesn't actually translate anything.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
