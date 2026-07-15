import { Line } from "react-konva";
import type { FreehandStroke } from "@/types";

interface Props {
  stroke: FreehandStroke;
}

/**
 * Draws a freehand stroke using React-Konva's Line component.
 * Tension adds Catmull-Rom spline interpolation, which makes the drawing
 * look smooth like Microsoft Whiteboard instead of jagged line segments.
 */
export function StrokeShape({ stroke }: Props) {
  const isEraser = stroke.tool === "eraser";
  const isHighlighter = stroke.tool === "highlighter";

  return (
    <Line
      points={stroke.points}
      stroke={stroke.color}
      strokeWidth={isHighlighter ? stroke.width * 2.5 : stroke.width}
      lineCap="round"
      lineJoin="round"
      globalCompositeOperation={isEraser ? "destination-out" : "source-over"}
      opacity={isHighlighter ? 0.35 : 1}
      tension={0.35}
      listening={false}
    />
  );
}
