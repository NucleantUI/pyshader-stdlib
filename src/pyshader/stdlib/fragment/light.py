"""Light, glow and shadow in 2D: how bright a pixel is near a light or a
glowing shape, LEDs and neon, shading that makes a flat shape look round, and
soft shadows.

Most functions take a distance: from a light's center, or to a shape's edge
from `sdf` (negative inside). That makes every shape in `sdf` a light: a
glowing ring is `glow_edge(sdf.sd_circle(p, 0.3), 0.05)`, a neon heart
`neon(sdf.sd_heart(p), ...)`. Brightness adds up past 1 where lights overlap;
a `tonemap_*` brings the sum back to 0..1.

    d = sdf.sd_circle(p, 0.3)
    color = neon(d, float3(0.2, 0.6, 1.0), 0.01, 0.04)
    return float4(tonemap_exposure(color, 1.0), 1.0)

Credits:
- `falloff_range`, `occlusion`, and lights casting soft shadows past shapes:
  the 2D distance-field lighting of "2D signed distance" on Shadertoy
  (https://www.shadertoy.com/view/4dfXDn)
- `drop_shadow`: after "Drop shadow of round rect"
  (https://www.shadertoy.com/view/NtVSW1), with a Gaussian's edge (erf) in
  place of its sigmoid
- `segment_light`: a line of inverse-square point lights, added up in closed
  form, the idea of Tim Gott's "Neon" (https://timgott.github.io/neon)
- `box_shadow`, `erf`: Evan Wallace, "Fast Rounded Rectangle Shadows" (CC0) —
  https://madebyevan.com/shaders/fast-rounded-rectangle-shadows/
- `soft_shadow_step`: Inigo Quilez, "soft shadows in raymarched SDFs" —
  https://iquilezles.org/articles/rmshadows/
- `breathe`: Sean Voisen's exp(sin) curve, "Re-creating the 'breathing' LED" (2011)
- `tonemap_exposure`: as in "Coffee & Tablet" (https://www.shadertoy.com/view/lssGzn);
  `tonemap_aces`: Krzysztof Narkowicz's fit of the ACES curve —
  https://knarkowicz.wordpress.com/2016/01/06/aces-filmic-tone-mapping-curve/
- `sphere_normal` and the shading with it: the lit ball of "Rotating Sphere"
  (https://www.shadertoy.com/view/4sj3zy); Blinn-Phong; Schlick's Fresnel
"""
from pyshader import *
from .random import hash11


# Falloff: brightness by distance, 1 at distance 0.


def falloff_inverse_square(d: float, radius: float) -> float:
    """Light's own falloff, softened: radius² / (radius² + d²). Half as bright
    at d = radius, then like 1/d²: a long, soft tail."""
    q = max(d, 0.0)
    return radius * radius / (radius * radius + q * q)


def falloff_exp(d: float, radius: float) -> float:
    """exp(-d / radius): a shorter tail than inverse square, easy to tune."""
    return exp(-max(d, 0.0) / radius)


def falloff_gaussian(d: float, radius: float) -> float:
    """A Gaussian bump, radius its standard deviation: soft, no tail, like bloom."""
    return exp(-d * d / (2.0 * radius * radius))


def falloff_range(d: float, reach: float) -> float:
    """(1 - d / reach)²: dark from `reach` on, so lights stay local."""
    t = 1.0 - clamp(d / reach, 0.0, 1.0)
    return t * t


# Glow of any shape, from its distance (sdf): 1 at the edge.


def glow(d: float, radius: float) -> float:
    """The shape lit from inside: 1 on and in the shape, a halo of `radius` outside."""
    return falloff_inverse_square(d, radius)


def glow_inner(d: float, radius: float) -> float:
    """Light along the inside of the edge, fading toward the middle; 0 outside."""
    return exp(d / radius) * step(d, 0.0)


def glow_edge(d: float, radius: float) -> float:
    """The edge itself glowing, to both sides: an outline made of light."""
    return falloff_inverse_square(abs(d), radius)


def neon(d: float, color: float3, width: float, radius: float) -> float3:
    """A neon tube `width` thick along the shape's edge: a white-hot core in a
    halo of `color` reaching `radius`. Brighter than 1 at the core: tonemap it."""
    t = max(abs(d) - width * 0.5, 0.0)
    core = 1.0 - smoothstep(0.0, width * 0.5, abs(d))
    return color * falloff_inverse_square(t, radius) + float3(core)


def segment_light(p: float2, a: float2, b: float2, radius: float) -> float:
    """A tube of light from a to b: every point on it an inverse-square light,
    added up exactly. 1 on the axis of a long tube; far off, a point light as
    bright as the tube is long. `radius` softens it like falloff_inverse_square."""
    e = b - a
    l = length(e)
    t = e / l
    w = p - a
    s = dot(w, t)                                   # along the tube, from a
    h = w.x * t.y - w.y * t.x                       # across it
    hh = sqrt(h * h + radius * radius)
    return radius / PI * (atan2(l - s, hh) + atan2(s, hh)) / hh


# LEDs


def led(p: float2, color: float3, radius: float, glow_radius: float) -> float3:
    """An LED at the origin: a white-hot spot of `radius` in a halo of `color`.
    Brighter than 1 in the middle: tonemap it."""
    d = length(p)
    core = 1.0 - smoothstep(0.0, radius, d)
    return color * falloff_inverse_square(d - radius, glow_radius) + float3(core * core)


def led_ring_index(p: float2, count: float) -> float:
    """Which of `count` LEDs on a ring around the origin is nearest p: 0 on +x,
    counting counterclockwise. Draw it and its two neighbours, so halos overlap:

        i0 = led_ring_index(p, 12.0)
        for k in range(3):
            i = mod(i0 + float(k) - 1.0, 12.0)
            color += led(p - led_ring_position(i, 12.0, 0.4), ...)
    """
    a = atan2(p.y, p.x)
    return mod(floor(a * count / (2.0 * PI) + 0.5), count)


def led_ring_position(index: float, count: float, radius: float) -> float2:
    """Where LED `index` of `count` sits on a ring of `radius` around the origin."""
    a = 2.0 * PI * index / count
    return radius * float2(cos(a), sin(a))


def chase(index: float, count: float, head: float, tail: float) -> float:
    """A running light around `count` LEDs: how bright LED `index` is when the
    head is at `head` (in LEDs: count it up with time), fading over `tail` LEDs
    behind it. The next LED fades in as the head moves on to it."""
    behind = mod(head - index, count)
    lit = max(1.0 - behind / tail, 0.0)
    coming = clamp(behind - (count - 1.0), 0.0, 1.0)
    return max(lit * lit, coming)


def breathe(time: float, period: float) -> float:
    """0..1, slow to light and quick to fade, like a sleeping laptop's LED; one
    breath every `period` seconds."""
    e = exp(1.0)
    return (exp(sin(2.0 * PI * time / period - 0.5 * PI)) - 1.0 / e) / (e - 1.0 / e)


def flicker(time: float, seed: float, amount: float) -> float:
    """About 1, with the restless dips of an old neon sign: `amount` (0..1) sets
    how deep. A different `seed` per light keeps them out of step."""
    n = hash11(floor(time * 18.0) + seed * 37.0)
    dip = step(0.9, n)
    return 1.0 - amount * (0.8 * dip + 0.2 * n)


# Shading: a flat shape lit as if it were round.


def sphere_normal(p: float2, radius: float) -> float3:
    """The surface direction of a ball of `radius` at the origin, seen from the
    front (z toward the viewer); on its rim and outside, sideways."""
    q = p / radius
    return float3(q, sqrt(max(1.0 - dot(q, q), 0.0))) / max(length(q), 1.0)


def bevel_normal(d: float, gradient: float2, width: float) -> float3:
    """The surface direction of a shape whose edge is rounded over `width`, from
    its distance d and the direction d grows in (`gradient`: normalize(p) for a
    circle, else from two more samples of d); flat inside the bevel."""
    x = clamp(-d / width, 0.0, 1.0)
    y = sqrt(max(1.0 - (1.0 - x) * (1.0 - x), 0.0001))
    return normalize(float3(gradient * (1.0 - x) / y, 1.0))


def lambert(n: float3, light: float3) -> float:
    """Diffuse light on a surface facing n from the direction `light` (unit)."""
    return max(dot(n, light), 0.0)


def blinn_phong(n: float3, light: float3, power: float) -> float:
    """The shine of a light from `light` (unit) seen from the front: a highlight
    that `power` makes small and sharp (8 broad, 128 glossy)."""
    h = normalize(light + float3(0.0, 0.0, 1.0))
    return pow(max(dot(n, h), 0.0), power)


def fresnel(n: float3, f0: float, power: float) -> float:
    """Light caught at grazing angles (Schlick): f0 head on, 1 at the rim;
    power 5 is glass, lower spreads it inward."""
    return f0 + (1.0 - f0) * pow(1.0 - max(n.z, 0.0), power)


def shine(p: float2, angle: float, offset: float, width: float) -> float:
    """A band of light across a shape, the glint swept over a button: turned by
    `angle`, moved `offset` along its normal (animate it), `width` wide."""
    x = dot(p, float2(cos(angle), sin(angle))) - offset
    return 1.0 - smoothstep(0.0, width * 0.5, abs(x))


# Shadows


def erf(x: float) -> float:
    """The error function, to within 0.001."""
    a = abs(x)
    t = 1.0 + (0.278393 + (0.230389 + 0.078108 * (a * a)) * a) * a
    t *= t
    return sign(x) * (1.0 - 1.0 / (t * t))


def drop_shadow(d: float, blur: float) -> float:
    """How dark the shadow of a shape is, 0..1, from its distance d (place the
    shape at the shadow's offset): the shape blurred by a Gaussian of `blur`.
    Exact along straight edges; corners come out a little rounder."""
    return 0.5 - 0.5 * erf(d / (blur * sqrt(2.0)))


def _box_shadow_x(x: float, y: float, blur: float, corner: float, half_size: float2) -> float:
    delta = min(half_size.y - corner - abs(y), 0.0)
    curved = half_size.x - corner + sqrt(max(0.0, corner * corner - delta * delta))
    k = sqrt(0.5) / blur
    return 0.5 * (erf((x + curved) * k) - erf((x - curved) * k))


def box_shadow(p: float2, half_size: float2, corner: float, blur: float) -> float:
    """The shadow of a rounded box, 0..1, blurred by a Gaussian of `blur`: exact
    across x, four samples down y. Sharper corners than drop_shadow's."""
    low = p.y - half_size.y
    high = p.y + half_size.y
    start = clamp(-3.0 * blur, low, high)
    end = clamp(3.0 * blur, low, high)
    dy = (end - start) / 4.0
    y = start + dy * 0.5
    value = 0.0
    for _ in range(4):
        g = exp(-y * y / (2.0 * blur * blur)) / (sqrt(2.0 * PI) * blur)
        value += _box_shadow_x(p.x, p.y - y, blur, corner, half_size) * g * dy
        y += dy
    return value


def circle_shadow(p: float2, light: float2, light_radius: float, center: float2, radius: float) -> float:
    """How much of a round light of `light_radius` at `light` p sees past a disk
    of `radius` at `center`: 1 lit, 0 in the full shadow, a soft penumbra between.
    Multiply several for several disks."""
    to_light = light - p
    to_disk = center - p
    dl = length(to_light)
    dd = length(to_disk)
    if dd <= radius:
        return 0.0
    # Both as angles seen from p; the disk shades only what is behind it.
    al = asin(min(light_radius / dl, 1.0))
    ad = asin(min(radius / dd, 1.0))
    between = acos(clamp(dot(to_light, to_disk) / (dl * dd), -1.0, 1.0))
    hidden = clamp(min(al, between + ad) - max(-al, between - ad), 0.0, 2.0 * al)
    behind = step(dd - radius, dl)
    return 1.0 - behind * hidden / (2.0 * al)


def soft_shadow_step(shadow: float, d: float, t: float, softness: float) -> float:
    """One step of a soft shadow marched through your own scene toward a light:
    d is the scene's distance at the point t along the way. Start with 1.0, step
    t by max(d, a little) until the light, and stop at d < 0 (0.0, in shadow).
    `softness` 2 is very soft, 32 nearly hard."""
    return min(shadow, softness * d / t)


def occlusion(d: float, radius: float, strength: float) -> float:
    """Darkening near a shape's edge, the shade in a corner: 1 - strength at the
    edge, 1 from `radius` away. Multiply the background by it."""
    t = 1.0 - clamp(d / radius, 0.0, 1.0)
    return 1.0 - strength * t * t


# Tone mapping: added-up light (any brightness) back into 0..1.


def tonemap_exposure(c: float3, exposure: float) -> float3:
    """1 - exp(-c · exposure): smooth, never clips."""
    return 1.0 - exp(-c * exposure)


def tonemap_reinhard(c: float3) -> float3:
    """c / (1 + c)."""
    return c / (1.0 + c)


def tonemap_aces(c: float3) -> float3:
    """Film-like: more contrast, bright colors run to white."""
    return clamp((c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14), 0.0, 1.0)
