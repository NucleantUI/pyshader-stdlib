"""Drifting clouds at sunset: fBm noise, a cosine palette and an easing curve."""
from pyshader import *
from pyshader.stdlib.fragment.noise import fbm, simplex_noise3
from pyshader.stdlib.fragment.color import palette
from pyshader.stdlib.fragment.coords import centered
from pyshader.stdlib.fragment import easing


def main(uv: float2, time: float, resolution: float2) -> float4:
    p = centered(uv, resolution) * 2.0
    warp = simplex_noise3(float3(p * 0.5, time * 0.05))
    density = fbm(p + float2(time * 0.1, 0.0) + warp, 6)
    cover = easing.cubic_in_out(clamp((density - 0.3) * 2.0, 0.0, 1.0))
    sky = palette(uv.y * 0.6 + 0.2, float3(0.5), float3(0.5), float3(1.0), float3(0.0, 0.1, 0.2))
    return float4(mix(sky, float3(1.0, 0.95, 0.9), cover), 1.0)
