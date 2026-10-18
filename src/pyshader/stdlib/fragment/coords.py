"""Coordinate helpers: centering, aspect ratio and polar coordinates.

Credits: The Book of Shaders, ch. 7 "Shapes" (polar shapes), Patricio
Gonzalez Vivo & Jen Lowe — https://thebookofshaders.com/07/
"""
from pyshader import *


def aspect(uv: float2, resolution: float2) -> float2:
    """uv with x stretched by the aspect ratio, so a circle stays round on a wide view."""
    return float2(uv.x * resolution.x / resolution.y, uv.y)


def centered(uv: float2, resolution: float2) -> float2:
    """uv moved to run -1..1 across the shorter side, (0, 0) in the middle, aspect kept."""
    p = uv * 2.0 - 1.0
    return p * resolution / min(resolution.x, resolution.y)


def to_polar(p: float2) -> float2:
    """(radius, angle) of p around the origin; the angle in -π..π."""
    return float2(length(p), atan2(p.y, p.x))


def from_polar(polar: float2) -> float2:
    """(radius, angle) back to x, y."""
    return polar.x * float2(cos(polar.y), sin(polar.y))


def remap(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """x from in_min..in_max to out_min..out_max (not clamped)."""
    return out_min + (x - in_min) * (out_max - out_min) / (in_max - in_min)
