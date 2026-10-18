"""Noise: smooth randomness, for clouds, terrain, fire and organic motion.

    n = simplex_noise(uv * 4.0)                       # -1..1
    n = simplex_noise3(float3(uv * 4.0, time * 0.2))  # animated
    n = fbm(uv * 3.0, 5)                              # layered detail, 0..1

Credits:
- `value_noise1`, `value_noise`, `gradient_noise`: The Book of Shaders,
  ch. 11 "Noise", Patricio Gonzalez Vivo & Jen Lowe —
  https://thebookofshaders.com/11/ ; gradient noise after Inigo Quilez,
  https://www.shadertoy.com/view/XdXGW8 (MIT)
- `simplex_noise`, `simplex_noise3`: Ian McEwan, Ashima Arts, and Stefan
  Gustavson, "webgl-noise" — https://github.com/ashima/webgl-noise
  (MIT License, Copyright (C) 2011 Ashima Arts, Copyright (C) 2011-2016
  Stefan Gustavson); simplex noise by Ken Perlin
- `fbm`, `turbulence`, `ridge`: The Book of Shaders, ch. 13 "Fractal
  Brownian Motion" — https://thebookofshaders.com/13/
"""
from pyshader import *
from .random import random, random1, random2

_mod289 = lambda x: x - floor(x * (1.0 / 289.0)) * 289.0
_permute = lambda x: _mod289(((x * 34.0) + 1.0) * x)
_taylor_inv_sqrt = lambda r: 1.79284291400159 - 0.85373472095314 * r


def value_noise1(x: float) -> float:
    """1D value noise in 0..1."""
    i = floor(x)
    f = fract(x)
    u = f * f * (3.0 - 2.0 * f)
    return mix(random1(i), random1(i + 1.0), u)


def value_noise(st: float2) -> float:
    """2D value noise in 0..1: random values on a grid, blended smoothly."""
    i = floor(st)
    f = fract(st)
    a = random(i)
    b = random(i + float2(1.0, 0.0))
    c = random(i + float2(0.0, 1.0))
    d = random(i + float2(1.0, 1.0))
    u = f * f * (3.0 - 2.0 * f)
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y


def gradient_noise(st: float2) -> float:
    """2D gradient noise in about -1..1: random directions on a grid, blended smoothly."""
    i = floor(st)
    f = fract(st)
    u = f * f * (3.0 - 2.0 * f)
    a = dot(random2(i) * 2.0 - 1.0, f)
    b = dot(random2(i + float2(1.0, 0.0)) * 2.0 - 1.0, f - float2(1.0, 0.0))
    c = dot(random2(i + float2(0.0, 1.0)) * 2.0 - 1.0, f - float2(0.0, 1.0))
    d = dot(random2(i + float2(1.0, 1.0)) * 2.0 - 1.0, f - float2(1.0, 1.0))
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y)


def simplex_noise(v: float2) -> float:
    """2D simplex noise in -1..1."""
    C = float4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439)
    i = floor(v + dot(v, C.yy))
    x0 = v - i + dot(i, C.xx)
    i1 = float2(1.0, 0.0) if x0.x > x0.y else float2(0.0, 1.0)
    x12 = x0.xyxy + C.xxzz
    x12.xy -= i1
    i = _mod289(i)
    p = _permute(_permute(i.y + float3(0.0, i1.y, 1.0)) + i.x + float3(0.0, i1.x, 1.0))
    m = max(0.5 - float3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), float3(0.0))
    m = m * m
    m = m * m
    x = 2.0 * fract(p * C.www) - 1.0
    h = abs(x) - 0.5
    ox = floor(x + 0.5)
    a0 = x - ox
    m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h)
    g = float3(a0.x * x0.x + h.x * x0.y, a0.yz * x12.xz + h.yz * x12.yw)
    return 130.0 * dot(m, g)


def simplex_noise3(v: float3) -> float:
    """3D simplex noise in -1..1; a 2D point plus time animates it smoothly."""
    C = float2(1.0 / 6.0, 1.0 / 3.0)
    D = float4(0.0, 0.5, 1.0, 2.0)
    i = floor(v + dot(v, C.yyy))
    x0 = v - i + dot(i, C.xxx)
    g = step(x0.yzx, x0.xyz)
    l = 1.0 - g
    i1 = min(g.xyz, l.zxy)
    i2 = max(g.xyz, l.zxy)
    x1 = x0 - i1 + C.xxx
    x2 = x0 - i2 + C.yyy
    x3 = x0 - D.yyy
    i = _mod289(i)
    p = _permute(_permute(_permute(
        i.z + float4(0.0, i1.z, i2.z, 1.0))
        + i.y + float4(0.0, i1.y, i2.y, 1.0))
        + i.x + float4(0.0, i1.x, i2.x, 1.0))
    n_ = 0.142857142857
    ns = n_ * D.wyz - D.xzx
    j = p - 49.0 * floor(p * ns.z * ns.z)
    x_ = floor(j * ns.z)
    y_ = floor(j - 7.0 * x_)
    x = x_ * ns.x + ns.yyyy
    y = y_ * ns.x + ns.yyyy
    h = 1.0 - abs(x) - abs(y)
    b0 = float4(x.xy, y.xy)
    b1 = float4(x.zw, y.zw)
    s0 = floor(b0) * 2.0 + 1.0
    s1 = floor(b1) * 2.0 + 1.0
    sh = -step(h, float4(0.0))
    a0 = b0.xzyw + s0.xzyw * sh.xxyy
    a1 = b1.xzyw + s1.xzyw * sh.zzww
    p0 = float3(a0.xy, h.x)
    p1 = float3(a0.zw, h.y)
    p2 = float3(a1.xy, h.z)
    p3 = float3(a1.zw, h.w)
    norm = _taylor_inv_sqrt(float4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)))
    p0 *= norm.x
    p1 *= norm.y
    p2 *= norm.z
    p3 *= norm.w
    m = max(0.6 - float4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), float4(0.0))
    m = m * m
    return 42.0 * dot(m * m, float4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)))


def fbm(st: float2, octaves: int) -> float:
    """Fractal Brownian motion: octaves of value noise, each twice as fine and half as strong. About 0..1."""
    value = 0.0
    amplitude = 0.5
    p = st
    for _ in range(octaves):
        value += amplitude * value_noise(p)
        p *= 2.0
        amplitude *= 0.5
    return value


def turbulence(st: float2, octaves: int) -> float:
    """fBm of the absolute value of simplex noise: billowing, with sharp creases. About 0..1."""
    value = 0.0
    amplitude = 0.5
    p = st
    for _ in range(octaves):
        value += amplitude * abs(simplex_noise(p))
        p *= 2.0
        amplitude *= 0.5
    return value


def ridge(st: float2, octaves: int) -> float:
    """Ridged multifractal: turbulence turned over, sharp crests like mountain ridges. About 0..1."""
    value = 0.0
    amplitude = 0.5
    weight = 1.0
    p = st
    for _ in range(octaves):
        n = 1.0 - abs(simplex_noise(p))
        n = n * n * weight
        weight = n
        value += n * amplitude
        p *= 2.0
        amplitude *= 0.5
    return value
