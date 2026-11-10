"""Surfaces and how light meets them: a `Surface` says what a point of a
material is (its color, the way it faces, how rough and how metallic), and
`shade` lights it the way physically based renderers do, so plastic, rubber,
metal and stone stay themselves under any light. `material` makes Surfaces
for named materials; here is what they all go through.

Directions are unit vectors in the space the normal is in: for a flat shape
on screen, x right, y up and z toward the viewer, so `view` is
float3(0.0, 0.0, 1.0) and a normal comes from `light.sphere_normal` or
`light.bevel_normal`. Colors are linear (`color.srgb_to_linear`), and the sum
of lights is brighter than 1 where they are strong: tone map it.

    n = light.sphere_normal(p, 0.4)
    s = material.rubber(p * 8.0, n, float3(0.8, 0.1, 0.1))
    l = normalize(float3(cos(time), 0.6, 0.8))
    c = shade(s, l, float3(0.0, 0.0, 1.0), float3(3.0)) + shade_ambient(s, float3(0.0, 0.0, 1.0), float3(0.15), float3(0.5))
    return float4(color.linear_to_srgb(light.tonemap_aces(c)), 1.0)

Credits:
- `ggx`: Trowbridge & Reitz (1975), "Average irregularity representation of
  a rough surface for ray reflection"; Walter, Marschner, Li & Torrance,
  "Microfacet Models for Refraction through Rough Surfaces" (EGSR 2007)
- `visibility`: Smith's masking with Schlick's approximation as remapped by
  Brian Karis, "Real Shading in Unreal Engine 4" (SIGGRAPH 2013 course)
- `fresnel_schlick`, `fresnel_roughness`: Christophe Schlick, "An Inexpensive
  BRDF Model for Physically-based Rendering" (1994); the roughness term after
  Sébastien Lagarde's "Adopting a physically based shading model" (2011)
- `shade`: the Cook-Torrance microfacet model with a Lambertian diffuse, the
  metallic / roughness parameterization of Burley, "Physically Based Shading
  at Disney" (SIGGRAPH 2012)
"""
from pyshader import *


class Surface:
    """A point of a material: what `shade` lights.

    albedo     base color (linear); a metal's is the color it reflects
    normal     unit, the way the surface faces
    roughness  0 a mirror .. 1 chalk
    metallic   0 a dielectric (plastic, stone, wood) .. 1 a metal
    specular   a dielectric's reflectance head on: 0.04 most, 0.02 water, 0.08 gems
    """
    albedo: float3
    normal: float3
    roughness: float
    metallic: float
    specular: float


def ggx(n_dot_h: float, roughness: float) -> float:
    """How many microfacets face the half vector (GGX / Trowbridge-Reitz): a
    tall narrow peak for a smooth surface, low and wide for a rough one."""
    a = roughness * roughness
    a2 = a * a
    d = n_dot_h * n_dot_h * (a2 - 1.0) + 1.0
    return a2 / (PI * d * d)


def visibility(n_dot_v: float, n_dot_l: float, roughness: float) -> float:
    """How much of the light the microfacets do not shadow or hide (Smith with
    Schlick's fit), divided by the 4 n·v n·l of the microfacet model."""
    k = (roughness + 1.0) * (roughness + 1.0) / 8.0
    gv = n_dot_v / (n_dot_v * (1.0 - k) + k)
    gl = n_dot_l / (n_dot_l * (1.0 - k) + k)
    return gv * gl / max(4.0 * n_dot_v * n_dot_l, 0.0001)


def fresnel_schlick(cos_theta: float, f0: float3) -> float3:
    """The share of light reflected at an angle (Schlick): f0 head on, all of it at grazing."""
    return f0 + (1.0 - f0) * pow(1.0 - clamp(cos_theta, 0.0, 1.0), 5.0)


def fresnel_roughness(cos_theta: float, f0: float3, roughness: float) -> float3:
    """`fresnel_schlick` for light from everywhere at once: a rough surface
    brightens less toward its rim."""
    return f0 + (max(float3(1.0 - roughness), f0) - f0) * pow(1.0 - clamp(cos_theta, 0.0, 1.0), 5.0)


def reflectance(s: Surface) -> float3:
    """The surface's reflectance head on (f0): `specular` for a dielectric, the
    albedo for a metal, between them as metallic goes."""
    return mix(float3(s.specular), s.albedo, s.metallic)


def shade(s: Surface, light: float3, view: float3, light_color: float3) -> float3:
    """The light a surface sends toward `view` (unit, toward the viewer) from a
    light in the direction `light` (unit, toward the light) of `light_color`
    (its brightness): a diffuse share and a highlight, together never more than
    the light brings."""
    n = s.normal
    n_dot_l = max(dot(n, light), 0.0)
    n_dot_v = max(dot(n, view), 0.0001)
    # Light straight from behind the viewer's direction has no half vector: no NaN.
    half = light + view
    h = half / max(length(half), 0.0001)
    n_dot_h = max(dot(n, h), 0.0)
    roughness = clamp(s.roughness, 0.04, 1.0)
    f0 = reflectance(s)
    f = fresnel_schlick(dot(h, view), f0)
    highlight = f * (ggx(n_dot_h, roughness) * visibility(n_dot_v, n_dot_l, roughness))
    # Only what is not reflected on the way in gets into the surface to scatter.
    diffuse = (1.0 - fresnel_schlick(n_dot_l, f0)) * (1.0 - s.metallic) * s.albedo / PI
    return (diffuse + highlight) * light_color * n_dot_l


def shade_ambient(s: Surface, view: float3, ambient: float3, reflected: float3) -> float3:
    """The surface in the light of its surroundings: `ambient`, the light
    from all around that its diffuse share scatters (what keeps the shadowed
    side from going black), and `reflected`, what it mirrors, the
    surroundings in the direction `reflect(-view, s.normal)` (a sky, a room,
    a horizon). A metal shows almost nothing else: give it something to
    reflect. A rough surface reflects a blur of it, dimmer."""
    f = fresnel_roughness(max(dot(s.normal, view), 0.0), reflectance(s), s.roughness)
    diffuse = (1.0 - f) * (1.0 - s.metallic) * s.albedo * ambient
    return diffuse + f * mix(reflected, ambient, s.roughness)


def bump(n: float3, slope: float2, strength: float) -> float3:
    """A normal tilted by a height field's slope (its change along x and y),
    as bumps and grooves tilt it; `strength` how deep they are. For a surface
    facing the viewer, as the 2D normals are."""
    return normalize(n - float3(slope * strength, 0.0))


def with_normal(s: Surface, n: float3) -> Surface:
    """The surface facing `n` instead."""
    return Surface(s.albedo, n, s.roughness, s.metallic, s.specular)


def blend(a: Surface, b: Surface, t: float) -> Surface:
    """A surface `t` of the way from a to b: rust over metal, wet over dry,
    moss over stone. The normal follows, renormalized."""
    return Surface(
        mix(a.albedo, b.albedo, t),
        normalize(mix(a.normal, b.normal, t)),
        mix(a.roughness, b.roughness, t),
        mix(a.metallic, b.metallic, t),
        mix(a.specular, b.specular, t),
    )
