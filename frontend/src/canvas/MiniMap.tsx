import type { FlowNode, Viewport } from "@/types";

interface Props {
  nodes: FlowNode[];
  viewport: Viewport;
}

const MAP_W = 180;
const MAP_H = 120;
const WORLD_SPAN = 3000; // world units represented by the minimap

export function MiniMap({ nodes, viewport }: Props) {
  const scale = MAP_W / WORLD_SPAN;
  const originOffset = WORLD_SPAN / 2;

  const viewX = (-viewport.x / viewport.zoom + originOffset) * scale;
  const viewY = (-viewport.y / viewport.zoom + originOffset) * scale;
  const viewW = (window.innerWidth / viewport.zoom) * scale;
  const viewH = (window.innerHeight / viewport.zoom) * scale;

  return (
    <div
      className="glass-panel absolute bottom-6 right-6 z-20 overflow-hidden rounded-xl"
      style={{ width: MAP_W, height: MAP_H }}
    >
      <svg width={MAP_W} height={MAP_H} className="absolute inset-0">
        {nodes.map((n) => (
          <rect
            key={n.id}
            x={(n.x + originOffset) * scale}
            y={(n.y + originOffset) * scale}
            width={Math.max(2, n.width * scale)}
            height={Math.max(2, n.height * scale)}
            fill="#7C5CFF"
            opacity={0.6}
            rx={1}
          />
        ))}
        <rect
          x={viewX}
          y={viewY}
          width={viewW}
          height={viewH}
          fill="none"
          stroke="#2EE6A6"
          strokeWidth={1.5}
        />
      </svg>
      <span className="absolute left-2 top-1.5 text-[10px] font-mono uppercase tracking-wider text-paper-500">
        Map
      </span>
    </div>
  );
}
