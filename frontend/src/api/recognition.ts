import { api } from "@/api/client";
import type { FreehandStroke, RecognizeResponse, Viewport } from "@/types";

interface SnapshotPayload {
  image_base64: string;
  viewport_x: number;
  viewport_y: number;
  viewport_zoom: number;
  pixel_ratio: number;
}

export async function recognizeFlowchart(
  strokes: FreehandStroke[],
  snapshot: { dataUrl: string; viewport: Viewport; pixelRatio: number } | null
): Promise<RecognizeResponse> {
  const payload: {
    strokes: Array<{
      id: string;
      tool: string;
      points: number[];
      pressures: number[];
      color: string;
      width: number;
    }>;
    snapshot?: SnapshotPayload;
  } = {
    strokes: strokes.map((s) => ({
      id: s.id,
      tool: s.tool,
      points: s.points,
      pressures: s.pressures,
      color: s.color,
      width: s.width,
    })),
  };

  if (snapshot) {
    payload.snapshot = {
      image_base64: snapshot.dataUrl.split(",")[1] ?? snapshot.dataUrl,
      viewport_x: snapshot.viewport.x,
      viewport_y: snapshot.viewport.y,
      viewport_zoom: snapshot.viewport.zoom,
      pixel_ratio: snapshot.pixelRatio,
    };
  }

  const { data } = await api.post<RecognizeResponse>("/recognition/flowchart", payload);
  return data;
}
