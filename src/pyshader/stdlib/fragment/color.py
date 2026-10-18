"""Color spaces and palettes.

Credits:
- HSB and the color chapter: The Book of Shaders, ch. 6 "Colors",
  Patricio Gonzalez Vivo & Jen Lowe — https://thebookofshaders.com/06/
- `rgb_to_hsb`: Sam Hocevar's branchless RGB to HSV —
  https://lolengine.net/blog/2013/07/27/rgb-to-hsv-in-glsl
- `hsb_to_rgb`: Inigo Quilez's smooth HSV — https://www.shadertoy.com/view/MsS3Wc (MIT)
- `palette`: Inigo Quilez, "Palettes" — https://iquilezles.org/articles/palettes/
- YUV: The Book of Shaders, ch. 8 "Matrices" — https://thebookofshaders.com/08/
  (BT.601 coefficients)
- sRGB transfer: IEC 61966-2-1; luminance: ITU-R BT.709
"""
from pyshader import *

_K = float4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0)

# Columns of the BT.601 matrices.
RGB_TO_YUV = float3x3(
    float3(0.299, -0.14713, 0.615),
    float3(0.587, -0.28886, -0.51499),
    float3(0.114, 0.436, -0.10001),
)
YUV_TO_RGB = float3x3(
    float3(1.0, 1.0, 1.0),
    float3(0.0, -0.39465, 2.03211),
    float3(1.13983, -0.58060, 0.0),
)


def rgb_to_hsb(c: float3) -> float3:
    """RGB to hue, saturation, brightness, each in 0..1."""
    p = mix(float4(c.bg, _K.wz), float4(c.gb, _K.xy), step(c.b, c.g))
    q = mix(float4(p.xyw, c.r), float4(c.r, p.yzx), step(p.x, c.r))
    d = q.x - min(q.w, q.y)
    e = 1.0e-10
    return float3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x)


def hsb_to_rgb(c: float3) -> float3:
    """Hue, saturation, brightness (each 0..1) to RGB, with the hue's corners smoothed."""
    rgb = clamp(abs(mod(c.x * 6.0 + float3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0)
    rgb = rgb * rgb * (3.0 - 2.0 * rgb)
    return c.z * mix(float3(1.0), rgb, c.y)


def hue_shift(c: float3, amount: float) -> float3:
    """Turns the hue by amount (1.0 is a full turn)."""
    hsb = rgb_to_hsb(c)
    hsb.x = fract(hsb.x + amount)
    return hsb_to_rgb(hsb)


def rgb_to_yuv(c: float3) -> float3:
    """RGB to YUV (BT.601): luma in x, chroma in y and z."""
    return RGB_TO_YUV * c


def yuv_to_rgb(c: float3) -> float3:
    """YUV (BT.601) back to RGB."""
    return YUV_TO_RGB * c


def palette(t: float, a: float3, b: float3, c: float3, d: float3) -> float3:
    """Cosine palette: a + b·cos(2π(c·t + d)). a is the middle, b the swing,
    c the frequency per channel, d the phase per channel."""
    return a + b * cos(6.28318530718 * (c * t + d))


def rainbow(t: float) -> float3:
    """A ready-made cosine palette through the hues."""
    return palette(t, float3(0.5), float3(0.5), float3(1.0), float3(0.0, 0.33, 0.67))


def luminance(c: float3) -> float:
    """Relative luminance of linear RGB (BT.709)."""
    return dot(c, float3(0.2126, 0.7152, 0.0722))


def desaturate(c: float3, amount: float) -> float3:
    """Moves c toward its gray by amount (0 keeps it, 1 is fully gray)."""
    return mix(c, float3(luminance(c)), amount)


def contrast(c: float3, amount: float) -> float3:
    """Scales c away from mid gray (amount > 1) or toward it (amount < 1)."""
    return (c - 0.5) * amount + 0.5


def srgb_to_linear(c: float3) -> float3:
    """sRGB-encoded color to linear light."""
    low = c / 12.92
    high = pow((c + 0.055) / 1.055, float3(2.4))
    return mix(high, low, step(c, float3(0.04045)))


def linear_to_srgb(c: float3) -> float3:
    """Linear light to sRGB encoding."""
    low = c * 12.92
    high = 1.055 * pow(c, float3(1.0 / 2.4)) - 0.055
    return mix(high, low, step(c, float3(0.0031308)))
