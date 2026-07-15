import { useState, useEffect } from "react";
import { Group, Rect, Ellipse, Text as KonvaText, Line, Image as KonvaImage } from "react-konva";
import type Konva from "konva";
import type { FlowNode } from "@/types";

function useImageLoader(url?: string) {
  const [image, setImage] = useState<HTMLImageElement | null>(null);

  useEffect(() => {
    if (!url) {
      setImage(null);
      return;
    }
    const img = new window.Image();
    img.src = url;
    img.onload = () => {
      setImage(img);
    };
  }, [url]);

  return image;
}

interface Props {
  node: FlowNode;
  isSelected: boolean;
  isExecuting?: boolean;
  theme?: "dark" | "light" | "chalkboard";
  viewOnly?: boolean;
  onSelect: () => void;
  onDragEnd: (x: number, y: number) => void;
  onDblClick: () => void;
}

export function NodeShape({ node, isSelected, isExecuting, theme = "dark", viewOnly = false, onSelect, onDragEnd, onDblClick }: Props) {
  const textFill =
    theme === "light"
      ? "#1E293B"
      : theme === "chalkboard"
      ? "#F0FDF4"
      : "#EDEBE6";

  const defaultFill =
    theme === "light"
      ? "#FFFFFF"
      : theme === "chalkboard"
      ? "#022C22"
      : "#1B1E29";

  const defaultStroke =
    theme === "light"
      ? "#7C5CFF"
      : theme === "chalkboard"
      ? "#34D399"
      : "#7C5CFF";

  const themeFillMap: Record<string, Record<string, string>> = {
    dark: {
      default: "#1B1E29",
      blue: "#1E3A8A",
      green: "#064E3B",
      yellow: "#78350F",
      red: "#7F1D1D",
      purple: "#581C87",
    },
    light: {
      default: "#FFFFFF",
      blue: "#DBEAFE",
      green: "#DCFCE7",
      yellow: "#FEF9C3",
      red: "#FEE2E2",
      purple: "#F3E8FF",
    },
    chalkboard: {
      default: "#022C22",
      blue: "#103F54",
      green: "#0F5132",
      yellow: "#664D03",
      red: "#5C1D24",
      purple: "#351A55",
    }
  };

  const themeStrokeMap: Record<string, Record<string, string>> = {
    dark: {
      default: "#7C5CFF",
      blue: "#60A5FA",
      green: "#34D399",
      yellow: "#FBBF24",
      red: "#F87171",
      purple: "#C084FC",
    },
    light: {
      default: "#7C5CFF",
      blue: "#2563EB",
      green: "#16A34A",
      yellow: "#D97706",
      red: "#DC2626",
      purple: "#9333EA",
    },
    chalkboard: {
      default: "#34D399",
      blue: "#38BDF8",
      green: "#4ADE80",
      yellow: "#FBBF24",
      red: "#F87171",
      purple: "#C084FC",
    }
  };

  const normalizedKey = (node.fill || "default").toLowerCase();
  const nodeFill = themeFillMap[theme]?.[normalizedKey] || themeFillMap[theme]?.["default"] || node.fill || defaultFill;

  const normalizedStrokeKey = (node.stroke || "default").toLowerCase();
  const strokeColor = themeStrokeMap[theme]?.[normalizedStrokeKey] || themeStrokeMap[theme]?.["default"] || node.stroke || defaultStroke;

  const stroke = isExecuting ? "#2EE6A6" : isSelected ? "#7C5CFF" : strokeColor;
  const strokeWidth = isExecuting || isSelected ? 2.5 : 1.5;

  function handleDragEnd(e: Konva.KonvaEventObject<DragEvent>) {
    onDragEnd(e.target.x(), e.target.y());
  }

  const imgElement = useImageLoader(node.type === "image" ? node.imageUrl : undefined);

  const shapeCommon = {
    x: node.x,
    y: node.y,
    fill: nodeFill,
    stroke: viewOnly && !isExecuting ? strokeColor : stroke,
    strokeWidth,
    draggable: !viewOnly,
    onClick: viewOnly ? undefined : onSelect,
    onTap: viewOnly ? undefined : onSelect,
    onDblClick: viewOnly ? undefined : onDblClick,
    onDragEnd: handleDragEnd,
    shadowColor: !viewOnly ? (isExecuting ? "#2EE6A6" : isSelected ? "#7C5CFF" : "transparent") : undefined,
    shadowBlur: !viewOnly ? (isExecuting ? 22 : isSelected ? 16 : 0) : 0,
    shadowOpacity: 0.6,
  };

  return (
    <Group id={node.id}>
      {node.type === "start" || node.type === "end" ? (
        <Ellipse
          {...shapeCommon}
          x={node.x + node.width / 2}
          y={node.y + node.height / 2}
          radiusX={node.width / 2}
          radiusY={node.height / 2}
        />
      ) : node.type === "decision" ? (
        <Line
          {...shapeCommon}
          points={[
            node.width / 2, 0,
            node.width, node.height / 2,
            node.width / 2, node.height,
            0, node.height / 2,
          ]}
          closed
        />
      ) : node.type === "input" || node.type === "output" ? (
        <Line
          {...shapeCommon}
          points={[
            node.width * 0.15, 0,
            node.width, 0,
            node.width * 0.85, node.height,
            0, node.height,
          ]}
          closed
        />
      ) : node.type === "connector" ? (
        <Ellipse
          {...shapeCommon}
          x={node.x + node.width / 2}
          y={node.y + node.height / 2}
          radiusX={Math.min(node.width, node.height) / 2}
          radiusY={Math.min(node.width, node.height) / 2}
        />
      ) : node.type === "text" ? (
        <Rect {...shapeCommon} width={node.width} height={node.height} fill="transparent" stroke="transparent" />
      ) : node.type === "image" ? (
        imgElement ? (
          <KonvaImage
            {...shapeCommon}
            image={imgElement}
            width={node.width}
            height={node.height}
          />
        ) : (
          <Rect
            {...shapeCommon}
            width={node.width}
            height={node.height}
            fill="#334155"
            cornerRadius={6}
          />
        )
      ) : (
        <Rect {...shapeCommon} width={node.width} height={node.height} cornerRadius={6} />
      )}

      <KonvaText
        x={node.x}
        y={node.y}
        width={node.width}
        height={node.height}
        text={node.text}
        align="center"
        verticalAlign="middle"
        fontFamily="Inter, sans-serif"
        fontSize={14}
        fill={textFill}
        listening={false}
        padding={8}
        wrap="word"
      />
    </Group>
  );
}
