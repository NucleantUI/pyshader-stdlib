"""Between pixels and clip space, and camera-facing quads.

Clip space here is y-up, -1..1 on both axes; pixels count from the top
left corner.

Credits: the standard viewport mapping; `billboard` reads the camera's
right and up axes from the view matrix's rows, the usual way to face a
quad to the camera.
"""
from pyshader import *


def pixel_to_clip(pixel: float2, resolution: float2) -> float2:
    """A pixel position (top-left origin, y down) to clip space."""
    p = pixel / resolution
    return float2(p.x * 2.0 - 1.0, 1.0 - p.y * 2.0)


def clip_to_pixel(clip: float2, resolution: float2) -> float2:
    """Clip space back to a pixel position (top-left origin, y down)."""
    return float2((clip.x + 1.0) * 0.5, (1.0 - clip.y) * 0.5) * resolution


def pixel_size_to_clip(size: float2, resolution: float2) -> float2:
    """A size in pixels as a size in clip space (no flip: sizes are positive)."""
    return size / resolution * 2.0


def keep_aspect(p: float2, resolution: float2) -> float2:
    """Squeezes x so a shape built in square units keeps its proportions on a wide or tall view."""
    return float2(p.x * resolution.y / resolution.x, p.y)


def billboard(center: float3, corner: float2, size: float2, view: float4x4) -> float3:
    """The world position of a quad corner (-1..1) around center, facing the camera of `view`."""
    right = float3(view[0][0], view[1][0], view[2][0])
    up = float3(view[0][1], view[1][1], view[2][1])
    return center + right * corner.x * size.x + up * corner.y * size.y
