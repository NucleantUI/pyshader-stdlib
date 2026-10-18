"""Easing curves: t in 0..1 to a value that starts at 0 and ends at 1.

`_in` starts slow, `_out` ends slow, `_in_out` does both. Used to animate
between colors and positions (The Book of Shaders, ch. 6 "Colors").

Credits:
- Robert Penner's easing equations — http://robertpenner.com/easing/
- in the closed forms of Warren Moore's AHEasing —
  https://github.com/warrenm/AHEasing
"""
from pyshader import *

HALF_PI = PI * 0.5


def linear(t: float) -> float:
    return t


def sine_in(t: float) -> float:
    return 1.0 - cos(t * HALF_PI)


def sine_out(t: float) -> float:
    return sin(t * HALF_PI)


def sine_in_out(t: float) -> float:
    return 0.5 * (1.0 - cos(t * PI))


def quad_in(t: float) -> float:
    return t * t


def quad_out(t: float) -> float:
    return -t * (t - 2.0)


def quad_in_out(t: float) -> float:
    if t < 0.5:
        return 2.0 * t * t
    return -2.0 * t * t + 4.0 * t - 1.0


def cubic_in(t: float) -> float:
    return t * t * t


def cubic_out(t: float) -> float:
    f = t - 1.0
    return f * f * f + 1.0


def cubic_in_out(t: float) -> float:
    if t < 0.5:
        return 4.0 * t * t * t
    f = 2.0 * t - 2.0
    return 0.5 * f * f * f + 1.0


def quart_in(t: float) -> float:
    return t * t * t * t


def quart_out(t: float) -> float:
    f = t - 1.0
    return 1.0 - f * f * f * f


def quart_in_out(t: float) -> float:
    if t < 0.5:
        return 8.0 * t * t * t * t
    f = t - 1.0
    return 1.0 - 8.0 * f * f * f * f


def quint_in(t: float) -> float:
    return t * t * t * t * t


def quint_out(t: float) -> float:
    f = t - 1.0
    return f * f * f * f * f + 1.0


def quint_in_out(t: float) -> float:
    if t < 0.5:
        return 16.0 * t * t * t * t * t
    f = 2.0 * t - 2.0
    return 0.5 * f * f * f * f * f + 1.0


def expo_in(t: float) -> float:
    return 0.0 if t <= 0.0 else pow(2.0, 10.0 * (t - 1.0))


def expo_out(t: float) -> float:
    return 1.0 if t >= 1.0 else 1.0 - pow(2.0, -10.0 * t)


def expo_in_out(t: float) -> float:
    if t <= 0.0 or t >= 1.0:
        return t
    if t < 0.5:
        return 0.5 * pow(2.0, 20.0 * t - 10.0)
    return 1.0 - 0.5 * pow(2.0, -20.0 * t + 10.0)


def circ_in(t: float) -> float:
    return 1.0 - sqrt(1.0 - t * t)


def circ_out(t: float) -> float:
    return sqrt((2.0 - t) * t)


def circ_in_out(t: float) -> float:
    if t < 0.5:
        return 0.5 * (1.0 - sqrt(1.0 - 4.0 * t * t))
    return 0.5 * (sqrt(-(2.0 * t - 3.0) * (2.0 * t - 1.0)) + 1.0)


def back_in(t: float) -> float:
    """Pulls back below 0 before going."""
    return t * t * t - t * sin(t * PI)


def back_out(t: float) -> float:
    """Overshoots 1 before settling."""
    f = 1.0 - t
    return 1.0 - (f * f * f - f * sin(f * PI))


def back_in_out(t: float) -> float:
    if t < 0.5:
        f = 2.0 * t
        return 0.5 * (f * f * f - f * sin(f * PI))
    f = 2.0 - 2.0 * t
    return 0.5 * (1.0 - (f * f * f - f * sin(f * PI))) + 0.5


def elastic_in(t: float) -> float:
    """Winds up like a spring before going."""
    return sin(13.0 * HALF_PI * t) * pow(2.0, 10.0 * (t - 1.0))


def elastic_out(t: float) -> float:
    """Springs past 1 and wobbles to rest."""
    return sin(-13.0 * HALF_PI * (t + 1.0)) * pow(2.0, -10.0 * t) + 1.0


def elastic_in_out(t: float) -> float:
    if t < 0.5:
        return 0.5 * sin(13.0 * HALF_PI * (2.0 * t)) * pow(2.0, 10.0 * (2.0 * t - 1.0))
    return 0.5 * (sin(-13.0 * HALF_PI * (2.0 * t)) * pow(2.0, -10.0 * (2.0 * t - 1.0)) + 2.0)


def bounce_out(t: float) -> float:
    """Falls to 1 and bounces."""
    if t < 4.0 / 11.0:
        return (121.0 * t * t) / 16.0
    if t < 8.0 / 11.0:
        return (363.0 / 40.0 * t * t) - (99.0 / 10.0 * t) + 17.0 / 5.0
    if t < 9.0 / 10.0:
        return (4356.0 / 361.0 * t * t) - (35442.0 / 1805.0 * t) + 16061.0 / 1805.0
    return (54.0 / 5.0 * t * t) - (513.0 / 25.0 * t) + 268.0 / 25.0


def bounce_in(t: float) -> float:
    return 1.0 - bounce_out(1.0 - t)


def bounce_in_out(t: float) -> float:
    if t < 0.5:
        return 0.5 * bounce_in(t * 2.0)
    return 0.5 * bounce_out(t * 2.0 - 1.0) + 0.5
