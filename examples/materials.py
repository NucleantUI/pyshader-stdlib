"""Sixteen materials under one light: plastic, rubber, ceramic and glass;
gold, brushed aluminum, copper and rust; rock, granite, marble and concrete;
sand, wood, leather and fabric. Each is a beveled tile lit by the same
orbiting light through the same shading model, so what tells them apart is
the material alone. The glass tile bends the checkerboard behind it."""
from pyshader import *
from pyshader.stdlib.fragment import sdf, light, material
from pyshader.stdlib.fragment.color import linear_to_srgb
from pyshader.stdlib.fragment.surface import shade, shade_ambient

VIEW = float3(0.0, 0.0, 1.0)
SUN = float3(3.2, 3.0, 2.8)
SKY = float3(0.10, 0.12, 0.16)
TILE = float2(0.78)
CORNERS = float4(0.22)


def tile_distance(p: float2) -> float:
    return sdf.sd_rounded_box(p, TILE, CORNERS)


def backdrop(q: float2) -> float3:
    """What the glass tile stands over: a checkerboard."""
    c = mod(floor(q.x * 10.0) + floor(q.y * 10.0), 2.0)
    return mix(float3(0.04, 0.06, 0.1), float3(0.85, 0.78, 0.6), c)


def surroundings(r: float3) -> float3:
    """What the tiles reflect: a dim floor below, a bright warm horizon, a blue sky above."""
    up = r.y + 0.3 * r.z
    sky = mix(float3(1.0, 0.85, 0.65), float3(0.35, 0.5, 0.8), smoothstep(0.1, 0.9, up))
    return mix(float3(0.08, 0.07, 0.06), sky, smoothstep(-0.25, 0.05, up))


def tile(k: int, m: float2, n: float3, l: float3, q: float2) -> float3:
    """Tile k, at material coordinates m, facing n, lit from l."""
    if k == 3:
        # Glass: the backdrop seen where the pane bends the view to.
        behind = backdrop(q + material.refraction_offset(n, material.GLASS_IOR, 0.12))
        return material.glass(behind, n, l, SUN, surroundings(reflect(-VIEW, n)), float3(0.8, 0.95, 0.9), material.GLASS_IOR, 1.0)
    s = material.plastic(n, float3(0.75, 0.08, 0.06), 0.3)
    if k == 1:
        s = material.rubber(m, n, float3(0.12, 0.12, 0.13))
    if k == 2:
        s = material.ceramic(n, float3(0.12, 0.3, 0.7))
    if k == 4:
        s = material.metal(n, material.GOLD, 0.2)
    if k == 5:
        s = material.brushed_metal(m, n, material.ALUMINUM, 0.4)
    if k == 6:
        s = material.metal(n, material.COPPER, 0.35)
    if k == 7:
        s = material.rust(m, n, material.IRON, 0.55)
    if k == 8:
        s = material.rock(m, n)
    if k == 9:
        s = material.granite(m, n)
    if k == 10:
        s = material.marble(m, n, float3(0.88, 0.86, 0.82), float3(0.22, 0.24, 0.28))
    if k == 11:
        s = material.concrete(m, n)
    if k == 12:
        s = material.sand(m * 2.0, n, float3(0.76, 0.6, 0.4))
    if k == 13:
        s = material.wood(m, n, float3(0.62, 0.4, 0.2), float3(0.3, 0.16, 0.07))
    if k == 14:
        s = material.leather(m * 3.0, n, float3(0.32, 0.15, 0.08))
    if k == 15:
        s = material.fabric(m * 6.0, n, float3(0.15, 0.25, 0.55))
    return shade(s, l, VIEW, SUN) + shade_ambient(s, VIEW, SKY, surroundings(reflect(-VIEW, s.normal)))


def main(uv: float2, time: float) -> float4:
    cells = uv * 4.0
    cell = floor(cells)
    # Row 0 at the top, left to right.
    k = int(cell.x + (3.0 - cell.y) * 4.0)
    p = fract(cells) * 2.0 - 1.0
    d = tile_distance(p)
    e = 0.002
    slope = float2(tile_distance(p + float2(e, 0.0)) - tile_distance(p - float2(e, 0.0)),
                   tile_distance(p + float2(0.0, e)) - tile_distance(p - float2(0.0, e)))
    n = light.bevel_normal(d, normalize(slope + float2(0.0001)), 0.2)

    a = time * 0.5
    l = normalize(float3(cos(a) * 0.9, sin(a) * 0.9, 0.75))

    # The table under the tiles, in their shadow away from the light.
    table = backdrop(uv * 1.2) * 0.15 + float3(0.02)
    shadow = light.drop_shadow(tile_distance(p + l.xy * 0.08), 0.06)
    under = table * (1.0 - 0.7 * shadow)

    m = p * 1.5 + cell * 3.7
    c = mix(under, tile(k, m, n, l, uv * 1.2), 1.0 - smoothstep(-0.01, 0.01, d))
    return float4(linear_to_srgb(light.tonemap_aces(c)), 1.0)
