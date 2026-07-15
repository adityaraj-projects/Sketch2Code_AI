import { Arrow, Text } from "react-konva";
import type { FlowEdge } from "@/types";

interface Props {
  edge: FlowEdge;
  isSelected: boolean;
  theme?: "dark" | "light" | "chalkboard";
  onSelect: () => void;
  onDblClick: () => void;
}

export function EdgeShape({ edge, isSelected, theme = "dark", onSelect, onDblClick }: Props) {
  const midX = (edge.points[0] + edge.points[2]) / 2;
  const midY = (edge.points[1] + edge.points[3]) / 2;

  const defaultStroke =
    theme === "light"
      ? "#7C5CFF"
      : theme === "chalkboard"
      ? "#34D399"
      : "#7C5CFF";

  const strokeColor = edge.stroke === "#7C5CFF" ? defaultStroke : edge.stroke;
  const stroke = isSelected ? "#7C5CFF" : strokeColor;

  return (
    <>
      <Arrow
        points={edge.points}
        stroke={stroke}
        strokeWidth={isSelected ? 2.5 : 1.75}
        fill={stroke}
        pointerLength={9}
        pointerWidth={9}
        hitStrokeWidth={16}
        onClick={onSelect}
        onTap={onSelect}
        onDblClick={onDblClick}
        onDblTap={onDblClick}
        lineCap="round"
        lineJoin="round"
      />
      {edge.label && (
        <Text
          x={midX - 20}
          y={midY - 18}
          width={40}
          align="center"
          text={edge.label}
          fontSize={12}
          fontFamily="Inter, sans-serif"
          fill={theme === "chalkboard" ? "#34D399" : "#2EE6A6"}
          listening={false}
        />
      )}
    </>
  );
}
