"""Patterns: repeat the 0..1 square across the plane, and vary each copy.

    st = tile(uv, 5.0)                 # 5 x 5 copies, each 0..1
    shape = circle(st, float2(0.5), 0.3)

Credits: The Book of Shaders, ch. 9 "Patterns" (tiles, bricks, rotated
tiles) and ch. 10 "Random" (truchet), Patricio Gonzalez Vivo & Jen Lowe —
https://thebookofshaders.com/09/ ; Truchet tiles after Sébastien Truchet (1704).
"""
from pyshader import *
from .matrix import rotate_around
from .random import random


def tile(st: float2, zoom: float) -> float2:
    """zoom x zoom copies of the 0..1 square."""
    return fract(st * zoom)


def tile_index(st: float2, zoom: float) -> float2:
    """Which copy st is in: (column, row), whole numbers from 0."""
    return floor(st * zoom)


def brick_tile(st: float2, zoom: float, offset: float) -> float2:
    """Tiles with every other row shifted by offset (0.5 for bricks)."""
    q = st * zoom
    q.x += step(1.0, mod(q.y, 2.0)) * offset
    return fract(q)


def mirror_tile(st: float2, zoom: float) -> float2:
    """Tiles with every other column and row mirrored, so edges meet seamlessly."""
    q = st * zoom
    cell = mod(floor(q), 2.0)
    f = fract(q)
    return mix(f, 1.0 - f, cell)


def checker(st: float2, zoom: float) -> float:
    """1.0 and 0.0 alternating like a chessboard."""
    cell = floor(st * zoom)
    return mod(cell.x + cell.y, 2.0)


def rotate_tile_pattern(st: float2) -> float2:
    """2 x 2 tiles, each turned a quarter more than the last: one motif makes a pattern."""
    q = st * 2.0
    index = step(1.0, mod(q.x, 2.0)) + step(1.0, mod(q.y, 2.0)) * 2.0
    f = fract(q)
    if index == 1.0:
        return rotate_around(f, PI * 0.5, float2(0.5))
    if index == 2.0:
        return rotate_around(f, -PI * 0.5, float2(0.5))
    if index == 3.0:
        return rotate_around(f, PI, float2(0.5))
    return f


def truchet(st: float2, zoom: float, seed: float) -> float2:
    """Tiles each turned a random quarter: draw one diagonal motif in the
    result and it joins into a maze. seed picks another arrangement."""
    q = st * zoom
    r = random(floor(q) + seed)
    f = fract(q)
    if r > 0.75:
        return 1.0 - f
    if r > 0.5:
        return float2(1.0 - f.x, f.y)
    if r > 0.25:
        return float2(f.x, 1.0 - f.y)
    return f


def stripes(x: float, count: float, width: float) -> float:
    """count stripes across 0..1, each `width` (0..1) of its period wide."""
    return step(fract(x * count), width)
