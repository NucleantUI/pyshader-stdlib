"""Shapes as masks: 1.0 inside, 0.0 outside, over coordinates in 0..1.

For outlines, unions and smooth edges of any shape, see `sdf`; the masks
from `rounded_rect` on are its distance fields filled, with an edge `blur`
wide (0.0 for a hard one).

Credits: The Book of Shaders, ch. 7 "Shapes", Patricio Gonzalez Vivo &
Jen Lowe — https://thebookofshaders.com/07/ ; the shapes from `sdf`, after
Inigo Quilez.
"""
from pyshader import *
from .sdf import (sd_rounded_box, sd_ellipse, sd_equilateral_triangle, sd_hexagon,
                  sd_star, sd_heart, sd_moon, sd_vesica, sd_egg, sd_pie, fill_smooth)

TAU = 6.28318530718


def rect(st: float2, size: float2) -> float:
    """A rectangle of the given size centered in the 0..1 square."""
    border = (1.0 - size) * 0.5
    bl = step(border, st)
    tr = step(border, 1.0 - st)
    return bl.x * bl.y * tr.x * tr.y


def rect_smooth(st: float2, size: float2, blur: float) -> float:
    """rect with edges blurred over `blur`."""
    border = (1.0 - size) * 0.5
    bl = smoothstep(border - blur, border + blur, st)
    tr = smoothstep(border - blur, border + blur, 1.0 - st)
    return bl.x * bl.y * tr.x * tr.y


def rect_outline(st: float2, size: float2, width: float) -> float:
    """The border of rect, `width` thick, on the inside of its edge."""
    return rect(st, size) - rect(st, size - 2.0 * width)


def circle(st: float2, center: float2, radius: float) -> float:
    return 1.0 - step(radius, distance(st, center))


def circle_smooth(st: float2, center: float2, radius: float, blur: float) -> float:
    return 1.0 - smoothstep(radius - blur, radius + blur, distance(st, center))


def ring(st: float2, center: float2, radius: float, width: float) -> float:
    """A circle's outline, `width` thick, centered on its radius."""
    return 1.0 - step(width * 0.5, abs(distance(st, center) - radius))


def polygon(st: float2, center: float2, sides: int, radius: float) -> float:
    """A regular polygon with `sides` sides; radius reaches the middle of each side."""
    return 1.0 - step(radius, polygon_distance(st - center, sides))


def polygon_smooth(st: float2, center: float2, sides: int, radius: float, blur: float) -> float:
    return 1.0 - smoothstep(radius - blur, radius + blur, polygon_distance(st - center, sides))


def polygon_distance(p: float2, sides: int) -> float:
    """The polygon field of ch. 7: equal on every regular-polygon outline around the origin."""
    a = atan2(p.x, p.y) + PI
    r = TAU / float(sides)
    return cos(floor(0.5 + a / r) * r - a) * length(p)


def flower(st: float2, center: float2, petals: float, radius: float) -> float:
    """A polar shape: petals around center, reaching out to radius."""
    p = st - center
    a = atan2(p.y, p.x)
    f = abs(cos(a * petals * 0.5)) * radius * 0.5 + radius * 0.5
    return 1.0 - smoothstep(f, f + 0.01, length(p))


def gear(st: float2, center: float2, teeth: float, radius: float) -> float:
    """A polar shape: a cog with `teeth` teeth."""
    p = st - center
    a = atan2(p.y, p.x)
    f = smoothstep(-0.5, 1.0, cos(a * teeth)) * radius * 0.2 + radius * 0.8
    return 1.0 - smoothstep(f, f + 0.01, length(p))


def plus(st: float2, size: float) -> float:
    """A plus sign centered in the 0..1 square: two bars of length size, size / 4 thick."""
    return max(rect(st, float2(size, size * 0.25)), rect(st, float2(size * 0.25, size)))


def _edge(d: float, blur: float) -> float:
    return 1.0 - step(0.0, d) if blur <= 0.0 else fill_smooth(d, blur)


def rounded_rect(st: float2, center: float2, size: float2, radius: float, blur: float) -> float:
    """A rectangle of the given size with corners rounded by radius."""
    return _edge(sd_rounded_box(st - center, size * 0.5, float4(radius)), blur)


def ellipse(st: float2, center: float2, radii: float2, blur: float) -> float:
    """An ellipse with half-axes radii.x and radii.y."""
    if radii.x == radii.y:
        return _edge(length(st - center) - radii.x, blur)
    return _edge(sd_ellipse(st - center, radii), blur)


def triangle(st: float2, center: float2, radius: float, blur: float) -> float:
    """An equilateral triangle pointing up; radius is half its side."""
    return _edge(sd_equilateral_triangle(st - center, radius), blur)


def hexagon(st: float2, center: float2, radius: float, blur: float) -> float:
    """A hexagon whose sides are radius from its center."""
    return _edge(sd_hexagon(st - center, radius), blur)


def star(st: float2, center: float2, points: int, radius: float, sharpness: float, blur: float) -> float:
    """A star with `points` points reaching radius; sharpness 0..1 from a polygon to spikes."""
    m = mix(float(points), 2.0, clamp(sharpness, 0.0, 1.0))
    return _edge(sd_star(st - center, radius, points, m), blur)


def heart(st: float2, center: float2, size: float, blur: float) -> float:
    """A heart about `size` tall, centered on center."""
    p = (st - center) / size + float2(0.0, 0.5)
    return _edge(sd_heart(p) * size, blur)


def crescent(st: float2, center: float2, radius: float, cut: float, blur: float) -> float:
    """A crescent moon: a circle of radius with a circle of the same size, cut (0..1
    of the radius) to its right, taken out."""
    return _edge(sd_moon(st - center, max(cut, 0.001) * radius, radius, radius), blur)


def lens(st: float2, center: float2, width: float, height: float, blur: float) -> float:
    """A lens (two arcs) width wide and height tall, pointed at the ends of its longer side."""
    p = st - center
    w = width * 0.5
    h = height * 0.5
    if w > h:
        p = p.yx
        w = height * 0.5
        h = width * 0.5
    # Two circles through (±w, 0) and (0, ±h): radius r, their centers r - w either side.
    r = (w * w + h * h) / (2.0 * w)
    return _edge(sd_vesica(p, r, r - w), blur)


def egg(st: float2, center: float2, radius: float, blur: float) -> float:
    """An egg, radius wide at its base, narrowing upward."""
    return _edge(sd_egg(st - center, radius, radius * 0.3), blur)


def pie(st: float2, center: float2, radius: float, angle: float, blur: float) -> float:
    """A pie slice opening upward, `angle` radians wide."""
    return _edge(sd_pie(st - center, float2(sin(angle * 0.5), cos(angle * 0.5)), radius), blur)
