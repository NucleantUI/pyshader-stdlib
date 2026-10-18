"""2D matrices: rotate and scale coordinates.

    st = rotate_around(st, time, float2(0.5))
    st = rotate2d(angle) * st

Credits: The Book of Shaders, ch. 8 "2D Matrices", Patricio Gonzalez Vivo &
Jen Lowe — https://thebookofshaders.com/08/
"""
from pyshader import *


def rotate2d(angle: float) -> float2x2:
    """Turns a point counter-clockwise by angle (radians) around the origin."""
    c = cos(angle)
    s = sin(angle)
    return float2x2(float2(c, s), float2(-s, c))


def scale2d(s: float2) -> float2x2:
    return float2x2(float2(s.x, 0.0), float2(0.0, s.y))


def shear2d(k: float2) -> float2x2:
    """x moves by k.x · y, y by k.y · x."""
    return float2x2(float2(1.0, k.y), float2(k.x, 1.0))


def rotate_around(st: float2, angle: float, center: float2) -> float2:
    """st turned counter-clockwise by angle around center."""
    return rotate2d(angle) * (st - center) + center


def scale_around(st: float2, s: float2, center: float2) -> float2:
    """The coordinates scaled by s around center. A shape drawn in them shrinks as s grows."""
    return scale2d(s) * (st - center) + center
