"""4x4 transforms for positions: model, view and projection.

    mvp = perspective(radians(60.0), aspect, 0.1, 100.0) * look_at(eye, target, UP) * rotate_y(time)
    position = mvp * float4(p, 1.0)

Right-handed, column-major, applied as `matrix * vector`. The projections
give a y-up clip space with depth 0..1 (near to far).

Credits: the standard matrix forms, as in Song Ho Ahn's "OpenGL Projection
Matrix" (http://www.songho.ca/opengl/gl_projectionmatrix.html), adapted to
depth 0..1; the axis-angle rotation is Rodrigues' rotation formula.
"""
from pyshader import *

UP = float3(0.0, 1.0, 0.0)


def translate(t: float3) -> float4x4:
    """Moves by t."""
    return float4x4(
        float4(1.0, 0.0, 0.0, 0.0),
        float4(0.0, 1.0, 0.0, 0.0),
        float4(0.0, 0.0, 1.0, 0.0),
        float4(t, 1.0),
    )


def scale(s: float3) -> float4x4:
    """Scales by s along x, y and z."""
    return float4x4(
        float4(s.x, 0.0, 0.0, 0.0),
        float4(0.0, s.y, 0.0, 0.0),
        float4(0.0, 0.0, s.z, 0.0),
        float4(0.0, 0.0, 0.0, 1.0),
    )


def rotate_x(angle: float) -> float4x4:
    """Turns by angle (radians) around the x axis."""
    c = cos(angle)
    s = sin(angle)
    return float4x4(
        float4(1.0, 0.0, 0.0, 0.0),
        float4(0.0, c, s, 0.0),
        float4(0.0, -s, c, 0.0),
        float4(0.0, 0.0, 0.0, 1.0),
    )


def rotate_y(angle: float) -> float4x4:
    """Turns by angle (radians) around the y axis."""
    c = cos(angle)
    s = sin(angle)
    return float4x4(
        float4(c, 0.0, -s, 0.0),
        float4(0.0, 1.0, 0.0, 0.0),
        float4(s, 0.0, c, 0.0),
        float4(0.0, 0.0, 0.0, 1.0),
    )


def rotate_z(angle: float) -> float4x4:
    """Turns by angle (radians) around the z axis."""
    c = cos(angle)
    s = sin(angle)
    return float4x4(
        float4(c, s, 0.0, 0.0),
        float4(-s, c, 0.0, 0.0),
        float4(0.0, 0.0, 1.0, 0.0),
        float4(0.0, 0.0, 0.0, 1.0),
    )


def rotate(axis: float3, angle: float) -> float4x4:
    """Turns by angle (radians) around axis, counter-clockwise looking down the axis."""
    a = normalize(axis)
    s = sin(angle)
    c = cos(angle)
    oc = 1.0 - c
    return float4x4(
        float4(oc * a.x * a.x + c, oc * a.x * a.y + a.z * s, oc * a.z * a.x - a.y * s, 0.0),
        float4(oc * a.x * a.y - a.z * s, oc * a.y * a.y + c, oc * a.y * a.z + a.x * s, 0.0),
        float4(oc * a.z * a.x + a.y * s, oc * a.y * a.z - a.x * s, oc * a.z * a.z + c, 0.0),
        float4(0.0, 0.0, 0.0, 1.0),
    )


def perspective(fovy: float, aspect: float, near: float, far: float) -> float4x4:
    """Perspective projection: fovy the vertical field of view (radians), aspect width / height."""
    f = 1.0 / tan(fovy * 0.5)
    return float4x4(
        float4(f / aspect, 0.0, 0.0, 0.0),
        float4(0.0, f, 0.0, 0.0),
        float4(0.0, 0.0, far / (near - far), -1.0),
        float4(0.0, 0.0, near * far / (near - far), 0.0),
    )


def orthographic(left: float, right: float, bottom: float, top: float, near: float, far: float) -> float4x4:
    """Parallel projection of the box left..right, bottom..top, near..far."""
    return float4x4(
        float4(2.0 / (right - left), 0.0, 0.0, 0.0),
        float4(0.0, 2.0 / (top - bottom), 0.0, 0.0),
        float4(0.0, 0.0, 1.0 / (near - far), 0.0),
        float4(-(right + left) / (right - left), -(top + bottom) / (top - bottom), near / (near - far), 1.0),
    )


def look_at(eye: float3, target: float3, up: float3) -> float4x4:
    """View matrix of a camera at eye looking at target, `up` roughly up (often UP)."""
    z = normalize(eye - target)
    x = normalize(cross(up, z))
    y = cross(z, x)
    return float4x4(
        float4(x.x, y.x, z.x, 0.0),
        float4(x.y, y.y, z.y, 0.0),
        float4(x.z, y.z, z.z, 0.0),
        float4(-dot(x, eye), -dot(y, eye), -dot(z, eye), 1.0),
    )


def normal_matrix(model: float4x4) -> float3x3:
    """Transforms normals the way `model` transforms positions, also under non-uniform scale."""
    return transpose(inverse(float3x3(model)))


def transform_point(m: float4x4, p: float3) -> float3:
    """p moved by m, divided back out of homogeneous space."""
    q = m * float4(p, 1.0)
    return q.xyz / q.w


def transform_direction(m: float4x4, d: float3) -> float3:
    """d turned and scaled by m, not moved."""
    return (m * float4(d, 0.0)).xyz
