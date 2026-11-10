"""PyShader's builtins on the CPU, enough to run the library's functions in
plain Python and check their numbers.

The `pyshader` package installed with the stubs only describes the API for
editors; `load(module)` runs a library module against these implementations
instead, with GLSL's rules: a negative square root or `acos` past ±1 gives NaN
(the tests look for it), `mod` takes the sign of its divisor.
"""

from __future__ import annotations

import builtins
import dataclasses
import importlib.util
import math
import sys
import types
from pathlib import Path

SOURCES = Path(__file__).resolve().parent.parent / "src"
_SWIZZLE = {c: i for i, c in enumerate("xyzw")} | {c: i for i, c in enumerate("rgba")}

PI = math.pi
nan = float("nan")


class Vec:
    """float2 / float3 / float4: a value, copied on every operation."""

    __slots__ = ("c",)

    def __init__(self, *parts, n: int):
        c: list[float] = []
        for part in parts:
            c.extend(part.c if isinstance(part, Vec) else [float(part)])
        if len(c) == 1:
            c *= n
        if len(c) != n:
            raise TypeError(f"float{n} from {len(c)} components")
        object.__setattr__(self, "c", c)

    @classmethod
    def of(cls, c) -> Vec:
        return cls(*c, n=len(c))

    def __getattr__(self, name: str):
        try:
            picked = [self.c[_SWIZZLE[ch]] for ch in name]
        except (KeyError, IndexError):
            raise AttributeError(name) from None
        return picked[0] if len(picked) == 1 else Vec.of(picked)

    def __setattr__(self, name: str, value) -> None:
        values = value.c if isinstance(value, Vec) else [float(value)]
        for ch, v in zip(name, values, strict=True):
            self.c[_SWIZZLE[ch]] = float(v)

    def __len__(self) -> int:
        return len(self.c)

    def __iter__(self):
        return iter(self.c)

    def __repr__(self) -> str:
        return f"float{len(self.c)}({', '.join(f'{v:.6g}' for v in self.c)})"

    def _zip(self, other, op):
        if isinstance(other, Vec):
            return Vec.of([op(a, b) for a, b in zip(self.c, other.c, strict=True)])
        return Vec.of([op(a, other) for a in self.c])

    def __add__(self, o): return self._zip(o, lambda a, b: a + b)
    def __radd__(self, o): return self._zip(o, lambda a, b: b + a)
    def __sub__(self, o): return self._zip(o, lambda a, b: a - b)
    def __rsub__(self, o): return self._zip(o, lambda a, b: b - a)
    def __mul__(self, o): return self._zip(o, lambda a, b: a * b)
    def __rmul__(self, o): return self._zip(o, lambda a, b: b * a)
    def __truediv__(self, o): return self._zip(o, _div)
    def __rtruediv__(self, o): return self._zip(o, lambda a, b: _div(b, a))
    def __neg__(self): return Vec.of([-a for a in self.c])


def _div(a: float, b: float) -> float:
    if b == 0.0:
        return nan if a == 0.0 else math.copysign(math.inf, a) * math.copysign(1.0, b)
    return a / b


class Mat2:
    """float2x2 from its two columns; times a float2 is the column combination."""

    __slots__ = ("columns",)

    def __init__(self, a: Vec, b: Vec):
        self.columns = (a, b)

    def __mul__(self, v: Vec) -> Vec:
        a, b = self.columns
        return Vec.of([a.c[0] * v.c[0] + b.c[0] * v.c[1], a.c[1] * v.c[0] + b.c[1] * v.c[1]])


def float2x2(a: Vec, b: Vec) -> Mat2: return Mat2(a, b)
def float2(*parts) -> Vec: return Vec(*parts, n=2)
def float3(*parts) -> Vec: return Vec(*parts, n=3)
def float4(*parts) -> Vec: return Vec(*parts, n=4)
def bool3(*parts) -> tuple[bool, ...]: return tuple(bool(p) for p in parts)


def _each(f):
    """f over a scalar, or over each component (vectors in any argument, scalars broadcast)."""
    def apply(*args):
        size = next((len(a) for a in args if isinstance(a, Vec)), None)
        if size is None:
            return f(*(float(a) for a in args))
        cols = [a.c if isinstance(a, Vec) else [float(a)] * size for a in args]
        return Vec.of([f(*row) for row in zip(*cols)])
    apply.__name__ = f.__name__
    return apply


def _sqrt(x): return math.sqrt(x) if x >= 0.0 else nan
def _acos(x): return math.acos(x) if -1.0 <= x <= 1.0 else nan
def _asin(x): return math.asin(x) if -1.0 <= x <= 1.0 else nan
def _pow(x, y):
    if x < 0.0:
        return nan
    if x == 0.0:
        return 0.0 if y > 0.0 else (1.0 if y == 0.0 else math.inf)
    return math.pow(x, y)
def _sign(x): return 1.0 if x > 0.0 else (-1.0 if x < 0.0 else 0.0)
def _mod(x, y): return x - y * math.floor(_div(x, y)) if y != 0.0 else nan
def _clamp(x, lo, hi): return builtins.min(builtins.max(x, lo), hi)
def _step(edge, x): return 0.0 if x < edge else 1.0
def _smoothstep(e0, e1, x):
    t = _clamp((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


sqrt = _each(_sqrt)
acos = _each(_acos)
asin = _each(_asin)
pow = _each(_pow)
sign = _each(_sign)
mod = _each(_mod)
clamp = _each(_clamp)
step = _each(_step)
smoothstep = _each(_smoothstep)
abs = _each(builtins.abs)
floor = _each(math.floor)
ceil = _each(math.ceil)
fract = _each(lambda x: x - math.floor(x))
sin = _each(math.sin)
cos = _each(math.cos)
tan = _each(math.tan)
exp = _each(math.exp)
log = _each(lambda x: math.log(x) if x > 0.0 else (-math.inf if x == 0.0 else nan))
atan2 = _each(math.atan2)
mix = _each(lambda a, b, t: a + (b - a) * t)
round = _each(lambda x: math.floor(x + 0.5))
min = _each(builtins.min)
max = _each(builtins.max)


def atan(y, x=None):
    return _each(math.atan)(y) if x is None else atan2(y, x)


def dot(a: Vec, b: Vec) -> float:
    return math.fsum(x * y for x, y in zip(a.c, b.c, strict=True))


def length(v) -> float:
    return math.sqrt(dot(v, v)) if isinstance(v, Vec) else builtins.abs(float(v))


def distance(a, b) -> float:
    return length(a - b)


def normalize(v: Vec) -> Vec:
    return v / length(v)


def reflect(i: Vec, n: Vec) -> Vec:
    """GLSL's reflect: i mirrored about the surface facing n."""
    return i - n * (2.0 * dot(n, i))


def refract(i: Vec, n: Vec, eta: float) -> Vec:
    """GLSL's refract: i bent through a surface facing n, eta = n1 / n2; zero past total internal reflection."""
    d = dot(n, i)
    k = 1.0 - eta * eta * (1.0 - d * d)
    if k < 0.0:
        return Vec.of([0.0] * len(i))
    return i * eta - n * (eta * d + math.sqrt(k))


def Texture(f):
    """A texture on the CPU: any callable from a float2 to a float4."""
    return f


NAMES = {name: value for name, value in globals().items()
         if not name.startswith("_") and name not in {"annotations", "builtins", "importlib", "math", "sys",
                                                      "types", "Path", "SOURCES", "Vec", "Mat2", "NAMES", "load",
                                                      "nan", "dataclasses"}}


def _structs(module: types.ModuleType) -> None:
    """The module's classes as PyShader has them: plain structs, built positionally or by keyword."""
    for value in list(vars(module).values()):
        if isinstance(value, type) and value.__module__ == module.__name__ and "__dataclass_fields__" not in vars(value):
            dataclasses.dataclass(value)


def load(module: str) -> types.ModuleType:
    """A library module (`pyshader.stdlib.fragment.sdf`) run on these builtins,
    with the library modules it imports (`from .random import ...`) run the same way."""
    shim = types.ModuleType("pyshader")
    shim.__dict__.update(NAMES)
    setattr(shim, "__all__", list(NAMES))
    setattr(shim, "__path__", [str(SOURCES / "pyshader")])
    saved = {name: m for name, m in sys.modules.items() if name == "pyshader" or name.startswith("pyshader.")}
    for name in saved:
        del sys.modules[name]
    sys.modules["pyshader"] = shim
    try:
        loaded = importlib.import_module(module)
        for name, m in list(sys.modules.items()):
            if name.startswith("pyshader.stdlib"):
                _structs(m)
        return loaded
    finally:
        for name in [n for n in sys.modules if n == "pyshader" or n.startswith("pyshader.")]:
            del sys.modules[name]
        sys.modules.update(saved)
