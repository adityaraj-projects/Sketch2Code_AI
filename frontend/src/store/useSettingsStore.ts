import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AutosaveInterval = 1000 | 2000 | 5000 | 10000 | "manual";
export type CanvasTheme = "dark" | "light" | "chalkboard";

interface SettingsState {
  autosaveInterval: AutosaveInterval;
  snapToGrid: boolean;
  gridSize: number;
  showGrid: boolean;
  reduceMotion: boolean;
  theme: CanvasTheme;

  setAutosaveInterval: (interval: AutosaveInterval) => void;
  setSnapToGrid: (value: boolean) => void;
  setShowGrid: (value: boolean) => void;
  setReduceMotion: (value: boolean) => void;
  setTheme: (theme: CanvasTheme) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      autosaveInterval: 2000,
      snapToGrid: false,
      gridSize: 20,
      showGrid: true,
      reduceMotion: false,
      theme: "dark",

      setAutosaveInterval: (interval) => set({ autosaveInterval: interval }),
      setSnapToGrid: (value) => set({ snapToGrid: value }),
      setShowGrid: (value) => set({ showGrid: value }),
      setReduceMotion: (value) => set({ reduceMotion: value }),
      setTheme: (theme) => set({ theme }),
    }),
    { name: "sketch2code-settings" }
  )
);
