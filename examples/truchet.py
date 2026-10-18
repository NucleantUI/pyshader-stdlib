"""A truchet maze of quarter circles that slowly reshuffles, drawn with distance fields."""
from pyshader import *
from pyshader.stdlib.fragment.pattern import truchet
from pyshader.stdlib.fragment.sdf import sd_circle, op_union, stroke_smooth
from pyshader.stdlib.fragment.color import hsb_to_rgb


def main(uv: float2, time: float) -> float4:
    st = truchet(uv, 8.0, floor(time * 0.5))
    # Two quarter circles in opposite corners; turned tiles join them into paths.
    d = op_union(abs(sd_circle(st, 0.5)), abs(sd_circle(st - float2(1.0), 0.5)))
    line = stroke_smooth(d, 0.12, 0.02)
    ink = hsb_to_rgb(float3(fract(uv.x * 0.5 + time * 0.05), 0.6, 0.9))
    return float4(mix(float3(0.06, 0.06, 0.1), ink, line), 1.0)
