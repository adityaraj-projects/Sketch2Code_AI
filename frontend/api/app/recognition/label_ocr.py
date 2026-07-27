from __future__ import annotations

import base64
import io
from dataclasses import dataclass

from PIL import Image

from app.recognition.geometry import BBox


@dataclass
class SnapshotContext:
    image: Image.Image
    viewport_x: float
    viewport_y: float
    viewport_zoom: float
    pixel_ratio: float

    def world_bbox_to_pixels(self, box: BBox, padding: float = 6.0) -> tuple[int, int, int, int]:
        def to_px(x: float, y: float) -> tuple[float, float]:
            screen_x = x * self.viewport_zoom + self.viewport_x
            screen_y = y * self.viewport_zoom + self.viewport_y
            return screen_x * self.pixel_ratio, screen_y * self.pixel_ratio

        px1, py1 = to_px(box.min_x, box.min_y)
        px2, py2 = to_px(box.max_x, box.max_y)
        pad = padding * self.pixel_ratio
        left = max(0, int(px1 - pad))
        top = max(0, int(py1 - pad))
        right = min(self.image.width, int(px2 + pad))
        bottom = min(self.image.height, int(py2 + pad))
        return left, top, right, bottom


def decode_snapshot(image_base64: str, viewport_x: float, viewport_y: float, viewport_zoom: float, pixel_ratio: float) -> SnapshotContext:
    raw = base64.b64decode(image_base64.split(",")[-1])
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    return SnapshotContext(
        image=image,
        viewport_x=viewport_x,
        viewport_y=viewport_y,
        viewport_zoom=viewport_zoom,
        pixel_ratio=pixel_ratio,
    )


def crop_node_png_bytes(ctx: SnapshotContext, box: BBox) -> bytes | None:
    left, top, right, bottom = ctx.world_bbox_to_pixels(box)
    if right - left < 6 or bottom - top < 6:
        return None
    crop = ctx.image.crop((left, top, right, bottom))
    buf = io.BytesIO()
    crop.save(buf, format="PNG")
    return buf.getvalue()
