import type { FlowEdge, FlowNode, FreehandStroke } from "@/types";
import { computeContentBoundingBox } from "@/lib/export/boundingBox";

function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function wrapText(text: string, maxWidth: number, avgCharWidth = 6.2): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = "";

  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length * avgCharWidth > maxWidth && current) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines.length > 0 ? lines : [""];
}

function renderLabel(node: FlowNode): string {
  if (!node.text) return "";
  const lines = wrapText(node.text, node.width - 16);
  const lineHeight = 15;
  const startY = node.y + node.height / 2 - ((lines.length - 1) * lineHeight) / 2;
  const cx = node.x + node.width / 2;

  const tspans = lines
    .map((line, i) => `<tspan x="${cx}" y="${startY + i * lineHeight}">${escapeXml(line)}</tspan>`)
    .join("");

  return `<text text-anchor="middle" dominant-baseline="middle" font-family="Inter, sans-serif" font-size="13" fill="#1B1E29">${tspans}</text>`;
}

function renderNode(node: FlowNode): string {
  const { x, y, width: w, height: h, fill, stroke } = node;
  const commonAttrs = `fill="${fill === "#1B1E29" ? "#FFFFFF" : fill}" stroke="${stroke}" stroke-width="1.75"`;

  let shape = "";
  if (node.type === "start" || node.type === "end") {
    shape = `<ellipse cx="${x + w / 2}" cy="${y + h / 2}" rx="${w / 2}" ry="${h / 2}" ${commonAttrs} />`;
  } else if (node.type === "decision") {
    const points = [
      [x + w / 2, y], [x + w, y + h / 2], [x + w / 2, y + h], [x, y + h / 2],
    ].map((p) => p.join(",")).join(" ");
    shape = `<polygon points="${points}" ${commonAttrs} />`;
  } else if (node.type === "input" || node.type === "output") {
    const points = [
      [x + w * 0.15, y], [x + w, y], [x + w * 0.85, y + h], [x, y + h],
    ].map((p) => p.join(",")).join(" ");
    shape = `<polygon points="${points}" ${commonAttrs} />`;
  } else if (node.type === "connector") {
    const r = Math.min(w, h) / 2;
    shape = `<ellipse cx="${x + w / 2}" cy="${y + h / 2}" rx="${r}" ry="${r}" ${commonAttrs} />`;
  } else if (node.type === "text") {
    shape = "";
  } else {
    shape = `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="6" ${commonAttrs} />`;
  }

  return shape + renderLabel(node);
}

function renderEdge(edge: FlowEdge): string {
  const [x1, y1, x2, y2] = edge.points;
  let line = `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${edge.stroke}" stroke-width="1.75" marker-end="url(#arrowhead)" />`;

  if (edge.label) {
    const midX = (x1 + x2) / 2;
    const midY = (y1 + y2) / 2;
    line += `<text x="${midX}" y="${midY - 6}" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" fill="${edge.stroke}">${escapeXml(edge.label)}</text>`;
  }
  return line;
}

function renderStroke(stroke: FreehandStroke): string {
  if (stroke.tool === "eraser") return "";
  const points: string[] = [];
  for (let i = 0; i < stroke.points.length; i += 2) {
    points.push(`${stroke.points[i]},${stroke.points[i + 1]}`);
  }
  const opacity = stroke.tool === "highlighter" ? 0.35 : 1;
  return `<polyline points="${points.join(" ")}" fill="none" stroke="${stroke.color}" stroke-width="${stroke.width}" stroke-linecap="round" stroke-linejoin="round" opacity="${opacity}" />`;
}

/**
 * Serializes the flowchart to real, standalone SVG markup — each shape is
 * hand-constructed to match how it's rendered on the Konva canvas
 * (NodeShape.tsx/EdgeShape.tsx), not a screenshot or a wrapped raster
 * image. Freehand strokes are rendered at constant width rather than
 * reproducing per-point pressure variation in vector form — a documented
 * simplification, since building a pressure-varying filled outline path
 * is significantly more complex for comparatively little visual benefit
 * in an exported diagram.
 */
export function canvasToSvgString(nodes: FlowNode[], edges: FlowEdge[], strokes: FreehandStroke[]): string {
  const box = computeContentBoundingBox(nodes, strokes);
  const viewBox = box ?? { minX: 0, minY: 0, maxX: 800, maxY: 600 };
  const width = viewBox.maxX - viewBox.minX;
  const height = viewBox.maxY - viewBox.minY;

  const body = [
    `<rect x="${viewBox.minX}" y="${viewBox.minY}" width="${width}" height="${height}" fill="#FFFFFF" />`,
    ...strokes.map(renderStroke),
    ...edges.map(renderEdge),
    ...nodes.map(renderNode),
  ].join("\n");

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox.minX} ${viewBox.minY} ${width} ${height}" width="${width}" height="${height}">
  <defs>
    <marker id="arrowhead" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
      <polygon points="0,0 9,4.5 0,9" fill="#7C5CFF" />
    </marker>
  </defs>
${body}
</svg>`;
}
