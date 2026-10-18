"""Deformations: move a position by a function of itself, for flags, water,
grass and wobbles.

Credits: the classic vertex deformations of Alan H. Barr, "Global and Local
Deformations of Solid Primitives" (SIGGRAPH 1984) — twist and bend; waves
are a sine displacement.
"""
from pyshader import *


def wave(p: float3, time: float, amplitude: float, frequency: float, speed: float) -> float3:
    """p lifted in y by a sine wave running along x."""
    return float3(p.x, p.y + amplitude * sin(p.x * frequency + time * speed), p.z)


def ripple(p: float3, center: float2, time: float, amplitude: float, frequency: float, speed: float) -> float3:
    """p lifted in y by circular waves spreading from center on the xz plane."""
    d = distance(p.xz, center)
    return float3(p.x, p.y + amplitude * sin(d * frequency - time * speed), p.z)


def twist(p: float3, amount: float) -> float3:
    """p turned around the y axis by amount radians per unit of height."""
    a = p.y * amount
    c = cos(a)
    s = sin(a)
    return float3(c * p.x + s * p.z, p.y, -s * p.x + c * p.z)


def bend(p: float3, amount: float) -> float3:
    """p bent around the z axis: the farther along x, the more it turns (amount radians per unit)."""
    a = p.x * amount
    c = cos(a)
    s = sin(a)
    return float3(c * p.x - s * p.y, s * p.x + c * p.y, p.z)


def sway(p: float2, time: float, strength: float, height: float) -> float2:
    """A 2D point pushed sideways by a sine, more the higher it is (0 at y == 0,
    full at y == height): grass and plants in the wind."""
    weight = clamp(p.y / height, 0.0, 1.0)
    return float2(p.x + sin(time) * strength * weight * weight, p.y)
