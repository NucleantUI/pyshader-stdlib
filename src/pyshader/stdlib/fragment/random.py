"""Pseudo-random values from coordinates: the same input always gives the
same output, in 0..1.

`random*` are the sine-based ones of The Book of Shaders; `hash*` are
Dave Hoskins' sine-free hashes, which hold up better at large inputs and
across GPUs. A hash's digits name its outputs then its inputs: `hash12`
takes a float2 and returns a float.

Credits:
- `random`, `random1`, `random2`: The Book of Shaders, ch. 10 "Random" and
  ch. 12 "Cellular noise", Patricio Gonzalez Vivo & Jen Lowe —
  https://thebookofshaders.com/10/
- `hash11` ... `hash33`: Dave Hoskins, "Hash without Sine" —
  https://www.shadertoy.com/view/4djSRW (MIT License, Copyright (c) 2014 David Hoskins)
"""
from pyshader import *


def random1(x: float) -> float:
    return fract(sin(x) * 43758.5453123)


def random(st: float2) -> float:
    return fract(sin(dot(st, float2(12.9898, 78.233))) * 43758.5453123)


def random2(st: float2) -> float2:
    q = float2(dot(st, float2(127.1, 311.7)), dot(st, float2(269.5, 183.3)))
    return fract(sin(q) * 43758.5453)


def hash11(p: float) -> float:
    q = fract(p * 0.1031)
    q *= q + 33.33
    q *= q + q
    return fract(q)


def hash12(p: float2) -> float:
    p3 = fract(float3(p.xyx) * 0.1031)
    p3 += dot(p3, p3.yzx + 33.33)
    return fract((p3.x + p3.y) * p3.z)


def hash13(p: float3) -> float:
    p3 = fract(p * 0.1031)
    p3 += dot(p3, p3.zyx + 31.32)
    return fract((p3.x + p3.y) * p3.z)


def hash21(p: float) -> float2:
    p3 = fract(float3(p) * float3(0.1031, 0.1030, 0.0973))
    p3 += dot(p3, p3.yzx + 33.33)
    return fract((p3.xx + p3.yz) * p3.zy)


def hash22(p: float2) -> float2:
    p3 = fract(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973))
    p3 += dot(p3, p3.yzx + 33.33)
    return fract((p3.xx + p3.yz) * p3.zy)


def hash32(p: float2) -> float3:
    p3 = fract(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973))
    p3 += dot(p3, p3.yxz + 33.33)
    return fract((p3.xxy + p3.yzz) * p3.zyx)


def hash33(p: float3) -> float3:
    p3 = fract(p * float3(0.1031, 0.1030, 0.0973))
    p3 += dot(p3, p3.yxz + 33.33)
    return fract((p3.xxy + p3.yxx) * p3.zyx)
