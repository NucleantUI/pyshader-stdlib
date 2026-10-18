# pyshader-stdlib

PyShader's standard library: ready-made shader functions written in
PyShader, imported like any other PyShader module. Once installed, it sits
under `pyshader` as `pyshader.stdlib`. Only the functions a shader actually
uses are compiled into its SPIR-V.

```py
from pyshader import *
from pyshader.stdlib.fragment.noise import fbm
from pyshader.stdlib.fragment import color          # color.palette(...)

def main(uv: float2, time: float) -> float4:
    n = fbm(uv * 4.0 + time * 0.1, 5)
    return float4(color.rainbow(n), 1.0)
```

## Install

In a shader project managed by uv, next to the `pyshader` stubs:

```toml title="pyproject.toml"
[project]
dependencies = ["pyshader", "pyshader-stdlib"]

[tool.uv.sources]
pyshader = { git = "https://github.com/NucleantUI/PyShader" }
pyshader-stdlib = { git = "https://github.com/NucleantUI/pyshader-stdlib", branch = "master" }
```

then `uv sync`. Installed this way (not editable), the library lands in the
stubs' `pyshader/` folder as `pyshader/stdlib/`, where the compiler and the
editor both find it.

The package declares `pyshader.stdlib` under the `pyshader.modules` entry
point. That entry point is how the compiler knows the package may be
imported from the environment's site-packages.

## `pyshader.stdlib.fragment`

| Module | What's in it |
|---|---|
| `shaping` | `plot`, Inigo Quilez's `almost_identity`, `exp_impulse`, `cubic_pulse`, `gain`, `parabola`, `pcurve`, `sinc` and more, and Golan Levin's seats and sigmoids (`double_cubic_seat`, `logistic_sigmoid`, `quadratic_bezier`, …) |
| `easing` | `sine`, `quad`, `cubic`, `quart`, `quint`, `expo`, `circ`, `back`, `elastic` and `bounce`, each with `_in`, `_out` and `_in_out` |
| `color` | `rgb_to_hsb`, `hsb_to_rgb`, `hue_shift`, `rgb_to_yuv`, `yuv_to_rgb`, `palette`, `rainbow`, `luminance`, `desaturate`, `contrast`, `srgb_to_linear`, `linear_to_srgb` |
| `blend` | `multiply`, `screen`, `overlay`, `darken`, `lighten`, `color_dodge`, `color_burn`, `hard_light`, `soft_light`, `difference`, `exclusion`, `add`, `subtract` |
| `shapes` | masks over 0..1: `rect`, `rect_smooth`, `rect_outline`, `rounded_rect`, `circle`, `circle_smooth`, `ring`, `ellipse`, `polygon`, `polygon_smooth`, `triangle`, `hexagon`, `star`, `heart`, `crescent`, `lens`, `egg`, `pie`, `flower`, `gear`, `plus` |
| `sdf` | boxes and polygons: `sd_polygon` (any list of corners), `sd_box`, `sd_rounded_box`, `sd_chamfer_box`, `sd_oriented_box`, `sd_rhombus`, `sd_trapezoid`, `sd_parallelogram`, `sd_triangle`, `sd_equilateral_triangle`, `sd_isosceles_triangle`, `sd_pentagon`, `sd_hexagon`, `sd_octagon`; stars and crosses: `sd_star`, `sd_star5`, `sd_pentagram`, `sd_hexagram`, `sd_cross`, `sd_rounded_cross`, `sd_rounded_x`; round shapes: `sd_circle`, `sd_ellipse`, `sd_pie`, `sd_arc`, `sd_cut_disk`, `sd_moon`, `sd_vesica`, `sd_egg`, `sd_heart`, `sd_uneven_capsule`, `sd_horseshoe`, `sd_tunnel`; curves: `sd_segment`, `sd_bezier`, `sd_parabola`. Operators: `op_union`, `op_subtract`, `op_intersect` and their smooth versions, `op_round`, `op_onion`. Masks: `fill`, `stroke` and their `_smooth` versions |
| `coords` | `aspect`, `centered`, `to_polar`, `from_polar`, `remap` |
| `matrix` | `rotate2d`, `scale2d`, `shear2d`, `rotate_around`, `scale_around` |
| `pattern` | `tile`, `tile_index`, `brick_tile`, `mirror_tile`, `checker`, `rotate_tile_pattern`, `truchet`, `stripes` |
| `random` | `random1`, `random`, `random2`; Dave Hoskins' `hash11` … `hash33` |
| `noise` | `value_noise1`, `value_noise`, `gradient_noise`, `simplex_noise`, `simplex_noise3`, `fbm`, `turbulence`, `ridge` |
| `cellular` | `cellular`, `cellular2` (F1 and F2), `voronoi` (distance to the border); each takes `time` to move its points |

## `pyshader.stdlib.vertex`

| Module | What's in it |
|---|---|
| `transform` | 4x4 `translate`, `scale`, `rotate_x` / `rotate_y` / `rotate_z`, `rotate(axis, angle)`, `perspective`, `orthographic`, `look_at`, `normal_matrix`, `transform_point`, `transform_direction` |
| `quad` | `quad_corner(vertex_index)`, `quad_uv`, `quad_index`, `grid_cell`, `grid_position`: quads without a vertex buffer |
| `space` | `pixel_to_clip`, `clip_to_pixel`, `pixel_size_to_clip`, `keep_aspect`, `billboard` |
| `deform` | `wave`, `ripple`, `twist`, `bend`, `sway` |

Projections are right-handed and produce y-up clip space with depth 0..1.

## Examples

`examples/` has whole shaders built on the library. It is a uv project of its
own: `uv sync` there installs `pyshader` and `pyshader-stdlib` into its
`.venv`, not editable, the way any shader project gets them. After a change
to the library, `uv sync` installs it again.

- `clouds.py`: fBm and simplex noise with a palette
- `truchet.py`: a truchet maze drawn with distance fields
- `cells.py`: moving Voronoi cells
- `spinning_quads.py`: a graphics-target grid of quads in 3D, using `vertex.quad` and `vertex.transform`

## Credits

Every module's docstring names the sources of its functions.
[CREDITS.md](CREDITS.md) collects them, including the license notices of
the MIT-licensed code this library is based on.
