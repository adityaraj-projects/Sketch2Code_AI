import { describe, expect, it } from "vitest";
import { computeContentBoundingBox } from "@/lib/export/boundingBox";
import { canvasToSvgString } from "@/lib/export/svgExport";
import { buildProjectExportJson } from "@/lib/export/jsonExport";
import type { FlowEdge, FlowNode, FreehandStroke } from "@/types";

function makeNode(overrides: Partial<FlowNode> = {}): FlowNode {
  return {
    id: "n1",
    type: "process",
    x: 100,
    y: 100,
    width: 160,
    height: 72,
    text: "x = 1",
    fill: "#1B1E29",
    stroke: "#7C5CFF",
    ...overrides,
  };
}

function makeEdge(overrides: Partial<FlowEdge> = {}): FlowEdge {
  return {
    id: "e1",
    fromNodeId: "n1",
    toNodeId: "n2",
    points: [180, 172, 180, 250],
    stroke: "#7C5CFF",
    ...overrides,
  };
}

describe("computeContentBoundingBox", () => {
  it("returns null for an empty canvas", () => {
    expect(computeContentBoundingBox([], [])).toBeNull();
  });

  it("computes the box around a single node with padding", () => {
    const box = computeContentBoundingBox([makeNode({ x: 100, y: 100, width: 160, height: 72 })], [], 20);
    expect(box).toEqual({ minX: 80, minY: 80, maxX: 280, maxY: 192 });
  });

  it("expands to include freehand strokes outside the node bounds", () => {
    const stroke: FreehandStroke = {
      id: "s1", tool: "pen", points: [0, 0, 500, 500], pressures: [0.5, 0.5], color: "#fff", width: 3,
    };
    const box = computeContentBoundingBox([makeNode({ x: 100, y: 100, width: 160, height: 72 })], [stroke], 0);
    expect(box!.minX).toBeLessThanOrEqual(0);
    expect(box!.maxX).toBeGreaterThanOrEqual(500);
  });
});

describe("canvasToSvgString", () => {
  it("produces well-formed, self-closing XML with matching root tags", () => {
    const svg = canvasToSvgString([makeNode()], [], []);
    expect(svg.startsWith("<?xml")).toBe(true);
    expect(svg).toContain("<svg");
    expect(svg.trim().endsWith("</svg>")).toBe(true);
    const openRects = (svg.match(/<rect /g) || []).length;
    expect(openRects).toBeGreaterThan(0);
  });

  it("renders a decision node as a 4-point polygon (diamond)", () => {
    const svg = canvasToSvgString([makeNode({ type: "decision", width: 170, height: 100 })], [], []);
    const bodyOnly = svg.split("</defs>")[1];
    const match = bodyOnly.match(/<polygon points="([^"]+)"/);
    expect(match).not.toBeNull();
    const points = match![1].trim().split(" ");
    expect(points).toHaveLength(4);
  });

  it("renders start/end nodes as ellipses", () => {
    const svg = canvasToSvgString([makeNode({ type: "start" })], [], []);
    expect(svg).toContain("<ellipse");
  });

  it("escapes XML-unsafe characters in node text", () => {
    const svg = canvasToSvgString([makeNode({ text: 'if a < b && c > "d"' })], [], []);
    expect(svg).not.toContain('< b');
    expect(svg).toContain("&lt;");
    expect(svg).toContain("&amp;");
  });

  it("renders an edge as a line with an arrowhead marker reference", () => {
    const svg = canvasToSvgString([], [makeEdge()], []);
    expect(svg).toContain("<line");
    expect(svg).toContain("marker-end=\"url(#arrowhead)\"");
  });

  it("includes an edge label as text when present", () => {
    const svg = canvasToSvgString([], [makeEdge({ label: "Yes" })], []);
    expect(svg).toContain(">Yes<");
  });

  it("falls back to a default canvas size when there is nothing to export", () => {
    const svg = canvasToSvgString([], [], []);
    expect(svg).toContain('width="800"');
  });

  it("skips eraser strokes (they represent removed ink, not visible marks)", () => {
    const stroke: FreehandStroke = {
      id: "s1", tool: "eraser", points: [0, 0, 10, 10], pressures: [1, 1], color: "#fff", width: 20,
    };
    const svg = canvasToSvgString([], [], [stroke]);
    expect(svg).not.toContain("<polyline");
  });
});

describe("buildProjectExportJson", () => {
  it("produces valid, parseable JSON with the expected shape", () => {
    const json = buildProjectExportJson("My Flowchart", {
      nodes: [makeNode()],
      edges: [],
      strokes: [],
      viewport: { x: 0, y: 0, zoom: 1 },
    });
    const parsed = JSON.parse(json);
    expect(parsed.format).toBe("sketch2code-project");
    expect(parsed.project_name).toBe("My Flowchart");
    expect(parsed.canvas_data.nodes).toHaveLength(1);
    expect(typeof parsed.exported_at).toBe("string");
  });
});
