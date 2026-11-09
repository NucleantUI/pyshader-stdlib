"""`light`, run on the CPU (tests/cpu.py): the closed forms against brute-force
sums of what they stand for, and every curve where its docstring puts it."""

import math
import random

import pytest

import cpu

light = cpu.load("pyshader.stdlib.fragment.light")
F, F3 = cpu.float2, cpu.float3


def points(count: int, box: float = 1.0, seed: int = 0):
    rng = random.Random(seed)
    return [(rng.uniform(-box, box), rng.uniform(-box, box)) for _ in range(count)]


# Falloff and glow


@pytest.mark.parametrize("name", ["falloff_inverse_square", "falloff_exp", "falloff_gaussian", "falloff_range"])
def test_falloff_is_one_at_zero_and_fades(name):
    f = getattr(light, name)
    values = [f(d, 0.3) for d in (0.0, 0.1, 0.2, 0.4, 0.8)]
    assert values[0] == pytest.approx(1.0)
    assert all(a >= b for a, b in zip(values, values[1:])) and values[1] < 1.0


def test_falloff_inverse_square_is_half_at_radius():
    assert light.falloff_inverse_square(0.3, 0.3) == pytest.approx(0.5)


def test_falloff_range_ends_at_its_reach():
    assert light.falloff_range(0.3, 0.3) == 0.0
    assert light.falloff_range(1.0, 0.3) == 0.0


def test_glows():
    assert light.glow(-0.2, 0.1) == 1.0 and light.glow(0.1, 0.1) == pytest.approx(0.5)
    assert light.glow_inner(0.0, 0.1) == 1.0 and light.glow_inner(0.01, 0.1) == 0.0
    assert light.glow_inner(-0.1, 0.1) == pytest.approx(math.exp(-1.0))
    assert light.glow_edge(-0.1, 0.1) == light.glow_edge(0.1, 0.1) == pytest.approx(0.5)


def test_neon_core_is_white_hot():
    c = light.neon(0.0, F3(0.2, 0.6, 1.0), 0.02, 0.05)
    assert list(c) == pytest.approx([1.2, 1.6, 2.0])
    far = light.neon(0.5, F3(0.2, 0.6, 1.0), 0.02, 0.05)
    assert max(far) < 0.02


def test_segment_light_is_its_points_added_up():
    a, b, radius = (-0.3, 0.1), (0.4, -0.2), 0.05
    steps = 4000
    for x, y in points(40):
        total = 0.0
        for i in range(steps):
            t = (i + 0.5) / steps
            sx, sy = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            total += 1.0 / ((x - sx) ** 2 + (y - sy) ** 2 + radius * radius)
        expected = radius / math.pi * total * math.dist(a, b) / steps
        assert light.segment_light(F(x, y), F(*a), F(*b), radius) == pytest.approx(expected, rel=1e-4)


def test_segment_light_is_one_on_a_long_tube():
    assert light.segment_light(F(0.0, 0.0), F(-1e4, 0.0), F(1e4, 0.0), 0.05) == pytest.approx(1.0, rel=1e-4)


# LEDs


def test_led_core_and_halo():
    assert list(light.led(F(0.0, 0.0), F3(1.0, 0.0, 0.0), 0.02, 0.05)) == pytest.approx([2.0, 1.0, 1.0])
    halo = light.led(F(0.07, 0.0), F3(1.0, 0.0, 0.0), 0.02, 0.05)
    assert list(halo) == pytest.approx([0.5, 0.0, 0.0])


@pytest.mark.parametrize("count", [8.0, 12.0, 24.0])
def test_led_ring_index_finds_the_nearest(count):
    for x, y in points(300):
        i = light.led_ring_index(F(x, y), count)
        assert i == int(i) and 0 <= i < count
        here = light.led_ring_position(i, count, 0.4)
        nearest = min(range(int(count)), key=lambda k: math.dist((x, y), tuple(light.led_ring_position(k, count, 0.4))))
        assert math.dist((x, y), tuple(here)) == pytest.approx(
            math.dist((x, y), tuple(light.led_ring_position(nearest, count, 0.4))))


def test_led_ring_position():
    assert list(light.led_ring_position(0.0, 12.0, 0.4)) == pytest.approx([0.4, 0.0])
    assert list(light.led_ring_position(3.0, 12.0, 0.4)) == pytest.approx([0.0, 0.4])


def test_chase():
    brightness = [light.chase(float(i), 12.0, 5.0, 4.0) for i in range(12)]
    assert brightness[5] == 1.0
    assert brightness[4] > brightness[3] > brightness[2] > 0.0
    assert brightness[1] == brightness[6] == brightness[7] == 0.0
    # Between LEDs the next one fades in.
    assert light.chase(6.0, 12.0, 5.25, 4.0) == pytest.approx(0.25)
    # Wraps around the ring.
    assert light.chase(11.0, 12.0, 0.0, 4.0) == pytest.approx((1.0 - 1.0 / 4.0) ** 2)


def test_breathe():
    values = [light.breathe(t / 100.0, 1.0) for t in range(101)]
    assert min(values) == pytest.approx(0.0, abs=1e-9) and max(values) == pytest.approx(1.0, abs=1e-9)
    assert values[0] == pytest.approx(0.0) and values[50] == pytest.approx(1.0)


def test_flicker_stays_within_its_amount():
    values = [light.flicker(t / 30.0, 3.0, 0.6) for t in range(600)]
    assert all(0.4 - 1e-9 <= v <= 1.0 for v in values)
    assert min(values) < 0.6 and max(values) > 0.95


# Shading


def test_sphere_normal():
    assert list(light.sphere_normal(F(0.0, 0.0), 0.5)) == pytest.approx([0.0, 0.0, 1.0])
    for x, y in points(100):
        n = light.sphere_normal(F(x, y), 0.5)
        assert cpu.length(n) == pytest.approx(1.0)
    assert list(light.sphere_normal(F(0.9, 0.0), 0.5)) == pytest.approx([1.0, 0.0, 0.0])


def test_bevel_normal():
    assert list(light.bevel_normal(-0.5, F(1.0, 0.0), 0.1)) == pytest.approx([0.0, 0.0, 1.0])
    edge = light.bevel_normal(0.0, F(0.0, 1.0), 0.1)
    assert edge.y > 0.99 and cpu.length(edge) == pytest.approx(1.0)
    mid = light.bevel_normal(-0.05, F(0.0, 1.0), 0.1)
    assert 0.0 < mid.y < 1.0 and mid.z > 0.0


def test_lighting_terms():
    up = F3(0.0, 0.0, 1.0)
    assert light.lambert(up, up) == 1.0 and light.lambert(up, F3(0.0, 0.0, -1.0)) == 0.0
    assert light.blinn_phong(up, up, 32.0) == pytest.approx(1.0)
    assert light.fresnel(up, 0.04, 5.0) == pytest.approx(0.04)
    assert light.fresnel(F3(1.0, 0.0, 0.0), 0.04, 5.0) == pytest.approx(1.0)


def test_shine():
    assert light.shine(F(0.3, 0.0), 0.0, 0.3, 0.1) == 1.0
    assert light.shine(F(0.4, 0.0), 0.0, 0.3, 0.1) == 0.0


# Shadows


def test_erf():
    for i in range(-40, 41):
        x = i / 10.0
        assert light.erf(x) == pytest.approx(math.erf(x), abs=1e-3)


def test_drop_shadow_is_a_blurred_edge():
    sigma = 0.05
    for d in (-0.1, -0.03, 0.0, 0.02, 0.08):
        assert light.drop_shadow(d, sigma) == pytest.approx(0.5 * math.erfc(d / (sigma * math.sqrt(2.0))), abs=5e-4 + 1e-9)


def blurred_box(x: float, y: float, half: tuple[float, float], corner: float, sigma: float, n: int = 160) -> float:
    """The rounded box's mask convolved with a Gaussian, summed on a grid."""
    reach = 4.0 * sigma
    step = 2.0 * reach / n
    total = 0.0
    for i in range(n):
        u = -reach + (i + 0.5) * step
        for j in range(n):
            v = -reach + (j + 0.5) * step
            qx, qy = abs(x - u) - half[0] + corner, abs(y - v) - half[1] + corner
            d = min(max(qx, qy), 0.0) + math.hypot(max(qx, 0.0), max(qy, 0.0)) - corner
            if d < 0.0:
                total += math.exp(-(u * u + v * v) / (2.0 * sigma * sigma))
    return total * step * step / (2.0 * math.pi * sigma * sigma)


@pytest.mark.parametrize("corner", [0.0, 0.08])
def test_box_shadow_is_a_blurred_box(corner):
    half, sigma = (0.3, 0.2), 0.06
    for x, y in [(0.0, 0.0), (0.3, 0.0), (0.0, 0.2), (0.3, 0.2), (0.35, 0.25), (0.25, 0.15), (0.45, 0.1)]:
        expected = blurred_box(x, y, half, corner, sigma)
        assert light.box_shadow(F(x, y), F(*half), corner, sigma) == pytest.approx(expected, abs=0.02), (x, y)


def visible_fraction(p, light_pos, light_radius, center, radius, n: int = 4000) -> float:
    """Rays from p spread evenly over the light's angle: the share not stopped
    by the disk before they reach the light."""
    dx, dy = light_pos[0] - p[0], light_pos[1] - p[1]
    dl = math.hypot(dx, dy)
    base = math.atan2(dy, dx)
    half = math.asin(min(light_radius / dl, 1.0))
    seen = 0
    for i in range(n):
        a = base - half + 2.0 * half * (i + 0.5) / n
        ux, uy = math.cos(a), math.sin(a)
        ox, oy = center[0] - p[0], center[1] - p[1]
        along = ox * ux + oy * uy
        across2 = ox * ox + oy * oy - along * along
        blocked = across2 < radius * radius and along - math.sqrt(radius * radius - across2) < dl and along > 0.0
        seen += not blocked
    return seen / n


def test_circle_shadow_is_the_light_it_sees():
    light_pos, light_radius = (0.0, 0.8), 0.1
    center, radius = (0.05, 0.3), 0.12
    for x, y in points(150, box=1.0, seed=3):
        if math.dist((x, y), center) <= radius or math.dist((x, y), light_pos) <= light_radius:
            continue
        expected = visible_fraction((x, y), light_pos, light_radius, center, radius)
        got = light.circle_shadow(F(x, y), F(*light_pos), light_radius, F(*center), radius)
        assert got == pytest.approx(expected, abs=0.01), (x, y)


def test_circle_shadow_in_the_disk_is_dark():
    assert light.circle_shadow(F(0.05, 0.3), F(0.0, 0.8), 0.1, F(0.05, 0.3), 0.12) == 0.0


def test_soft_shadow_step():
    assert light.soft_shadow_step(1.0, 0.5, 1.0, 8.0) == 1.0
    assert light.soft_shadow_step(1.0, 0.01, 1.0, 8.0) == pytest.approx(0.08)


def test_occlusion():
    assert light.occlusion(0.0, 0.2, 0.6) == pytest.approx(0.4)
    assert light.occlusion(0.3, 0.2, 0.6) == 1.0


# Tone mapping


@pytest.mark.parametrize("name", ["tonemap_exposure", "tonemap_reinhard", "tonemap_aces"])
def test_tonemaps_stay_in_range_and_keep_order(name):
    f = getattr(light, name)
    args = (1.0,) if name == "tonemap_exposure" else ()
    values = [f(F3(x), *args).x for x in (0.0, 0.1, 0.5, 1.0, 4.0, 50.0)]
    assert all(0.0 <= v <= 1.0 for v in values)
    assert all(a < b for a, b in zip(values, values[1:]))
