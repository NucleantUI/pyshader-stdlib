"""2D signed distance functions: the distance from p to a shape's edge,
negative inside. Shapes sit at the origin; move p to place them
(`sd_circle(p - center, r)`), turn it with `matrix.rotate2d`.

    d = op_smooth_union(sd_circle(p, 0.3), sd_box(p - float2(0.3, 0.0), float2(0.2)), 0.1)
    color = mix(background, ink, fill_smooth(d, 0.01))

Credits:
- distance functions and operators: Inigo Quilez, "2D distance functions" —
  https://iquilezles.org/articles/distfunctions2d/ and "smooth minimum" —
  https://iquilezles.org/articles/smin/ (his shader code is MIT licensed)
- `sd_arc_polygon`: after Aditya Ganeshan's polygon with bulge-arc edges
  (2026, MIT licensed), which builds on sdPolygon; bulges as in AutoCAD's
  polylines — https://www.lee-mac.com/bulgeconversion.html
- `fill` / `stroke`: the way The Book of Shaders, ch. 7 "Shapes"
  (https://thebookofshaders.com/07/) turns a distance field into a mask
"""
from pyshader import *


def sd_circle(p: float2, r: float) -> float:
    """A circle of radius r."""
    return length(p) - r


def sd_box(p: float2, b: float2) -> float:
    """A box with half-size b."""
    d = abs(p) - b
    return length(max(d, float2(0.0))) + min(max(d.x, d.y), 0.0)


def sd_rounded_box(p: float2, b: float2, r: float4) -> float:
    """A box with half-size b and a radius per corner: r = (top right, bottom right, top left, bottom left)."""
    rr = r.xy if p.x > 0.0 else r.zw
    radius = rr.x if p.y > 0.0 else rr.y
    q = abs(p) - b + radius
    return min(max(q.x, q.y), 0.0) + length(max(q, float2(0.0))) - radius


def sd_segment(p: float2, a: float2, b: float2) -> float:
    """Distance to the line segment from a to b; subtract a width for a stroke."""
    pa = p - a
    ba = b - a
    h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0)
    return length(pa - ba * h)


def sd_equilateral_triangle(p: float2, r: float) -> float:
    """An equilateral triangle pointing up; r is half its side."""
    k = sqrt(3.0)
    q = float2(abs(p.x) - r, p.y + r / k)
    if q.x + k * q.y > 0.0:
        q = float2(q.x - k * q.y, -k * q.x - q.y) / 2.0
    q.x -= clamp(q.x, -2.0 * r, 0.0)
    return -length(q) * sign(q.y)


def sd_hexagon(p: float2, r: float) -> float:
    """A hexagon whose sides are r from its center."""
    k = float3(-0.866025404, 0.5, 0.577350269)
    q = abs(p)
    q -= 2.0 * min(dot(k.xy, q), 0.0) * k.xy
    q -= float2(clamp(q.x, -k.z * r, k.z * r), r)
    return length(q) * sign(q.y)


def sd_star5(p: float2, r: float, rf: float) -> float:
    """A five-pointed star of outer radius r; rf (0..1) sets how deep the points cut in."""
    k1 = float2(0.809016994375, -0.587785252292)
    k2 = float2(-k1.x, k1.y)
    q = float2(abs(p.x), p.y)
    q -= 2.0 * max(dot(k1, q), 0.0) * k1
    q -= 2.0 * max(dot(k2, q), 0.0) * k2
    q.x = abs(q.x)
    q.y -= r
    ba = rf * float2(-k1.y, k1.x) - float2(0.0, 1.0)
    h = clamp(dot(q, ba) / dot(ba, ba), 0.0, r)
    return length(q - ba * h) * sign(q.y * ba.x - q.x * ba.y)


def sd_rhombus(p: float2, b: float2) -> float:
    """A rhombus with half-diagonals b."""
    q = abs(p)
    c = b - 2.0 * q
    h = clamp((c.x * b.x - c.y * b.y) / dot(b, b), -1.0, 1.0)
    d = length(q - 0.5 * b * float2(1.0 - h, 1.0 + h))
    return d * sign(q.x * b.y + q.y * b.x - b.x * b.y)


def sd_heart(p: float2) -> float:
    """A heart about one unit tall, its point at the origin."""
    q = float2(abs(p.x), p.y)
    if q.y + q.x > 1.0:
        e = q - float2(0.25, 0.75)
        return sqrt(dot(e, e)) - sqrt(2.0) / 4.0
    a = q - float2(0.0, 1.0)
    b = q - 0.5 * max(q.x + q.y, 0.0)
    return sqrt(min(dot(a, a), dot(b, b))) * sign(q.x - q.y)


def _dot2(v: float2) -> float:
    return dot(v, v)


# Boxes and polygons


def sd_chamfer_box(p: float2, b: float2, chamfer: float) -> float:
    """A box with half-size b and its corners cut off at 45° by `chamfer`."""
    q = abs(p) - b
    q = q.yx if q.y > q.x else q
    q.y += chamfer
    k = 1.0 - sqrt(2.0)
    if q.y < 0.0 and q.y + q.x * k < 0.0:
        return q.x
    if q.x < q.y:
        return (q.x + q.y) * sqrt(0.5)
    return length(q)


def sd_oriented_box(p: float2, a: float2, b: float2, thickness: float) -> float:
    """A box running from a to b, `thickness` wide: a thick line with square ends."""
    l = length(b - a)
    d = (b - a) / l
    c = p - (a + b) * 0.5
    q = float2(d.x * c.x + d.y * c.y, -d.y * c.x + d.x * c.y)
    q = abs(q) - float2(l, thickness) * 0.5
    return length(max(q, float2(0.0))) + min(max(q.x, q.y), 0.0)


def sd_trapezoid(p: float2, r1: float, r2: float, he: float) -> float:
    """A trapezoid: half-width r1 at the bottom (y = -he), r2 at the top (y = he)."""
    k1 = float2(r2, he)
    k2 = float2(r2 - r1, 2.0 * he)
    q = float2(abs(p.x), p.y)
    ca = float2(q.x - min(q.x, r1 if q.y < 0.0 else r2), abs(q.y) - he)
    cb = q - k1 + k2 * clamp(dot(k1 - q, k2) / _dot2(k2), 0.0, 1.0)
    s = -1.0 if cb.x < 0.0 and ca.y < 0.0 else 1.0
    return s * sqrt(min(_dot2(ca), _dot2(cb)))


def sd_parallelogram(p: float2, wi: float, he: float, sk: float) -> float:
    """A parallelogram: half-width wi, half-height he, top edge shifted right by sk."""
    e = float2(sk, he)
    q = -p if p.y < 0.0 else p
    w = q - e
    w.x -= clamp(w.x, -wi, wi)
    d = float2(dot(w, w), -w.y)
    s = q.x * e.y - q.y * e.x
    q = -q if s < 0.0 else q
    v = q - float2(wi, 0.0)
    v -= e * clamp(dot(v, e) / dot(e, e), -1.0, 1.0)
    d = min(d, float2(dot(v, v), wi * he - abs(s)))
    return sqrt(d.x) * sign(-d.y)


def sd_triangle(p: float2, p0: float2, p1: float2, p2: float2) -> float:
    """Any triangle, by its three corners."""
    e0 = p1 - p0
    e1 = p2 - p1
    e2 = p0 - p2
    v0 = p - p0
    v1 = p - p1
    v2 = p - p2
    pq0 = v0 - e0 * clamp(dot(v0, e0) / dot(e0, e0), 0.0, 1.0)
    pq1 = v1 - e1 * clamp(dot(v1, e1) / dot(e1, e1), 0.0, 1.0)
    pq2 = v2 - e2 * clamp(dot(v2, e2) / dot(e2, e2), 0.0, 1.0)
    s = sign(e0.x * e2.y - e0.y * e2.x)
    d = min(min(float2(dot(pq0, pq0), s * (v0.x * e0.y - v0.y * e0.x)),
                float2(dot(pq1, pq1), s * (v1.x * e1.y - v1.y * e1.x))),
            float2(dot(pq2, pq2), s * (v2.x * e2.y - v2.y * e2.x)))
    return -sqrt(d.x) * sign(d.y)


def sd_isosceles_triangle(p: float2, q: float2) -> float:
    """A triangle with its tip at the origin and its base from (-q.x, q.y) to
    (q.x, q.y); a negative q.y has it point up."""
    r = float2(abs(p.x), p.y)
    a = r - q * clamp(dot(r, q) / dot(q, q), 0.0, 1.0)
    b = r - q * float2(clamp(r.x / q.x, 0.0, 1.0), 1.0)
    s = -sign(q.y)
    d = min(float2(dot(a, a), s * (r.x * q.y - r.y * q.x)),
            float2(dot(b, b), s * (r.y - q.y)))
    return -sqrt(d.x) * sign(d.y)


def sd_polygon(v: list[float2], p: float2) -> float:
    """Any simple polygon, by its corners in order (a list of any length).
    Exact, for convex and concave polygons alike."""
    d = dot(p - v[0], p - v[0])
    s = 1.0
    # The previous corner is carried along, not indexed: OpenGL ES 2 indexes
    # only with constants and the loop's counter.
    last = v[len(v) - 1]
    for i in range(len(v)):
        e = last - v[i]
        w = p - v[i]
        b = w - e * clamp(dot(w, e) / dot(e, e), 0.0, 1.0)
        d = min(d, dot(b, b))
        # Crossings of a ray to the right: an odd count is inside.
        c = bool3(p.y >= v[i].y, p.y < last.y, e.x * w.y > e.y * w.x)
        if all(c) or not any(c):
            s = -s
        last = v[i]
    return s * sqrt(d)


def sd_arc_polygon(v: list[float3], p: float2) -> float:
    """Any outline of straight edges and circular arcs, by its corners in order:
    v[i] = (x, y, bulge), the bulge of the edge from corner i to the next.
    A bulge of 0 is a straight edge, else tan(arc angle / 4): 1 a half circle,
    0.41 a quarter; positive bows the edge to the right of its direction
    (outward when the corners run counterclockwise), negative to the left.
    Exact."""
    d = dot(p - v[0].xy, p - v[0].xy)
    s = 1.0
    last = v[len(v) - 1]      # carried along, as in sd_polygon
    for i in range(len(v)):
        a = last.xy
        b = v[i].xy
        k = last.z
        e = b - a
        w = p - a
        # Crossings of a ray to the right with the chord: an odd count is inside.
        c = bool3(p.y >= a.y, p.y < b.y, e.x * w.y > e.y * w.x)
        if all(c) or not any(c):
            s = -s
        if abs(k) < 0.0001:
            g = w - e * clamp(dot(w, e) / dot(e, e), 0.0, 1.0)
            d = min(d, dot(g, g))
        else:
            # The arc's circle: center beside the chord's middle, toward the
            # bulge for more than a half circle, away from it for less.
            n = float2(e.y, -e.x)                     # the chord's right normal, chord-long
            center = (a + b) * 0.5 + n * ((k * k - 1.0) / (4.0 * k))
            radius = length(e) * (1.0 + k * k) / (4.0 * abs(k))
            u = p - center
            l = length(u)
            # p's nearest point on the circle is on the arc when it lies on the
            # bulge's side of the chord; else the nearest point is an end.
            if length(e) * (k * k - 1.0) * l + sign(k) * (1.0 + k * k) * dot(u, n) > 0.0:
                d = min(d, (l - radius) * (l - radius))
            else:
                d = min(d, min(dot(w, w), dot(p - b, p - b)))
            # Between the chord and the arc: the arc adds it, or cuts it away.
            if l < radius and sign(k) * dot(w, n) > 0.0:
                s = -s
        last = v[i]
    return s * sqrt(d)


def sd_stairs(p: float2, wh: float2, n: float) -> float:
    """A staircase of n steps, each wh.x deep and wh.y high, climbing to the
    right from the origin; solid below the steps, down to y = 0."""
    ba = wh * n
    d = min(_dot2(p - float2(clamp(p.x, 0.0, ba.x), 0.0)),
            _dot2(p - float2(ba.x, clamp(p.y, 0.0, ba.y))))
    s = sign(max(-p.y, p.x - ba.x))
    dia = length(wh)
    q = float2(wh.x * p.x + wh.y * p.y, wh.x * p.y - wh.y * p.x) / dia
    i = clamp(floor(q.x / dia + 0.5), 0.0, n - 1.0)
    q.x -= i * dia
    q = float2(wh.x * q.x - wh.y * q.y, wh.y * q.x + wh.x * q.y) / dia
    hh = wh.y * 0.5
    q.y -= hh
    if q.y > hh * sign(q.x):
        s = 1.0
    q = q if i < 0.5 or q.x > 0.0 else -q
    d = min(d, _dot2(q - float2(0.0, clamp(q.y, -hh, hh))))
    d = min(d, _dot2(q - float2(clamp(q.x, 0.0, wh.x), hh)))
    return sqrt(d) * s


def sd_pentagon(p: float2, r: float) -> float:
    """A regular pentagon whose sides are r from its center, a corner pointing down."""
    k = float3(0.809016994, 0.587785252, 0.726542528)
    q = float2(abs(p.x), p.y)
    q -= 2.0 * min(dot(float2(-k.x, k.y), q), 0.0) * float2(-k.x, k.y)
    q -= 2.0 * min(dot(float2(k.x, k.y), q), 0.0) * float2(k.x, k.y)
    q -= float2(clamp(q.x, -r * k.z, r * k.z), r)
    return length(q) * sign(q.y)


def sd_octagon(p: float2, r: float) -> float:
    """A regular octagon whose sides are r from its center."""
    k = float3(-0.9238795325, 0.3826834323, 0.4142135623)
    q = abs(p)
    q -= 2.0 * min(dot(float2(k.x, k.y), q), 0.0) * float2(k.x, k.y)
    q -= 2.0 * min(dot(float2(-k.x, k.y), q), 0.0) * float2(-k.x, k.y)
    q -= float2(clamp(q.x, -k.z * r, k.z * r), r)
    return length(q) * sign(q.y)


# Stars and crosses


def sd_hexagram(p: float2, r: float) -> float:
    """A six-pointed star (two overlapping triangles)."""
    k = float4(-0.5, 0.8660254038, 0.5773502692, 1.7320508076)
    q = abs(p)
    q -= 2.0 * min(dot(k.xy, q), 0.0) * k.xy
    q -= 2.0 * min(dot(k.yx, q), 0.0) * k.yx
    q -= float2(clamp(q.x, r * k.z, r * k.w), r)
    return length(q) * sign(q.y)


def sd_pentagram(p: float2, r: float) -> float:
    """A five-pointed star with straight-through edges, points r from the center."""
    k1x = 0.809016994
    k2x = 0.309016994
    k1y = 0.587785252
    k2y = 0.951056516
    k1z = 0.726542528
    v1 = float2(k1x, -k1y)
    v2 = float2(-k1x, -k1y)
    v3 = float2(k2x, -k2y)
    q = float2(abs(p.x), p.y)
    q -= 2.0 * max(dot(v1, q), 0.0) * v1
    q -= 2.0 * max(dot(v2, q), 0.0) * v2
    q.x = abs(q.x)
    q.y -= r
    return length(q - v3 * clamp(dot(q, v3), 0.0, k1z * r)) * sign(q.y * v3.x - q.x * v3.y)


def sd_star(p: float2, r: float, n: int, m: float) -> float:
    """An n-pointed star, points r from the center; m (2..n) sets how sharp: 2 is
    spiky, n a regular polygon."""
    an = PI / float(n)
    en = PI / m
    acs = float2(cos(an), sin(an))
    ecs = float2(cos(en), sin(en))
    bn = mod(atan2(p.x, p.y), 2.0 * an) - an
    q = length(p) * float2(cos(bn), abs(sin(bn)))
    q -= r * acs
    q += ecs * clamp(-dot(q, ecs), 0.0, r * acs.y / ecs.y)
    return length(q) * sign(q.x)


def sd_cross(p: float2, b: float2, r: float) -> float:
    """A plus sign: arms b.x long and b.y thick (half sizes); r rounds (or shrinks) it."""
    q = abs(p)
    q = q.yx if q.y > q.x else q
    c = q - b
    k = max(c.y, c.x)
    w = c if k > 0.0 else float2(b.y - q.x, -k)
    return sign(k) * length(max(w, float2(0.0))) + r


def sd_rounded_x(p: float2, w: float, r: float) -> float:
    """An X with round arm ends: arms reaching w along the diagonals, r thick.
    Exact outside; inside, where the arms cross, a bound."""
    q = abs(p)
    return length(q - min(q.x + q.y, w) * 0.5) - r


def sd_rounded_cross(p: float2, h: float) -> float:
    """A cross with concave round sides; h (0..1) sets how thick its arms are."""
    k = 0.5 * (h + 1.0 / h)
    q = abs(p)
    if q.x < 1.0 and q.y < q.x * (k - h) + h:
        return k - sqrt(_dot2(q - float2(1.0, k)))
    return sqrt(min(_dot2(q - float2(0.0, h)), _dot2(q - float2(1.0, 0.0))))


def sd_blobby_cross(p: float2, he: float) -> float:
    """A four-pointed blob with its points at (±1, 0) and (0, ±1). he (at most
    0.35) curves the sides between them: in toward the center for he > 0, a
    cross; out for he < 0, a rounded square."""
    q = abs(p)
    q = float2(abs(q.x - q.y), 1.0 - q.x - q.y) / sqrt(2.0)
    pp = (he - q.y - 0.25 / he) / (6.0 * he)
    qq = q.x / (he * he * 16.0)
    h = qq * qq - pp * pp * pp
    x = 0.0
    if h > 0.0:
        r = sqrt(h)
        x = pow(qq + r, 1.0 / 3.0) - pow(abs(qq - r), 1.0 / 3.0) * sign(r - qq)
    else:
        r = sqrt(pp)
        x = 2.0 * r * cos(acos(qq / (pp * r)) / 3.0)
    x = min(x, sqrt(2.0) / 2.0)
    z = float2(x, he * (1.0 - 2.0 * x * x)) - q
    return length(z) * sign(z.y)


def sd_cool_s(p: float2) -> float:
    """The "Cool S" of school notebooks, from y = -1 to 1."""
    six = -p.x if p.y < 0.0 else p.x
    q = float2(abs(p.x), abs(p.y) - 0.2)
    rex = q.x - min(floor(q.x / 0.4 + 0.5), 0.4)
    aby = abs(q.y - 0.2) - 0.6
    d = _dot2(float2(six, -q.y) - clamp(0.5 * (six - q.y), 0.0, 0.2))
    d = min(d, _dot2(float2(q.x, -aby) - clamp(0.5 * (q.x - aby), 0.0, 0.4)))
    d = min(d, _dot2(float2(rex, q.y - clamp(q.y, 0.0, 0.4))))
    s = 2.0 * q.x + aby + abs(aby + 0.4) - 0.4
    return sqrt(d) * sign(s)


# Round shapes


def sd_ellipse(p: float2, ab: float2) -> float:
    """An ellipse with half-axes ab.x and ab.y (they must differ; use sd_circle when equal)."""
    q = abs(p)
    e = ab
    if q.x > q.y:
        q = q.yx
        e = e.yx
    l = e.y * e.y - e.x * e.x
    m = e.x * q.x / l
    m2 = m * m
    n = e.y * q.y / l
    n2 = n * n
    c = (m2 + n2 - 1.0) / 3.0
    c3 = c * c * c
    qq = c3 + m2 * n2 * 2.0
    d = c3 + m2 * n2
    g = m + m * n2
    co = 0.0
    if d < 0.0:
        h = acos(qq / c3) / 3.0
        s = cos(h)
        t = sin(h) * sqrt(3.0)
        rx = sqrt(-c * (s + t + 2.0) + m2)
        ry = sqrt(-c * (s - t + 2.0) + m2)
        co = (ry + sign(l) * rx + abs(g) / (rx * ry) - m) / 2.0
    else:
        h = 2.0 * m * n * sqrt(d)
        s = sign(qq + h) * pow(abs(qq + h), 1.0 / 3.0)
        u = sign(qq - h) * pow(abs(qq - h), 1.0 / 3.0)
        rx = -s - u - c * 4.0 + 2.0 * m2
        ry = (s - u) * sqrt(3.0)
        rm = sqrt(rx * rx + ry * ry)
        co = (ry / sqrt(rm - rx) + 2.0 * g / rm - m) / 2.0
    r = e * float2(co, sqrt(1.0 - co * co))
    # Inside or out by the ellipse's own equation: steady on the axes, where
    # comparing with the nearest point's height is not.
    return length(r - q) * sign(_dot2(q / e) - 1.0)


def sd_quadratic_circle(p: float2) -> float:
    """A circle of radius 1 drawn with parabolas: a little squarer than a circle."""
    q = abs(p)
    if q.y > q.x:
        q = q.yx
    a = q.x - q.y
    b = q.x + q.y
    c = (2.0 * b - 1.0) / 3.0
    h = a * a + c * c * c
    t = 0.0
    if h >= 0.0:
        h = sqrt(h)
        t = sign(h - a) * pow(abs(h - a), 1.0 / 3.0) - pow(h + a, 1.0 / 3.0)
    else:
        z = sqrt(-c)
        v = acos(a / (c * z)) / 3.0
        t = -z * (cos(v) + sin(v) * 1.732050808)
    t *= 0.5
    w = float2(-t, t) + 0.75 - t * t - q
    return length(w) * sign(a * a * 0.5 + b - 1.5)


def sd_pie(p: float2, c: float2, r: float) -> float:
    """A pie slice of radius r opening upward; c = (sin, cos) of half its angle."""
    q = float2(abs(p.x), p.y)
    l = length(q) - r
    m = length(q - c * clamp(dot(q, c), 0.0, r))
    return max(l, m * sign(c.y * q.x - c.x * q.y))


def sd_arc(p: float2, sc: float2, ra: float, rb: float) -> float:
    """An arc of radius ra, rb thick, opening upward; sc = (sin, cos) of half its angle."""
    q = float2(abs(p.x), p.y)
    if sc.y * q.x > sc.x * q.y:
        return length(q - sc * ra) - rb
    return abs(length(q) - ra) - rb


def sd_ring(p: float2, n: float2, r: float, th: float) -> float:
    """A piece of a ring of radius r, th thick, with flat ends, centered on the
    +y axis; n = (cos, sin) of half its angle."""
    q = float2(abs(p.x), p.y)
    q = float2(n.x * q.x - n.y * q.y, n.y * q.x + n.x * q.y)
    return max(abs(length(q) - r) - th * 0.5,
               length(float2(q.x, max(0.0, abs(r - q.y) - th * 0.5))) * sign(q.x))


def sd_cut_disk(p: float2, r: float, h: float) -> float:
    """A disk of radius r with everything below y = h cut away (-r < h < r)."""
    w = sqrt(r * r - h * h)
    q = float2(abs(p.x), p.y)
    s = max((h - r) * q.x * q.x + w * w * (h + r - 2.0 * q.y), h * q.x - w * q.y)
    if s < 0.0:
        return length(q) - r
    if q.x < w:
        return h - q.y
    return length(q - float2(w, h))


def sd_moon(p: float2, d: float, ra: float, rb: float) -> float:
    """A crescent: a circle of radius ra with one of radius rb, d to the right, cut out of it."""
    q = float2(p.x, abs(p.y))
    a = (ra * ra - rb * rb + d * d) / (2.0 * d)
    b = sqrt(max(ra * ra - a * a, 0.0))
    if d * (q.x * b - q.y * a) > d * d * max(b - q.y, 0.0):
        return length(q - float2(a, b))
    return max(length(q) - ra, -(length(q - float2(d, 0.0)) - rb))


def sd_vesica(p: float2, r: float, d: float) -> float:
    """A lens (vesica piscis): where two circles of radius r, centered d left and
    right of the origin, overlap (d < r)."""
    q = abs(p)
    b = sqrt(r * r - d * d)
    if (q.y - b) * d > q.x * b:
        return length(q - float2(0.0, b))
    return length(q - float2(-d, 0.0)) - r


def sd_lens(p: float2, w: float, h: float) -> float:
    """A lens (vesica) lying on its side, by its size: its points at (±w, 0),
    h half tall in the middle (h < w). Turn it upright with p.yx."""
    d = 0.5 * (w * w - h * h) / h
    q = abs(p)
    if w * q.y < d * (q.x - w):
        return length(q - float2(w, 0.0))
    return length(q - float2(0.0, -d)) - (d + h)


def sd_oriented_vesica(p: float2, a: float2, b: float2, w: float) -> float:
    """A lens with its points at a and b, w half wide in the middle (w smaller
    than half the distance from a to b)."""
    r = 0.5 * length(b - a)
    d = 0.5 * (r * r - w * w) / w
    v = (b - a) / r
    c = p - (a + b) * 0.5
    q = 0.5 * abs(float2(v.y * c.x - v.x * c.y, v.x * c.x + v.y * c.y))
    if r * q.x < d * (q.y - r):
        return length(q - float2(0.0, r))
    return length(q - float2(-d, 0.0)) - (d + w)


def sd_egg(p: float2, ra: float, rb: float) -> float:
    """An egg: a circle of radius ra at the bottom narrowing to rb at the top (rb < ra)."""
    k = sqrt(3.0)
    q = float2(abs(p.x), p.y)
    r = ra - rb
    if q.y < 0.0:
        return length(q) - r - rb
    if k * (q.x + r) < q.y:
        return length(float2(q.x, q.y - k * r)) - rb
    return length(float2(q.x + r, q.y)) - 2.0 * r - rb


def sd_bulging_egg(p: float2, he: float, ra: float, rb: float, bu: float) -> float:
    """An egg from a circle of radius ra at the origin to one of radius rb at
    (0, he), joined by round sides; bu (0..1] sets how much they bulge."""
    r = 0.5 * (he + ra + rb) / bu
    da = r - ra
    db = r - rb
    y = (db * db - da * da - he * he) / (2.0 * he)
    x = sqrt(da * da - y * y)
    q = float2(abs(p.x), p.y)
    k = q.y * x - q.x * y
    if k > 0.0 and k < he * (q.x + x):
        return length(q + float2(x, y)) - r
    return min(length(q) - ra, length(float2(q.x, q.y - he)) - rb)


def sd_uneven_capsule(p: float2, r1: float, r2: float, h: float) -> float:
    """A capsule from a circle of radius r1 at the origin to one of radius r2 at (0, h)."""
    q = float2(abs(p.x), p.y)
    b = (r1 - r2) / h
    a = sqrt(1.0 - b * b)
    k = dot(q, float2(-b, a))
    if k < 0.0:
        return length(q) - r1
    if k > a * h:
        return length(q - float2(0.0, h)) - r2
    return dot(q, float2(a, b)) - r1


def sd_horseshoe(p: float2, c: float2, r: float, w: float2) -> float:
    """A horseshoe of radius r opening upward; c = (cos, sin) of the angle its legs
    leave the circle at, w = (length of the legs, half thickness)."""
    q = float2(abs(p.x), p.y)
    l = length(q)
    q = float2(-c.x * q.x + c.y * q.y, c.y * q.x + c.x * q.y)
    q = float2(q.x if q.y > 0.0 or q.x > 0.0 else l * sign(-c.x), q.y if q.x > 0.0 else l)
    q = float2(q.x, abs(q.y - r)) - w
    return length(max(q, float2(0.0))) + min(0.0, max(q.x, q.y))


def sd_tunnel(p: float2, wh: float2) -> float:
    """An arch: a box of half-width wh.x reaching down wh.y, its top a half circle."""
    q0 = float2(abs(p.x), -p.y)
    q = q0 - wh
    d1 = _dot2(float2(max(q.x, 0.0), q.y))
    q.x = q.x if q0.y > 0.0 else length(q0) - wh.x
    d2 = _dot2(float2(q.x, max(q.y, 0.0)))
    d = sqrt(min(d1, d2))
    return -d if max(q.x, q.y) < 0.0 else d


# Curves (unsigned: distance to the line itself)


def sd_parabola(p: float2, k: float) -> float:
    """Signed distance to the parabola y = k·x², negative inside its cup (above it for k > 0)."""
    q = float2(abs(p.x), p.y)
    ik = 1.0 / k
    pp = ik * (q.y - 0.5 * ik) / 3.0
    qq = 0.25 * ik * ik * q.x
    h = qq * qq - pp * pp * pp
    r = sqrt(abs(h))
    x = 0.0
    if h > 0.0:
        x = pow(qq + r, 1.0 / 3.0) - pow(abs(qq - r), 1.0 / 3.0) * sign(r - qq)
    else:
        x = 2.0 * cos(atan2(r, qq) / 3.0) * sqrt(pp)
    return length(q - float2(x, k * x * x)) * sign(q.x - x)


def sd_parabola_segment(p: float2, wi: float, he: float) -> float:
    """Signed distance to an arch of parabola from (-wi, 0) up to (0, he) and
    down to (wi, 0); negative below the curve."""
    q = float2(abs(p.x), p.y)
    ik = wi * wi / he
    pp = ik * (he - q.y - 0.5 * ik) / 3.0
    qq = q.x * ik * ik / 4.0
    h = qq * qq - pp * pp * pp
    x = 0.0
    if h > 0.0:
        r = pow(qq + sqrt(h), 1.0 / 3.0)
        x = r + pp / r
    else:
        r = sqrt(pp)
        x = 2.0 * r * cos(acos(qq / (pp * r)) / 3.0)
    x = min(x, wi)
    return length(q - float2(x, he - x * x / ik)) * sign(ik * (q.y - he) + q.x * q.x)


def sd_hyperbola(p: float2, k: float, he: float) -> float:
    """Signed distance to the hyperbola x² - y² = 2k (k > 0), its two branches
    cut off he from the x axis; negative inside the branches."""
    q = abs(p)
    q = float2(q.x - q.y, q.x + q.y) / sqrt(2.0)
    x2 = q.x * q.x / 16.0
    y2 = q.y * q.y / 16.0
    r = k * (4.0 * k - q.x * q.y) / 12.0
    qq = (x2 - y2) * k * k
    h = qq * qq + r * r * r
    u = 0.0
    if h < 0.0:
        m = sqrt(-r)
        u = m * cos(acos(qq / (r * m)) / 3.0)
    else:
        m = pow(sqrt(h) - qq, 1.0 / 3.0)
        u = (m - r / m) / 2.0
    w = sqrt(u + x2)
    b = k * q.y - x2 * q.x * 2.0
    t = q.x / 4.0 - w + sqrt(2.0 * x2 - u + b / w / 4.0)
    t = max(t, sqrt(he * he * 0.5 + k) - he / sqrt(2.0))
    d = length(q - float2(t, k / t))
    return d if q.x * q.y < k else -d


def sd_circle_wave(p: float2, tb: float, ra: float) -> float:
    """Distance to a wave of circle arcs of radius ra running along the x axis;
    tb (0..1) sets how much of each circle an arc takes, from nearly flat to
    almost closed loops."""
    t = PI * 5.0 / 6.0 * max(tb, 0.0001)
    co = ra * float2(sin(t), cos(t))
    x = abs(mod(p.x, co.x * 4.0) - co.x * 2.0)
    p1 = float2(x, p.y)
    p2 = float2(abs(x - 2.0 * co.x), 2.0 * co.y - p.y)
    d1 = length(p1 - co) if co.y * p1.x > co.x * p1.y else abs(length(p1) - ra)
    d2 = length(p2 - co) if co.y * p2.x > co.x * p2.y else abs(length(p2) - ra)
    return min(d1, d2)


# Repetition: these move p, not the distance. Draw one shape at the point they
# return and it is drawn in every cell. A shape bigger than its cell is cut
# off at the cell's edge.


def op_repeat(p: float2, spacing: float2) -> float2:
    """Repeats a shape over a grid, a copy every `spacing`, one at the origin."""
    return p - spacing * floor(p / spacing + 0.5)


def op_repeat_limited(p: float2, spacing: float2, count: float2) -> float2:
    """Repeats a shape over a grid, `count` copies to each side of the one at the
    origin: (2·count + 1) along each axis. A row: count = (n, 0)."""
    return p - spacing * clamp(floor(p / spacing + 0.5), -count, count)


def op_repeat_polar(p: float2, count: float) -> float2:
    """Repeats a shape `count` times around the origin. Place the one copy along
    +x: sd_circle(op_repeat_polar(p, 6.0) - float2(0.3, 0.0), 0.1)."""
    an = 2.0 * PI / count
    a = mod(atan2(p.y, p.x) + 0.5 * an, an) - 0.5 * an
    return length(p) * float2(cos(a), sin(a))


def sd_bezier(p: float2, a: float2, b: float2, c: float2) -> float:
    """Distance to the quadratic Bézier curve from a to c, pulled toward b; subtract
    a width for a stroke."""
    e = b - a
    f = a - 2.0 * b + c
    g = e * 2.0
    d = a - p
    kk = 1.0 / dot(f, f)
    kx = kk * dot(e, f)
    ky = kk * (2.0 * dot(e, e) + dot(d, f)) / 3.0
    kz = kk * dot(d, e)
    pp = ky - kx * kx
    p3 = pp * pp * pp
    q = kx * (2.0 * kx * kx - 3.0 * ky) + kz
    h = q * q + 4.0 * p3
    res = 0.0
    if h >= 0.0:
        h = sqrt(h)
        x = (float2(h, -h) - q) / 2.0
        uv = sign(x) * pow(abs(x), float2(1.0 / 3.0))
        t = clamp(uv.x + uv.y - kx, 0.0, 1.0)
        res = _dot2(d + (g + f * t) * t)
    else:
        z = sqrt(-pp)
        v = acos(q / (pp * z * 2.0)) / 3.0
        m = cos(v)
        n = sin(v) * 1.732050808
        ts = clamp(float3(m + m, -n - m, n - m) * z - kx, 0.0, 1.0)
        res = min(_dot2(d + (g + f * ts.x) * ts.x), _dot2(d + (g + f * ts.y) * ts.y))
    return sqrt(res)


# Operators


def op_union(a: float, b: float) -> float:
    """Both shapes."""
    return min(a, b)


def op_subtract(a: float, b: float) -> float:
    """a with b cut out of it."""
    return max(a, -b)


def op_intersect(a: float, b: float) -> float:
    """Only where the shapes overlap."""
    return max(a, b)


def op_smooth_union(a: float, b: float, k: float) -> float:
    """Union blended over a distance of about k (quadratic smooth minimum)."""
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k * 0.25


def op_smooth_subtract(a: float, b: float, k: float) -> float:
    """a with b cut out of it, the cut's edge rounded over about k."""
    return -op_smooth_union(-a, b, k)


def op_smooth_intersect(a: float, b: float, k: float) -> float:
    """The overlap of the shapes, its edges rounded over about k."""
    return -op_smooth_union(-a, -b, k)


def op_round(d: float, r: float) -> float:
    """Rounds a shape's corners by growing it by r."""
    return d - r


def op_onion(d: float, thickness: float) -> float:
    """A shape's outline as a shape of its own, `thickness` thick."""
    return abs(d) - thickness * 0.5


# Distance to mask


def fill(d: float) -> float:
    """1.0 inside the shape."""
    return 1.0 - step(0.0, d)


def fill_smooth(d: float, blur: float) -> float:
    """1.0 inside the shape, its edge blurred over `blur`."""
    return 1.0 - smoothstep(-blur, blur, d)


def stroke(d: float, width: float) -> float:
    """1.0 on the shape's edge, `width` thick."""
    return 1.0 - step(width * 0.5, abs(d))


def stroke_smooth(d: float, width: float, blur: float) -> float:
    """1.0 on the shape's edge, `width` thick, blurred over `blur`."""
    return 1.0 - smoothstep(width * 0.5 - blur, width * 0.5 + blur, abs(d))
