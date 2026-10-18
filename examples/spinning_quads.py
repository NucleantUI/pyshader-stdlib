"""A grid of quads spinning in 3D (graphics target: vertex + fragment).

Draw 6 vertices per instance, 64 instances.
"""
from pyshader import *
from pyshader.stdlib.vertex.quad import quad_corner, grid_position
from pyshader.stdlib.vertex.transform import perspective, look_at, rotate, translate, UP
from pyshader.stdlib.fragment.sdf import sd_rounded_box, fill_smooth


class Tile:
    position: float4
    local: float2
    seed: float


def vertex(vertex_index: int, instance_index: int, time: float, resolution: float2) -> Tile:
    corner = quad_corner(vertex_index)
    center = grid_position(instance_index, 8, float2(1.2)) - float2(4.2)
    seed = float(instance_index) / 64.0
    model = translate(float3(center, 0.0)) * rotate(float3(1.0, 1.0, 0.0), time + seed * 6.28)
    view = look_at(float3(0.0, -6.0, 9.0), float3(0.0), UP)
    projection = perspective(radians(50.0), resolution.x / resolution.y, 0.1, 50.0)
    return Tile(projection * view * model * float4(corner * 0.45, 0.0, 1.0), local=corner, seed=seed)


def fragment(local: float2, seed: float) -> float4:
    shape = fill_smooth(sd_rounded_box(local, float2(0.8), float4(0.2)), 0.03)
    return float4(float3(0.3 + seed * 0.7, 0.5, 1.0 - seed) * shape, shape)
