"""Blend modes: `base` is the layer below, `top` the layer above, both RGB in 0..1.
Mix the result with `base` by an opacity to fade a layer: `mix(base, screen(base, top), 0.5)`.

Credits: the separable blend modes of the W3C "Compositing and Blending
Level 1" specification — https://www.w3.org/TR/compositing-1/#blending
"""
from pyshader import *


def multiply(base: float3, top: float3) -> float3:
    """Darkens: the product of the layers; white leaves base unchanged."""
    return base * top


def screen(base: float3, top: float3) -> float3:
    """Lightens: the inverse of multiplying the inverses; black leaves base unchanged."""
    return base + top - base * top


def overlay(base: float3, top: float3) -> float3:
    """Multiply where base is dark, screen where it is light: more contrast."""
    return hard_light(top, base)


def darken(base: float3, top: float3) -> float3:
    """The darker of the two, per channel."""
    return min(base, top)


def lighten(base: float3, top: float3) -> float3:
    """The lighter of the two, per channel."""
    return max(base, top)


def color_dodge(base: float3, top: float3) -> float3:
    """Brightens base by dividing it by the inverse of top."""
    dodge = min(float3(1.0), base / max(float3(1.0) - top, float3(1.0e-5)))
    return mix(dodge, float3(0.0), step(base, float3(0.0)))


def color_burn(base: float3, top: float3) -> float3:
    """Darkens base by dividing its inverse by top."""
    burn = float3(1.0) - min(float3(1.0), (float3(1.0) - base) / max(top, float3(1.0e-5)))
    return mix(burn, float3(1.0), step(float3(1.0), base))


def hard_light(base: float3, top: float3) -> float3:
    """Multiply where top is dark, screen where it is light: overlay with the layers swapped."""
    low = 2.0 * base * top
    high = screen(base, 2.0 * top - 1.0)
    return mix(low, high, step(float3(0.5), top))


def soft_light(base: float3, top: float3) -> float3:
    """A gentler hard_light, like shining a diffuse light on base."""
    d = mix(sqrt(base), ((16.0 * base - 12.0) * base + 4.0) * base, step(base, float3(0.25)))
    low = base - (1.0 - 2.0 * top) * base * (1.0 - base)
    high = base + (2.0 * top - 1.0) * (d - base)
    return mix(low, high, step(float3(0.5), top))


def difference(base: float3, top: float3) -> float3:
    """The absolute difference: equal colors go black."""
    return abs(base - top)


def exclusion(base: float3, top: float3) -> float3:
    """Like difference, with less contrast."""
    return base + top - 2.0 * base * top


def add(base: float3, top: float3) -> float3:
    """Linear dodge, clamped at 1."""
    return min(base + top, float3(1.0))


def subtract(base: float3, top: float3) -> float3:
    """Clamped at 0."""
    return max(base - top, float3(0.0))
