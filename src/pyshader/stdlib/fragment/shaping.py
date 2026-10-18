"""Shaping functions: curves that take a value in 0..1 and bend it.

Credits:
- `plot`: The Book of Shaders, ch. 5 "Algorithmic drawing",
  Patricio Gonzalez Vivo & Jen Lowe — https://thebookofshaders.com/05/
- `almost_identity` ... `sinc`: Inigo Quilez, "Useful little functions" —
  https://iquilezles.org/articles/functions/
- `blinn_wyvill_cosine` ... `quadratic_bezier`: Golan Levin's shaping
  function collection — https://www.flong.com/archive/texts/code/shapers_poly/
  and https://www.flong.com/archive/texts/code/shapers_exp/ ,
  https://www.flong.com/archive/texts/code/shapers_circ/ ,
  https://www.flong.com/archive/texts/code/shapers_bez/
"""
from pyshader import *

EPSILON = 0.00001


def plot(st: float2, pct: float) -> float:
    """1.0 on a thin line where st.y == pct, fading off either side: draws y = f(x)."""
    return smoothstep(pct - 0.02, pct, st.y) - smoothstep(pct, pct + 0.02, st.y)


# Inigo Quilez


def almost_identity(x: float, m: float, n: float) -> float:
    """x above the threshold m; below it, a smooth floor at n instead of reaching 0."""
    if x > m:
        return x
    a = 2.0 * n - m
    b = 2.0 * m - 3.0 * n
    t = x / m
    return (a * t + b) * t * t + n


def almost_unit_identity(x: float) -> float:
    """Identity-like on 0..1, with zero derivative at 0 and slope 1 at 1."""
    return x * x * (2.0 - x)


def exp_impulse(x: float, k: float) -> float:
    """Grows fast, falls slowly; peaks at 1.0 when x == 1/k."""
    h = k * x
    return h * exp(1.0 - h)


def quad_impulse(x: float, k: float) -> float:
    """Like exp_impulse, falling off as 1/x²; peaks at 1.0 when x == sqrt(1/k)."""
    return 2.0 * sqrt(k) * x / (1.0 + k * x * x)


def poly_impulse(x: float, k: float, n: float) -> float:
    """Impulse falling off as 1/x^n; peaks at 1.0 when x == (k(n-1))^(-1/n)."""
    return (n / (n - 1.0)) * pow((n - 1.0) * k, 1.0 / n) * x / (1.0 + k * pow(x, n))


def cubic_pulse(c: float, w: float, x: float) -> float:
    """A smooth bump of half-width w centered on c; a smoothstep-based gaussian stand-in."""
    x = abs(x - c)
    if x > w:
        return 0.0
    x /= w
    return 1.0 - x * x * (3.0 - 2.0 * x)


def exp_step(x: float, k: float, n: float) -> float:
    """A step that gets sharper as n grows."""
    return exp(-k * pow(x, n))


def gain(x: float, k: float) -> float:
    """Expands the sides of 0..1 and compresses the center (k > 1), or the reverse (k < 1)."""
    a = 0.5 * pow(2.0 * (x if x < 0.5 else 1.0 - x), k)
    return a if x < 0.5 else 1.0 - a


def parabola(x: float, k: float) -> float:
    """0 at both ends of 0..1 and 1 in the middle; k shapes it."""
    return pow(4.0 * x * (1.0 - x), k)


def pcurve(x: float, a: float, b: float) -> float:
    """Like parabola, with the peak skewed: a and b shape each side."""
    k = pow(a + b, a + b) / (pow(a, a) * pow(b, b))
    return k * pow(x, a) * pow(1.0 - x, b)


def sinc(x: float, k: float) -> float:
    """A phase-shifted sinc: a bounce that settles; k sets how many."""
    a = PI * (k * x - 1.0)
    return sin(a) / a


# Golan Levin


def blinn_wyvill_cosine(x: float) -> float:
    """Polynomial approximation of a raised inverted cosine, 0..1 to 0..1."""
    x2 = x * x
    x4 = x2 * x2
    x6 = x4 * x2
    return (4.0 / 9.0) * x6 - (17.0 / 9.0) * x4 + (22.0 / 9.0) * x2


def double_cubic_seat(x: float, a: float, b: float) -> float:
    """Two cubics meeting in a flat seat at (a, b)."""
    a = clamp(a, EPSILON, 1.0 - EPSILON)
    b = clamp(b, 0.0, 1.0)
    if x <= a:
        return b - b * pow(1.0 - x / a, 3.0)
    return b + (1.0 - b) * pow((x - a) / (1.0 - a), 3.0)


def double_cubic_seat_linear_blend(x: float, a: float, b: float) -> float:
    """A cubic seat blended with the identity: a is the seat's x, b how much of the seat."""
    a = clamp(a, EPSILON, 1.0 - EPSILON)
    b = 1.0 - clamp(b, 0.0, 1.0)
    if x <= a:
        return b * x + (1.0 - b) * a * (1.0 - pow(1.0 - x / a, 3.0))
    return b * x + (1.0 - b) * (a + (1.0 - a) * pow((x - a) / (1.0 - a), 3.0))


def double_exponential_seat(x: float, a: float) -> float:
    """A seat at the center made of two exponentials; a sets its flatness."""
    a = clamp(a, EPSILON, 1.0 - EPSILON)
    if x <= 0.5:
        return pow(2.0 * x, 1.0 - a) / 2.0
    return 1.0 - pow(2.0 * (1.0 - x), 1.0 - a) / 2.0


def double_exponential_sigmoid(x: float, a: float) -> float:
    """An S-curve made of two exponentials; a sets its steepness."""
    a = 1.0 - clamp(a, EPSILON, 1.0 - EPSILON)
    if x <= 0.5:
        return pow(2.0 * x, 1.0 / a) / 2.0
    return 1.0 - pow(2.0 * (1.0 - x), 1.0 / a) / 2.0


def logistic_sigmoid(x: float, a: float) -> float:
    """The logistic S-curve, normalized to pass through (0, 0) and (1, 1)."""
    a = clamp(a, EPSILON, 1.0 - EPSILON)
    a = 1.0 / (1.0 - a) - 1.0
    A = 1.0 / (1.0 + exp(-(x - 0.5) * a * 2.0))
    B = 1.0 / (1.0 + exp(a))
    C = 1.0 / (1.0 + exp(-a))
    return (A - B) / (C - B)


def circular_ease_in(x: float) -> float:
    """A quarter circle, flat at 0."""
    return 1.0 - sqrt(1.0 - x * x)


def circular_ease_out(x: float) -> float:
    """A quarter circle, flat at 1."""
    return sqrt(1.0 - (1.0 - x) * (1.0 - x))


def double_circle_seat(x: float, a: float) -> float:
    """Two quarter circles meeting in a seat at x == a."""
    a = clamp(a, 0.0, 1.0)
    if x <= a:
        return sqrt(a * a - (x - a) * (x - a))
    return 1.0 - sqrt((1.0 - a) * (1.0 - a) - (x - a) * (x - a))


def double_circle_sigmoid(x: float, a: float) -> float:
    """Two quarter circles making an S-curve, joined at x == a."""
    a = clamp(a, 0.0, 1.0)
    if x <= a:
        return a - sqrt(a * a - x * x)
    return a + sqrt((1.0 - a) * (1.0 - a) - (x - 1.0) * (x - 1.0))


def quadratic_bezier(x: float, a: float, b: float) -> float:
    """y of the quadratic Bézier from (0, 0) to (1, 1) with its control point at (a, b)."""
    a = clamp(a, 0.0, 1.0)
    b = clamp(b, 0.0, 1.0)
    if a == 0.5:
        a += EPSILON
    om2a = 1.0 - 2.0 * a
    t = (sqrt(a * a + om2a * x) - a) / om2a
    return (1.0 - 2.0 * b) * t * t + 2.0 * b * t
