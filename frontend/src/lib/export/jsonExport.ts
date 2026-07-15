import type { CanvasData } from "@/types";

export interface ProjectExportFile {
  format: "sketch2code-project";
  version: 1;
  exported_at: string;
  project_name: string;
  canvas_data: CanvasData;
}

export function buildProjectExportJson(projectName: string, canvasData: CanvasData): string {
  const file: ProjectExportFile = {
    format: "sketch2code-project",
    version: 1,
    exported_at: new Date().toISOString(),
    project_name: projectName,
    canvas_data: canvasData,
  };
  return JSON.stringify(file, null, 2);
}
