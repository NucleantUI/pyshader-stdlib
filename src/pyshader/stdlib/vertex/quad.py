"""Quads from vertex_index alone, with no vertex buffer: draw 6 vertices per
quad (two triangles) and take each corner from its index.

    corner = quad_corner(vertex_index)                     # -1..1
    center = grid_position(instance_index, 8, float2(0.25))
    position = float4(center + corner * 0.1, 0.0, 1.0)

Credits: the common two-triangle quad; nothing borrowed.
"""
from pyshader import *

# Two counter-clockwise triangles covering -1..1.
QUAD = [
    float2(-1.0, -1.0), float2(1.0, -1.0), float2(-1.0, 1.0),
    float2(-1.0, 1.0), float2(1.0, -1.0), float2(1.0, 1.0),
]


def quad_corner(vertex_index: int) -> float2:
    """The corner (-1..1) of the quad vertex_index belongs to; vertex_index % 6 picks it."""
    return QUAD[vertex_index % 6]


def quad_uv(vertex_index: int) -> float2:
    """The same corner in 0..1, (0, 0) at bottom left."""
    return quad_corner(vertex_index) * 0.5 + 0.5


def quad_index(vertex_index: int) -> int:
    """Which quad vertex_index belongs to, when several are drawn in one instance."""
    return vertex_index // 6


def grid_cell(index: int, columns: int) -> int2:
    """(column, row) of the index-th item of a grid filled row by row."""
    return int2(index % columns, index // columns)


def grid_position(index: int, columns: int, spacing: float2) -> float2:
    """The center of the index-th cell of a grid starting at the origin."""
    return float2(grid_cell(index, columns)) * spacing
