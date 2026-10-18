"""Moving Voronoi cells with glowing borders, each cell its own color."""
from pyshader import *
import pyshader.stdlib.fragment.cellular as cellular
import pyshader.stdlib.fragment.random as random


def main(uv: float2, time: float) -> float4:
    st = uv * 6.0
    v = cellular.voronoi(st, time)
    cell = floor(st + v.yz)
    tint = 0.4 + 0.5 * random.hash32(cell)
    border = 1.0 - smoothstep(0.0, 0.06, v.x)
    return float4(mix(tint * (0.6 + 0.4 * length(v.yz)), float3(1.0), border), 1.0)
