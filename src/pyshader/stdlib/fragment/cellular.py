"""Cellular noise: a random point in every grid cell, and the distances to them.

    d = cellular(uv * 5.0, time)          # distance to the nearest point
    f = cellular2(uv * 5.0, time)         # nearest and second nearest
    v = voronoi(uv * 5.0, time)           # distance to the cell's border, and its point

`time` moves the points along circles; 0.0 keeps them still.

Credits:
- `cellular`, `cellular2`: Steven Worley, "A Cellular Texture Basis
  Function" (1996), as taught in The Book of Shaders, ch. 12 "Cellular
  noise", Patricio Gonzalez Vivo & Jen Lowe — https://thebookofshaders.com/12/
- `voronoi`: Inigo Quilez, "Voronoi edges" —
  https://iquilezles.org/articles/voronoilines/ (MIT)
"""
from pyshader import *
from .random import random2

TAU = 6.28318530718


def _point(cell: float2, time: float) -> float2:
    """The feature point of a cell, 0..1 inside it."""
    return 0.5 + 0.5 * sin(time + TAU * random2(cell))


def cellular(st: float2, time: float) -> float:
    """Distance (about 0..1) from st to the nearest cell point."""
    i = floor(st)
    f = fract(st)
    nearest = 8.0
    for y in range(-1, 2):
        for x in range(-1, 2):
            neighbor = float2(float(x), float(y))
            nearest = min(nearest, length(neighbor + _point(i + neighbor, time) - f))
    return nearest


def cellular2(st: float2, time: float) -> float2:
    """(nearest, second nearest) distances to cell points; F2 - F1 outlines the cells."""
    i = floor(st)
    f = fract(st)
    f1 = 8.0
    f2 = 8.0
    for y in range(-1, 2):
        for x in range(-1, 2):
            neighbor = float2(float(x), float(y))
            d = length(neighbor + _point(i + neighbor, time) - f)
            if d < f1:
                f2 = f1
                f1 = d
            elif d < f2:
                f2 = d
    return float2(f1, f2)


def voronoi(st: float2, time: float) -> float3:
    """(distance to the nearest cell border, offset from st to its cell's point)."""
    i = floor(st)
    f = fract(st)
    nearest_cell = float2(0.0)
    nearest_offset = float2(0.0)
    best = 8.0
    for y in range(-1, 2):
        for x in range(-1, 2):
            g = float2(float(x), float(y))
            r = g + _point(i + g, time) - f
            d = dot(r, r)
            if d < best:
                best = d
                nearest_offset = r
                nearest_cell = g
    border = 8.0
    for y in range(-2, 3):
        for x in range(-2, 3):
            g = nearest_cell + float2(float(x), float(y))
            r = g + _point(i + g, time) - f
            between = r - nearest_offset
            if dot(between, between) > 0.00001:
                border = min(border, dot(0.5 * (nearest_offset + r), normalize(between)))
    return float3(border, nearest_offset)
