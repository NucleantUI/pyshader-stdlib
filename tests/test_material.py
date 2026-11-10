"""`material`, run on the CPU (tests/cpu.py): every material a valid surface
everywhere, each kind what it says it is, glass bending and tinting the view."""

import pytest

import cpu

material = cpu.load("pyshader.stdlib.fragment.material")
F2, F3, F4 = cpu.float2, cpu.float3, cpu.float4
UP = F3(0.0, 0.0, 1.0)
TILTED = cpu.normalize(F3(0.4, -0.2, 1.0))
RED = F3(0.8, 0.1, 0.1)

MATERIALS = {
    "plastic": lambda p, n: material.plastic(n, RED, 0.3),
    "ceramic": lambda p, n: material.ceramic(n, RED),
    "rubber": lambda p, n: material.rubber(p, n, RED),
    "metal": lambda p, n: material.metal(n, material.GOLD, 0.2),
    "brushed_metal": lambda p, n: material.brushed_metal(p, n, material.ALUMINUM, 0.5),
    "rust": lambda p, n: material.rust(p, n, material.IRON, 0.5),
    "rock": lambda p, n: material.rock(p, n),
    "granite": lambda p, n: material.granite(p, n),
    "marble": lambda p, n: material.marble(p, n, F3(0.9, 0.88, 0.85), F3(0.25, 0.27, 0.3)),
    "concrete": lambda p, n: material.concrete(p, n),
    "sand": lambda p, n: material.sand(p, n, F3(0.76, 0.6, 0.4)),
    "wood": lambda p, n: material.wood(p, n, F3(0.6, 0.4, 0.22), F3(0.3, 0.17, 0.08)),
    "leather": lambda p, n: material.leather(p, n, F3(0.35, 0.18, 0.1)),
    "fabric": lambda p, n: material.fabric(p, n, F3(0.2, 0.3, 0.8)),
    "ice": lambda p, n: material.ice(p, n),
}
POINTS = [F2(x * 0.37 - 1.1, y * 0.41 - 0.9) for x in range(6) for y in range(5)]


@pytest.mark.parametrize("name", sorted(MATERIALS))
def test_a_material_is_a_valid_surface_everywhere(name):
    for n in (UP, TILTED):
        for p in POINTS:
            s = MATERIALS[name](p, n)
            assert cpu.length(s.normal) == pytest.approx(1.0, abs=1e-6)
            assert s.normal.z > 0.0, "a bump never turns the surface away"
            assert all(0.0 <= c <= 1.0 for c in s.albedo), s.albedo
            assert 0.0 <= s.roughness <= 1.0 and 0.0 <= s.metallic <= 1.0
            assert 0.0 < s.specular < 0.1


@pytest.mark.parametrize("name", ["rubber", "rock", "concrete", "sand", "leather", "fabric", "brushed_metal"])
def test_textured_materials_vary_and_bump(name):
    surfaces = [MATERIALS[name](p, UP) for p in POINTS]
    assert len({round(s.albedo.x, 4) for s in surfaces}) > 3
    assert any(s.normal.z < 0.9999 for s in surfaces)


def test_metals_are_metallic_and_the_rest_are_not():
    for name in ("metal", "brushed_metal"):
        assert MATERIALS[name](POINTS[0], UP).metallic == 1.0
    for name in ("plastic", "ceramic", "rubber", "rock", "granite", "marble", "concrete", "sand", "wood", "leather", "fabric", "ice"):
        assert MATERIALS[name](POINTS[0], UP).metallic == 0.0


def test_rubber_is_rougher_than_plastic_and_ceramic_smoother_still():
    p = POINTS[3]
    assert MATERIALS["rubber"](p, UP).roughness > 0.7 > MATERIALS["plastic"](p, UP).roughness > MATERIALS["ceramic"](p, UP).roughness


def test_rust_grows_with_its_amount():
    def mean_metallic(amount):
        return sum(material.rust(p, UP, material.IRON, amount).metallic for p in POINTS) / len(POINTS)
    clean, half, rusted = mean_metallic(0.0), mean_metallic(0.5), mean_metallic(1.0)
    assert clean == pytest.approx(1.0)
    assert clean > half > rusted
    assert rusted < 0.1


def test_marble_has_veins():
    tones = [MATERIALS["marble"](F2(x * 0.05, 0.3), UP).albedo.x for x in range(80)]
    assert min(tones) < 0.5 < 0.8 < max(tones)


def test_metal_reflectances_are_linear_colors():
    for name in ("GOLD", "SILVER", "COPPER", "BRASS", "ALUMINUM", "IRON", "CHROMIUM"):
        assert all(0.3 < c <= 1.0 for c in getattr(material, name))
    assert material.GOLD.z < material.GOLD.x, "gold reflects less blue"


def test_water_normal():
    assert list(material.water_normal(F2(0.3, 0.2), 1.0, 0.0)) == pytest.approx([0.0, 0.0, 1.0])
    n = material.water_normal(F2(0.3, 0.2), 1.0, 0.3)
    assert cpu.length(n) == pytest.approx(1.0) and n.z < 1.0
    later = material.water_normal(F2(0.3, 0.2), 2.0, 0.3)
    assert list(later) != pytest.approx(list(n)), "the waves move"


# Glass


def test_refraction_head_on_or_through_air_moves_nothing():
    assert list(material.refraction_offset(UP, material.GLASS_IOR, 0.1)) == pytest.approx([0.0, 0.0], abs=1e-9)
    assert list(material.refraction_offset(TILTED, 1.0, 0.1)) == pytest.approx([0.0, 0.0], abs=1e-9)


def test_refraction_bends_more_with_a_higher_index_and_thickness():
    glass = cpu.length(material.refraction_offset(TILTED, material.GLASS_IOR, 0.1))
    diamond = cpu.length(material.refraction_offset(TILTED, material.DIAMOND_IOR, 0.1))
    thick = cpu.length(material.refraction_offset(TILTED, material.GLASS_IOR, 0.2))
    assert 0.0 < glass < diamond
    assert thick == pytest.approx(2.0 * glass)


def test_absorb_follows_beer_lambert():
    tint = F3(0.5, 0.8, 1.0)
    assert list(material.absorb(tint, 0.0)) == pytest.approx([1.0] * 3)
    assert list(material.absorb(tint, 1.0)) == pytest.approx([0.5, 0.8, 1.0])
    assert list(material.absorb(tint, 2.0)) == pytest.approx([0.25, 0.64, 1.0])


def no_light():
    return F3(0.0, 0.0, 1.0), F3(0.0)


def test_clear_glass_head_on_shows_the_background():
    light, dark = no_light()
    c = material.glass(F3(0.2, 0.5, 0.9), UP, light, dark, F3(0.0), F3(1.0), material.GLASS_IOR, 1.0)
    # Head on, glass reflects (1.5 - 1)² / (1.5 + 1)² = 4%.
    assert list(c) == pytest.approx([0.2 * 0.96, 0.5 * 0.96, 0.9 * 0.96])


def test_glass_reflects_more_at_its_rim():
    light, dark = no_light()
    rim = cpu.normalize(F3(1.0, 0.0, 0.08))
    head_on = material.glass(F3(0.0), UP, light, dark, F3(1.0), F3(1.0), material.GLASS_IOR, 1.0).x
    grazing = material.glass(F3(0.0), rim, light, dark, F3(1.0), F3(1.0), material.GLASS_IOR, 1.0).x
    assert head_on == pytest.approx(0.04) and grazing > 0.5


def test_glass_over_samples_where_the_pane_bends_the_view():
    light, dark = no_light()
    texture = cpu.Texture(lambda uv: F4(uv.x, uv.y, 0.0, 1.0))
    uv = F2(0.4, 0.6)
    shift = material.refraction_offset(TILTED, material.GLASS_IOR, 0.1)
    c = material.glass_over(texture, uv, TILTED, light, dark, F3(0.0), F3(1.0), material.GLASS_IOR, 0.1)
    expected = material.glass(F3(uv.x + shift.x, uv.y + shift.y, 0.0), TILTED, light, dark, F3(0.0), F3(1.0), material.GLASS_IOR, 0.1)
    assert list(c) == pytest.approx(list(expected))


def test_frosted_glass_blurs():
    light, dark = no_light()
    flat = cpu.Texture(lambda uv: F4(0.3, 0.6, 0.9, 1.0))
    c = material.frosted_glass_over(flat, F2(0.5, 0.5), UP, light, dark, F3(0.0), F3(1.0), material.GLASS_IOR, 0.1, 0.05)
    assert list(c) == pytest.approx([0.3 * 0.96, 0.6 * 0.96, 0.9 * 0.96])
    # Over a hard edge, the frost mixes both sides.
    edge = cpu.Texture(lambda uv: F4(1.0 if uv.x > 0.5 else 0.0, 0.0, 0.0, 1.0))
    sharp = material.glass_over(edge, F2(0.51, 0.5), UP, light, dark, F3(0.0), F3(1.0), material.GLASS_IOR, 0.1).x
    frosted = material.frosted_glass_over(edge, F2(0.51, 0.5), UP, light, dark, F3(0.0), F3(1.0), material.GLASS_IOR, 0.1, 0.05).x
    assert sharp == pytest.approx(0.96) and 0.2 < frosted < 0.8


def test_ice_has_white_fractures():
    # Along a line across many cells, through their borders.
    tones = [material.ice(F2(x * 0.004, 0.37 + x * 0.0013), UP).albedo.x for x in range(2000)]
    assert max(tones) > 0.9 and min(tones) < 0.2
