"""`surface`, run on the CPU (tests/cpu.py): the microfacet model's pieces
against what they stand for, and `shade` against conservation of energy."""

import math

import pytest

import cpu

surface = cpu.load("pyshader.stdlib.fragment.surface")
F2, F3 = cpu.float2, cpu.float3
UP = F3(0.0, 0.0, 1.0)


def hemisphere(steps_theta: int = 48, steps_phi: int = 96):
    """Directions over the upper hemisphere (z up) with their solid angle."""
    for i in range(steps_theta):
        theta = (i + 0.5) / steps_theta * math.pi / 2.0
        d_theta = math.pi / 2.0 / steps_theta
        for j in range(steps_phi):
            phi = (j + 0.5) / steps_phi * 2.0 * math.pi
            yield F3(math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)), \
                math.sin(theta) * d_theta * (2.0 * math.pi / steps_phi)


def white(roughness: float, metallic: float):
    return surface.Surface(F3(1.0), UP, roughness, metallic, 0.04)


@pytest.mark.parametrize("roughness", [0.3, 0.5, 0.8, 1.0])
def test_ggx_projects_to_one(roughness):
    # The microfacets' projected area is the surface's own: ∫ D(h) (n·h) dω = 1.
    total = sum(surface.ggx(h.z, roughness) * h.z * dw for h, dw in hemisphere(160, 8))
    assert total == pytest.approx(1.0, abs=0.02)


def test_ggx_is_sharper_when_smoother():
    assert surface.ggx(1.0, 0.2) > surface.ggx(1.0, 0.5) > surface.ggx(1.0, 0.9)


def test_fresnel_from_head_on_to_grazing():
    f0 = F3(0.04, 0.5, 0.9)
    assert list(surface.fresnel_schlick(1.0, f0)) == pytest.approx([0.04, 0.5, 0.9])
    assert list(surface.fresnel_schlick(0.0, f0)) == pytest.approx([1.0, 1.0, 1.0])
    head_on, oblique = surface.fresnel_schlick(0.9, f0).x, surface.fresnel_schlick(0.3, f0).x
    assert head_on < oblique


def test_rough_surfaces_brighten_less_at_the_rim():
    f0 = F3(0.04)
    assert surface.fresnel_roughness(0.0, f0, 0.9).x < surface.fresnel_roughness(0.0, f0, 0.1).x


def test_reflectance_is_specular_for_dielectrics_and_the_albedo_for_metals():
    s = surface.Surface(F3(0.9, 0.6, 0.2), UP, 0.5, 0.0, 0.04)
    assert list(surface.reflectance(s)) == pytest.approx([0.04] * 3)
    m = surface.Surface(F3(0.9, 0.6, 0.2), UP, 0.5, 1.0, 0.04)
    assert list(surface.reflectance(m)) == pytest.approx([0.9, 0.6, 0.2])


@pytest.mark.parametrize("roughness", [0.2, 0.5, 0.9])
@pytest.mark.parametrize("metallic", [0.0, 1.0])
@pytest.mark.parametrize("light_angle", [0.0, 0.6, 1.2, 1.45])
def test_shade_sends_out_no_more_light_than_comes_in(roughness, metallic, light_angle):
    # Light of 1 from `light_angle` off the normal brings cos(angle); what leaves
    # over the hemisphere, ∫ L(v) (n·v) dω, is never more.
    light = F3(math.sin(light_angle), 0.0, math.cos(light_angle))
    # Fine in theta: a smooth surface's highlight is a narrow peak.
    out = sum(surface.shade(white(roughness, metallic), light, v, F3(1.0)).y * v.z * dw for v, dw in hemisphere(96, 128))
    assert 0.0 < out <= math.cos(light_angle) * 1.01


def test_a_white_matte_dielectric_keeps_most_of_the_light():
    out = sum(surface.shade(white(1.0, 0.0), UP, v, F3(1.0)).y * v.z * dw for v, dw in hemisphere(32, 64))
    assert out > 0.85


def test_shade_is_dark_lit_from_behind():
    # Straight from behind: light + view is zero, which must not make a NaN.
    assert list(surface.shade(white(0.5, 0.0), F3(0.0, 0.0, -1.0), UP, F3(1.0))) == pytest.approx([0.0] * 3)
    assert list(surface.shade(white(0.5, 0.0), F3(0.6, 0.0, -0.8), UP, F3(1.0))) == pytest.approx([0.0] * 3)


def test_the_highlight_peaks_at_the_mirror_direction():
    light = surface.normalize(F3(0.5, 0.0, 1.0))
    mirror = F3(-light.x, 0.0, light.z)
    off = surface.normalize(F3(0.3, 0.0, 1.0))
    s = surface.Surface(F3(0.0), UP, 0.2, 0.0, 0.04)
    assert surface.shade(s, light, mirror, F3(1.0)).x > 5.0 * surface.shade(s, light, off, F3(1.0)).x


def test_a_metal_has_no_diffuse():
    # Rough metal seen far from the mirror direction: only a faint highlight.
    light = surface.normalize(F3(1.0, 0.0, 0.3))
    view = surface.normalize(F3(0.9, 0.0, 0.4))
    metal = surface.shade(surface.Surface(F3(1.0), UP, 0.3, 1.0, 0.04), light, view, F3(1.0)).x
    plastic = surface.shade(surface.Surface(F3(1.0), UP, 0.3, 0.0, 0.04), light, view, F3(1.0)).x
    assert metal < plastic


def test_ambient_is_positive_and_no_more_than_the_surroundings():
    for metallic in (0.0, 1.0):
        a = surface.shade_ambient(white(0.5, metallic), UP, F3(1.0), F3(1.0))
        assert all(0.0 < c <= 1.0 for c in a)


def test_a_smooth_metal_mirrors_its_surroundings_and_a_rough_one_blurs_them():
    gold = F3(1.0, 0.766, 0.336)
    mirror = surface.shade_ambient(surface.Surface(gold, UP, 0.0, 1.0, 0.04), UP, F3(0.0), F3(1.0))
    assert list(mirror) == pytest.approx(list(gold), abs=1e-6), "head on, a mirror reflects its f0 of what it sees"
    rough = surface.shade_ambient(surface.Surface(gold, UP, 1.0, 1.0, 0.04), UP, F3(0.2), F3(1.0))
    assert rough.x < mirror.x
    plastic = surface.shade_ambient(surface.Surface(F3(0.5), UP, 0.0, 0.0, 0.04), UP, F3(0.0), F3(1.0))
    assert plastic.x == pytest.approx(0.04), "a dielectric mirrors only its 4%"


def test_bump_tilts_away_from_uphill():
    assert list(surface.bump(UP, F2(0.0, 0.0), 1.0)) == pytest.approx([0.0, 0.0, 1.0])
    n = surface.bump(UP, F2(1.0, 0.0), 0.5)
    assert n.x < 0.0 and cpu.length(n) == pytest.approx(1.0)


def test_blend_ends_at_each_surface():
    a = surface.Surface(F3(1.0, 0.0, 0.0), UP, 0.1, 1.0, 0.04)
    b = surface.Surface(F3(0.0, 0.0, 1.0), surface.normalize(F3(1.0, 0.0, 1.0)), 0.9, 0.0, 0.02)
    start = surface.blend(a, b, 0.0)
    assert list(start.albedo) == pytest.approx(list(a.albedo)) and list(start.normal) == pytest.approx(list(a.normal))
    assert start.roughness == pytest.approx(0.1) and start.metallic == 1.0
    end = surface.blend(a, b, 1.0)
    assert list(end.albedo) == pytest.approx(list(b.albedo)) and end.roughness == pytest.approx(0.9)
    half = surface.blend(a, b, 0.5)
    assert half.metallic == pytest.approx(0.5) and cpu.length(half.normal) == pytest.approx(1.0)
