"""Materials: plastic, rubber, metals, stone, wood, leather, fabric, glass and
ice, each a function giving the `surface.Surface` of a point, to light with
`surface.shade`.

A material takes `p`, where the point is on the material (scale it to make
the grain finer or coarser), and `n`, the way the shape faces there
(`light.sphere_normal`, `light.bevel_normal`, or a real 3D normal), which its
bumps tilt. A color is linear.

    n = light.bevel_normal(d, grad, 0.05)
    s = material.marble(p * 3.0, n, float3(0.9, 0.88, 0.85), float3(0.25, 0.27, 0.3))
    c = surface.shade(s, l, float3(0.0, 0.0, 1.0), float3(3.0))

Glass and ice are seen through: `glass` takes the background behind the
pane as you sample it at `refraction_offset`, or `glass_over` and
`frosted_glass_over` sample a texture there themselves (compute and graphics
targets, which have textures).

Credits:
- The metals' reflectances (`GOLD` … `CHROMIUM`), linear: Naty Hoffman,
  "Background: Physics and Math of Shading" (SIGGRAPH 2013 course)
- `absorb`: the Beer-Lambert law
- `frosted_glass_over`: its samples on Vogel's spiral (the golden angle),
  Helmut Vogel, "A better way to construct the sunflower head" (1979)
- Marble's veins as turbulent sine bands: Ken Perlin, "An Image Synthesizer"
  (SIGGRAPH 1985)
"""
from pyshader import *
from .surface import Surface, bump, blend, fresnel_schlick, shade
from .noise import value_noise, fbm, turbulence, ridge
from .cellular import cellular, cellular2, voronoi
from .random import random
from .matrix import rotate2d

# Reflectance of metals head on (their albedo), linear.
GOLD = float3(1.0, 0.766, 0.336)
SILVER = float3(0.972, 0.96, 0.915)
COPPER = float3(0.955, 0.637, 0.538)
BRASS = float3(0.91, 0.778, 0.423)
ALUMINUM = float3(0.913, 0.922, 0.924)
IRON = float3(0.562, 0.565, 0.578)
CHROMIUM = float3(0.55, 0.556, 0.554)

# Indices of refraction.
WATER_IOR = 1.33
ICE_IOR = 1.31
GLASS_IOR = 1.5
DIAMOND_IOR = 2.42

# The finite difference the height fields' slopes are taken over.
_E = 0.01


# Smooth dielectrics and metals


def plastic(n: float3, color: float3, roughness: float) -> Surface:
    """Plastic: its own color under a white highlight, sharp when smooth
    (roughness 0.2), spread when matte (0.6)."""
    return Surface(color, n, roughness, 0.0, 0.04)


def ceramic(n: float3, color: float3) -> Surface:
    """Glazed ceramic: glossy, a small bright highlight and a clear rim."""
    return Surface(color, n, 0.08, 0.0, 0.05)


def rubber(p: float2, n: float3, color: float3) -> Surface:
    """Rubber: matte and soft, a dim wide highlight over a faint grain."""
    g = value_noise(p * 40.0)
    gx = value_noise((p + float2(_E, 0.0)) * 40.0)
    gy = value_noise((p + float2(0.0, _E)) * 40.0)
    s = float2(gx - g, gy - g) / _E
    return Surface(color * (0.92 + 0.08 * g), bump(n, s, 0.004), 0.8 + 0.1 * g, 0.0, 0.03)


def metal(n: float3, color: float3, roughness: float) -> Surface:
    """Polished (roughness 0.1) to blasted (0.6) metal: no diffuse, the
    highlight in the metal's own color (`GOLD`, `COPPER`, …)."""
    return Surface(color, n, roughness, 1.0, 0.04)


def brushed_metal(p: float2, n: float3, color: float3, angle: float) -> Surface:
    """Brushed metal: fine streaks along `angle`, the highlight smeared along them."""
    m = rotate2d(-angle)
    q = m * p
    g = value_noise(float2(q.x * 2.0, q.y * 160.0))
    gy = value_noise(float2(q.x * 2.0, (q.y + _E) * 160.0))
    # The slope only runs across the streaks: turned back into p's directions.
    s = rotate2d(angle) * float2(0.0, (gy - g) / _E)
    return Surface(color * (0.88 + 0.12 * g), bump(n, s, 0.0015), 0.28 + 0.12 * g, 1.0, 0.04)


def rust(p: float2, n: float3, color: float3, amount: float) -> Surface:
    """A metal of `color` rusting: rough, orange-brown patches eating into it
    from `amount` 0 (clean) to 1 (all rust)."""
    patch = fbm(p * 1.5, 5) + 0.3 * (1.0 - cellular(p * 4.0, 0.0))
    t = smoothstep(1.0 - amount, 1.15 - amount, patch)
    grain = fbm(p * 12.0, 3)
    gx = fbm((p + float2(_E, 0.0)) * 12.0, 3)
    gy = fbm((p + float2(0.0, _E)) * 12.0, 3)
    rusted = Surface(
        mix(float3(0.35, 0.12, 0.04), float3(0.62, 0.28, 0.1), grain),
        bump(n, float2(gx - grain, gy - grain) / _E, 0.02),
        0.9, 0.0, 0.04,
    )
    return blend(metal(n, color, 0.35), rusted, t)


# Stone


def rock(p: float2, n: float3) -> Surface:
    """Rough rock: ridged and cracked, grey-brown, the cracks dark."""
    h = ridge(p, 5)
    hx = ridge(p + float2(_E, 0.0), 5)
    hy = ridge(p + float2(0.0, _E), 5)
    cells = cellular2(p * 2.0, 0.0)
    crack = 1.0 - smoothstep(0.0, 0.08, cells.y - cells.x)
    tone = fbm(p * 3.0, 4)
    albedo = mix(float3(0.22, 0.2, 0.18), float3(0.52, 0.48, 0.43), tone) * (1.0 - 0.7 * crack)
    return Surface(albedo, bump(n, float2(hx - h, hy - h) / _E, 0.015), 0.85, 0.0, 0.04)


def granite(p: float2, n: float3) -> Surface:
    """Polished granite: crystals of grey feldspar, pink feldspar and black
    mica, about a twelfth of a unit of p across, under a gloss."""
    q = p * 12.0
    v = voronoi(q, 0.0)
    # The crystal's point lies in its own cell: its floor names the crystal.
    g = random(floor(q + v.yz))
    albedo = float3(0.45, 0.44, 0.43)
    if g > 0.6:
        albedo = float3(0.6, 0.44, 0.4)
    if g < 0.22:
        albedo = float3(0.05, 0.05, 0.06)
    tone = 0.85 + 0.15 * random(floor(q + v.yz) + float2(17.0, 3.0))
    return Surface(albedo * tone, n, 0.2, 0.0, 0.045)


def marble(p: float2, n: float3, base: float3, vein: float3) -> Surface:
    """Polished marble: `base` stone with winding veins of `vein`."""
    t = turbulence(p * 0.6, 5)
    v = abs(sin(p.x * 2.0 + p.y + t * 7.0))
    veins = pow(1.0 - v, 6.0)
    albedo = mix(base * (0.94 + 0.06 * t), vein, veins)
    return Surface(albedo, n, 0.12 + 0.1 * veins, 0.0, 0.045)


def concrete(p: float2, n: float3) -> Surface:
    """Concrete: mottled grey, fine grit, small dark pits."""
    tone = fbm(p * 2.0, 4)
    h = value_noise(p * 30.0)
    hx = value_noise((p + float2(_E, 0.0)) * 30.0)
    hy = value_noise((p + float2(0.0, _E)) * 30.0)
    pit = 1.0 - smoothstep(0.0, 0.12, cellular(p * 5.0, 0.0))
    albedo = float3(0.42 + 0.18 * tone) * (1.0 - 0.5 * pit)
    return Surface(albedo, bump(n, float2(hx - h, hy - h) / _E, 0.003), 0.92, 0.0, 0.04)


def sand(p: float2, n: float3, color: float3) -> Surface:
    """Sand: wind ripples, one every unit of p or so, and grains; very matte."""
    ripple = sin(p.y * 6.0 + fbm(p, 3) * 4.0)
    ripple_y = sin((p.y + _E) * 6.0 + fbm(p + float2(0.0, _E), 3) * 4.0)
    ripple_x = sin(p.y * 6.0 + fbm(p + float2(_E, 0.0), 3) * 4.0)
    grain = random(floor(p * 60.0))
    s = float2(ripple_x - ripple, ripple_y - ripple) / _E
    tone = 0.8 + 0.1 * ripple + 0.1 * grain
    return Surface(color * tone, bump(n, s, 0.05), 0.97, 0.0, 0.03)


# Organic


def wood(p: float2, n: float3, light: float3, dark: float3) -> Surface:
    """Wood: growth rings, warped, with grain along them; satin finish."""
    warp = fbm(p * 0.7, 3) * 1.5
    rings = fract(length(p * float2(1.0, 0.3)) * 4.0 + warp)
    band = smoothstep(0.0, 0.25, rings) * (1.0 - smoothstep(0.6, 1.0, rings))
    grain = value_noise(float2(p.x * 2.0, p.y * 60.0))
    albedo = mix(dark, light, band * 0.8 + 0.2 * grain)
    return Surface(albedo, n, 0.5 + 0.1 * grain, 0.0, 0.04)


def leather(p: float2, n: float3, color: float3) -> Surface:
    """Leather: pebbled cells, darker in the creases between them."""
    c = cellular2(p, 0.0)
    h = smoothstep(0.0, 0.3, c.y - c.x)
    cx = cellular2(p + float2(_E, 0.0), 0.0)
    cy = cellular2(p + float2(0.0, _E), 0.0)
    hx = smoothstep(0.0, 0.3, cx.y - cx.x)
    hy = smoothstep(0.0, 0.3, cy.y - cy.x)
    return Surface(color * (0.6 + 0.4 * h), bump(n, float2(hx - h, hy - h) / _E, 0.01), 0.6, 0.0, 0.04)


def fabric(p: float2, n: float3, color: float3) -> Surface:
    """Woven fabric: threads over and under each other, one per unit of p."""
    u = fract(p)
    over = mod(floor(p.x) + floor(p.y), 2.0)
    # A thread is round across: its height is a sine over its width.
    h = mix(sin(u.y * PI), sin(u.x * PI), over)
    s = mix(float2(0.0, PI * cos(u.y * PI)), float2(PI * cos(u.x * PI), 0.0), over)
    return Surface(color * (0.6 + 0.4 * h), bump(n, s, 0.15), 0.95, 0.0, 0.03)


# Water, glass and ice


def water_normal(p: float2, time: float, strength: float) -> float3:
    """The way still water faces, rippled by two drifting layers of waves;
    `strength` 0.05 is a breeze, 0.3 choppy."""
    a = p + float2(time * 0.3, time * 0.2)
    b = p * 1.7 - float2(time * 0.25, -time * 0.15)
    h = fbm(a, 4) + 0.5 * fbm(b, 4)
    hx = fbm(a + float2(_E, 0.0), 4) + 0.5 * fbm(b + float2(_E * 1.7, 0.0), 4)
    hy = fbm(a + float2(0.0, _E), 4) + 0.5 * fbm(b + float2(0.0, _E * 1.7), 4)
    return bump(float3(0.0, 0.0, 1.0), float2(hx - h, hy - h) / _E, strength)


def refraction_offset(n: float3, ior: float, thickness: float) -> float2:
    """How far the background behind a pane facing `n` shifts in view, light
    bent going in (index of refraction `ior`) through `thickness`: add it to
    where you sample the background."""
    r = refract(float3(0.0, 0.0, -1.0), n, 1.0 / ior)
    return r.xy * thickness


def absorb(tint: float3, thickness: float) -> float3:
    """What gets through tinted glass of `thickness`: `tint` through a
    thickness of 1, deeper color through more (Beer-Lambert)."""
    return pow(max(tint, float3(0.0001)), float3(thickness))


def glass(background: float3, n: float3, light: float3, light_color: float3, reflected: float3,
          tint: float3, ior: float, thickness: float) -> float3:
    """A pane of glass facing `n`: the `background` seen through it (sample it
    at `refraction_offset`), tinted by `absorb`, plus what it reflects
    (`reflected`, the room or sky) by Fresnel and the light's highlight. Glass
    is mostly see-through head on and a mirror at its rim."""
    view = float3(0.0, 0.0, 1.0)
    k = (ior - 1.0) / (ior + 1.0)
    f = fresnel_schlick(max(dot(n, view), 0.0), float3(k * k))
    highlight = shade(Surface(float3(0.0), n, 0.05, 0.0, k * k), light, view, light_color)
    return background * absorb(tint, thickness) * (1.0 - f) + reflected * f + highlight


def glass_over(t: Texture, uv: float2, n: float3, light: float3, light_color: float3, reflected: float3,
               tint: float3, ior: float, thickness: float) -> float3:
    """`glass` over the texture `t` at `uv`, sampled where the pane bends the view to."""
    behind = t(uv + refraction_offset(n, ior, thickness)).rgb
    return glass(behind, n, light, light_color, reflected, tint, ior, thickness)


def frosted_glass_over(t: Texture, uv: float2, n: float3, light: float3, light_color: float3, reflected: float3,
                       tint: float3, ior: float, thickness: float, frost: float) -> float3:
    """`glass_over` through frosted glass: the texture blurred over a disk of
    radius `frost` (in uv), sixteen samples on a sunflower spiral."""
    center = uv + refraction_offset(n, ior, thickness)
    total = float3(0.0)
    for i in range(16):
        r = sqrt((float(i) + 0.5) / 16.0) * frost
        a = float(i) * 2.39996323
        total += t(center + r * float2(cos(a), sin(a))).rgb
    return glass(total / 16.0, n, light, light_color, reflected, tint, ior, thickness)


def ice(p: float2, n: float3) -> Surface:
    """Ice: clear and smooth, pale blue, with white fracture lines inside.
    Seen through as glass is: put it over its background with `glass`
    (ICE_IOR), then light the fractures with `surface.shade`."""
    c = cellular2(p, 0.0)
    crack = 1.0 - smoothstep(0.0, 0.03, c.y - c.x)
    albedo = mix(float3(0.72, 0.86, 0.95) * 0.2, float3(0.95), crack)
    return Surface(albedo, n, 0.05 + 0.5 * crack, 0.0, 0.02)
