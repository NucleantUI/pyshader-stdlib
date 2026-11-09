"""`sdf`'s distance functions, run on the CPU (tests/cpu.py) and checked by
their numbers: a distance field's gradient is 1 long, the point it leads to is
on the shape's edge, and the edge is where the docstring puts it."""

import math
import random

import pytest

import cpu

sdf = cpu.load("pyshader.stdlib.fragment.sdf")
F, F3 = cpu.float2, cpu.float3


def points(count: int = 800, box: float = 1.5, seed: int = 0) -> list[tuple[float, float]]:
    rng = random.Random(seed)
    return [(rng.uniform(-box, box), rng.uniform(-box, box)) for _ in range(count)]


def assert_exact(f, box: float = 1.5) -> None:
    """f is an exact distance field: no NaN, a gradient 1 long (except on the
    few points where two nearest edges meet), and stepping d back along it
    lands on the edge."""
    h = 1e-5
    kinks = 0
    for x, y in points(box=box):
        d = f(F(x, y))
        assert not math.isnan(d), (x, y)
        gx = (f(F(x + h, y)) - f(F(x - h, y))) / (2 * h)
        gy = (f(F(x, y + h)) - f(F(x, y - h))) / (2 * h)
        g = math.hypot(gx, gy)
        if abs(g - 1.0) > 1e-3:
            kinks += 1
            continue
        edge = f(F(x - d * gx / g, y - d * gy / g))
        assert abs(edge) < 1e-4, f"{(x, y)}: d = {d}, but {edge} from the edge where it leads"
    assert kinks < 8, f"gradient not 1 long at {kinks} points"


def assert_at(f, cases) -> None:
    for (x, y), expected in cases:
        if expected in ("in", "out"):
            d = f(F(x, y))
            assert (d < 0.0) == (expected == "in"), f"{(x, y)}: {d}, expected {expected}side"
        else:
            assert f(F(x, y)) == pytest.approx(expected, abs=1e-6), (x, y)


HALF = (math.cos(0.6), math.sin(0.6))

SHAPES = {
    "ring": (lambda p: sdf.sd_ring(p, F(*HALF), 0.8, 0.2), [
        ((0.0, 0.8), -0.1), ((0.0, 0.9), 0.0), ((0.8 * math.sin(0.5), 0.8 * math.cos(0.5)), "in"),
        ((0.8 * math.sin(0.7), 0.8 * math.cos(0.7)), "out"), ((0.0, -0.8), "out")]),
    "lens": (lambda p: sdf.sd_lens(p, 0.8, 0.4), [
        ((0.8, 0.0), 0.0), ((-0.8, 0.0), 0.0), ((0.0, 0.4), 0.0), ((0.0, 0.0), -0.4)]),
    "oriented_vesica": (lambda p: sdf.sd_oriented_vesica(p, F(-0.6, -0.3), F(0.7, 0.5), 0.3), [
        ((-0.6, -0.3), 0.0), ((0.7, 0.5), 0.0), ((0.05, 0.1), -0.3)]),
    "bulging_egg": (lambda p: sdf.sd_bulging_egg(p, 0.6, 0.4, 0.2, 0.6), [
        ((0.0, -0.4), 0.0), ((0.0, 0.8), 0.0), ((0.0, 0.3), "in"), ((0.5, 0.3), "out")]),
    "parabola_segment": (lambda p: sdf.sd_parabola_segment(p, 0.6, 0.8), [
        ((0.6, 0.0), 0.0), ((-0.6, 0.0), 0.0), ((0.0, 0.8), 0.0), ((0.0, 0.4), "in"), ((0.0, 1.0), "out")]),
    "blobby_cross": (lambda p: sdf.sd_blobby_cross(p, 0.2), [
        ((1.0, 0.0), 0.0), ((0.0, -1.0), 0.0), ((0.0, 0.0), "in"),
        ((0.5 - 0.1 * math.sqrt(2.0), 0.5 - 0.1 * math.sqrt(2.0)), 0.0)]),
    "blobby_cross_out": (lambda p: sdf.sd_blobby_cross(p, -0.3), [
        ((1.0, 0.0), 0.0), ((0.5, 0.5), "in"), ((1.0, 1.0), "out")]),
    "stairs": (lambda p: sdf.sd_stairs(p + F(0.75, 0.5), F(0.3, 0.2), 5.0), [
        ((-0.75, -0.3), 0.0), ((-0.45, -0.1), 0.0), ((0.75, 0.5), 0.0), ((-0.65, -0.45), -0.05),
        ((-0.65, -0.2), 0.1), ((-0.95, -0.4), 0.2), ((0.0, -0.6), 0.1)]),
    "quadratic_circle": (lambda p: sdf.sd_quadratic_circle(p), [
        ((1.0, 0.0), 0.0), ((0.0, -1.0), 0.0), ((0.75, 0.75), 0.0), ((0.0, 0.0), "in")]),
    "hyperbola": (lambda p: sdf.sd_hyperbola(p, 0.1, 0.5), [
        ((math.sqrt(0.2), 0.0), 0.0), ((-math.sqrt(0.2 + 0.25), 0.5), 0.0), ((1.0, 0.0), "in"),
        ((0.0, 0.0), "out"), ((0.0, 1.0), "out")]),
    "cool_s": (lambda p: sdf.sd_cool_s(p), [
        ((0.0, 1.0), 0.0), ((0.0, -1.0), 0.0), ((0.4, 0.5), 0.0), ((-0.3, 0.5), "in"), ((0.0, 0.0), "in"),
        ((0.6, 0.0), "out")]),
    "circle_wave": (lambda p: sdf.sd_circle_wave(p, 0.6, 0.3), [((0.6, 0.3), 0.0), ((0.6, 0.0), 0.3), ((1.8, 0.3), 0.0)]),
}


@pytest.mark.parametrize("name", list(SHAPES))
def test_exact(name):
    assert_exact(SHAPES[name][0])


@pytest.mark.parametrize("name", list(SHAPES))
def test_where_the_edge_is(name):
    assert_at(*SHAPES[name])


def test_circle_wave_is_a_line():
    assert all(sdf.sd_circle_wave(F(x, y), 0.6, 0.3) >= 0.0 for x, y in points())


def test_lens_is_the_vesica_by_its_size():
    # Two circles of radius 0.5, 0.3 apart from the middle: points 0.4 up and
    # down, 0.2 wide to each side.
    for x, y in points(200):
        assert sdf.sd_lens(F(y, x), 0.4, 0.2) == pytest.approx(sdf.sd_vesica(F(x, y), 0.5, 0.3), abs=1e-9)


def test_oriented_vesica_on_the_x_axis_is_the_lens():
    for x, y in points(200):
        expected = sdf.sd_lens(F(x, y), 0.8, 0.4)
        assert sdf.sd_oriented_vesica(F(x, y), F(-0.8, 0.0), F(0.8, 0.0), 0.4) == pytest.approx(expected, abs=1e-9)


# sd_arc_polygon, against the same outline drawn as a polygon of many short
# straight edges, measured by a plain implementation of its own.


def outline(corners: list[tuple[float, float, float]], steps: int = 400) -> list[tuple[float, float]]:
    """The outline as points: each arc walked around its circle."""
    out = []
    for i, (ax, ay, k) in enumerate(corners):
        bx, by, _ = corners[(i + 1) % len(corners)]
        if k == 0.0:
            out.append((ax, ay))
            continue
        # The arc turns by 4·atan(k) from a to b, counterclockwise when k > 0.
        theta = 4.0 * math.atan(k)
        ex, ey = bx - ax, by - ay
        chord = math.hypot(ex, ey)
        radius = chord / (2.0 * math.sin(abs(theta) / 2.0))
        mx, my = (ax + bx) / 2, (ay + by) / 2
        to_center = radius * math.cos(theta / 2.0) * math.copysign(1.0, k)
        cx, cy = mx - ey / chord * to_center, my + ex / chord * to_center
        start = math.atan2(ay - cy, ax - cx)
        out += [(cx + radius * math.cos(start + theta * t / steps), cy + radius * math.sin(start + theta * t / steps))
                for t in range(steps)]
    return out


def polygon_distance(poly: list[tuple[float, float]], x: float, y: float) -> float:
    d2 = math.inf
    inside = False
    for i, (ax, ay) in enumerate(poly):
        bx, by = poly[i - 1]
        ex, ey = bx - ax, by - ay
        wx, wy = x - ax, y - ay
        t = min(max((wx * ex + wy * ey) / (ex * ex + ey * ey), 0.0), 1.0)
        d2 = min(d2, (wx - ex * t) ** 2 + (wy - ey * t) ** 2)
        if (ay > y) != (by > y) and x < ax + (y - ay) * ex / ey:
            inside = not inside
    return -math.sqrt(d2) if inside else math.sqrt(d2)


ARC_POLYGONS = {
    "half circle out": [(-0.5, -0.5, 0.0), (0.5, -0.5, 1.0), (0.5, 0.5, 0.0), (-0.5, 0.5, 0.0)],
    "every bulge": [(-0.5, -0.5, 0.5), (0.5, -0.5, 0.0), (0.5, 0.5, -0.4), (-0.5, 0.5, 0.25)],
    "more than a half circle": [(-0.4, -0.4, 0.0), (0.4, -0.4, 0.0), (0.4, 0.4, 0.0), (-0.4, 0.4, 2.0)],
    "clockwise": [(-0.5, 0.5, 0.0), (0.5, 0.5, -0.3), (0.5, -0.5, 0.0), (-0.5, -0.5, 0.6)],
    "two arcs, a disk": [(-0.5, 0.0, 1.0), (0.5, 0.0, 1.0)],
    "concave": [(-0.6, -0.5, 0.0), (0.6, -0.5, 0.0), (0.6, 0.5, -0.8), (0.0, 0.0, -0.8), (-0.6, 0.5, 0.0)],
}


@pytest.mark.parametrize("name", list(ARC_POLYGONS))
def test_arc_polygon_matches_its_outline(name):
    corners = ARC_POLYGONS[name]
    v = [F3(*c) for c in corners]
    poly = outline(corners)
    for x, y in points(300, box=1.2):
        expected = polygon_distance(poly, x, y)
        d = sdf.sd_arc_polygon(v, F(x, y))
        assert d == pytest.approx(expected, abs=2e-4), (x, y)


def test_arc_polygon_two_half_circles_are_a_circle():
    v = [F3(-0.5, 0.0, 1.0), F3(0.5, 0.0, 1.0)]
    for x, y in points(300):
        assert sdf.sd_arc_polygon(v, F(x, y)) == pytest.approx(math.hypot(x, y) - 0.5, abs=1e-9)


def test_arc_polygon_without_bulges_is_the_polygon():
    corners = [(-0.6, -0.5), (0.6, -0.5), (0.6, 0.5), (0.0, 0.0), (-0.6, 0.5)]
    v = [F3(x, y, 0.0) for x, y in corners]
    for x, y in points(300):
        expected = sdf.sd_polygon([F(*c) for c in corners], F(x, y))
        assert sdf.sd_arc_polygon(v, F(x, y)) == pytest.approx(expected, abs=1e-12)


def test_arc_polygon_exact():
    v = [F3(*c) for c in ARC_POLYGONS["every bulge"]]
    assert_exact(lambda p: sdf.sd_arc_polygon(v, p))


# Repetition


def test_repeat():
    q = sdf.op_repeat(F(1.3, -2.2), F(1.0, 0.5))
    assert (q.x, q.y) == pytest.approx((0.3, -0.2))


def test_repeat_limited_stops_after_count():
    q = sdf.op_repeat_limited(F(5.2, 0.1), F(1.0, 1.0), F(2.0, 0.0))
    assert (q.x, q.y) == pytest.approx((3.2, 0.1))
    q = sdf.op_repeat_limited(F(-1.2, 3.0), F(1.0, 1.0), F(2.0, 0.0))
    assert (q.x, q.y) == pytest.approx((-0.2, 3.0))


@pytest.mark.parametrize("count", [3.0, 5.0, 6.0])
def test_repeat_polar(count):
    an = 2.0 * math.pi / count
    for x, y in points(200):
        q = sdf.op_repeat_polar(F(x, y), count)
        assert math.hypot(q.x, q.y) == pytest.approx(math.hypot(x, y))
        assert abs(math.atan2(q.y, q.x)) <= an / 2 + 1e-9
        # Turned by one copy's angle, p lands on the same point.
        c, s = math.cos(an), math.sin(an)
        turned = sdf.op_repeat_polar(F(c * x - s * y, s * x + c * y), count)
        assert (turned.x, turned.y) == pytest.approx((q.x, q.y), abs=1e-9)
