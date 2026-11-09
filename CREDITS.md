# Credits

pyshader-stdlib writes these techniques in PyShader. Each module's docstring
names its sources; this file collects them.

## The Book of Shaders

Patricio Gonzalez Vivo & Jen Lowe — https://thebookofshaders.com

The structure of `fragment` follows the book's chapters:

| Chapter | Module |
|---|---|
| [05 Algorithmic drawing](https://thebookofshaders.com/05/) | `shaping` (`plot`) |
| [06 Colors](https://thebookofshaders.com/06/) | `color`, `easing` |
| [07 Shapes](https://thebookofshaders.com/07/) | `shapes`, `coords`, `sdf` (`fill` / `stroke`) |
| [08 Matrices](https://thebookofshaders.com/08/) | `matrix`, `color` (YUV) |
| [09 Patterns](https://thebookofshaders.com/09/) | `pattern` |
| [10 Random](https://thebookofshaders.com/10/) | `random`, `pattern` (`truchet`) |
| [11 Noise](https://thebookofshaders.com/11/) | `noise` (value and gradient noise) |
| [12 Cellular noise](https://thebookofshaders.com/12/) | `cellular` |
| [13 Fractal Brownian motion](https://thebookofshaders.com/13/) | `noise` (`fbm`, `turbulence`, `ridge`) |

## LYGIA

Patricio Gonzalez Vivo — https://github.com/patriciogonzalezvivo/lygia

LYGIA served as a reference for which functions a shader library should
have and how to group them. No LYGIA code is copied here: LYGIA is licensed
under the Prosperity License and the Patron License, not an open-source
license.

## Inigo Quilez

https://iquilezles.org

- `shaping`: "Useful little functions" — https://iquilezles.org/articles/functions/
- `sdf` (and the masks `shapes` builds from it): "2D distance functions" —
  https://iquilezles.org/articles/distfunctions2d/ ; "Smooth minimum" —
  https://iquilezles.org/articles/smin/ . `sd_ellipse` decides inside or
  outside by the ellipse's equation instead of the original's comparison
  with the nearest point, which flips on the ellipse's axis.
  `sd_stairs` and `sd_cool_s` round with `floor(x + 0.5)`, and `sd_polygon`
  carries its previous corner along instead of indexing it: OpenGL ES 2 has
  no `round` and indexes arrays only with constants and loop counters.
- `color.palette`: "Palettes" — https://iquilezles.org/articles/palettes/
- `color.hsb_to_rgb`: smooth HSV — https://www.shadertoy.com/view/MsS3Wc
- `noise.gradient_noise`: https://www.shadertoy.com/view/XdXGW8
- `cellular.voronoi`: "Voronoi edges" — https://iquilezles.org/articles/voronoilines/

The shader code Inigo Quilez publishes is under the MIT License:

> The MIT License
> Copyright © Inigo Quilez
> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Polygons with arcs: Aditya Ganeshan

`sdf.sd_arc_polygon` follows Aditya Ganeshan's polygon whose edges are
straight or bulge into circular arcs (Copyright © 2026 Aditya Ganeshan, MIT
License), itself built on Inigo Quilez's `sdPolygon`. The bulge is AutoCAD's,
as Lee Mac describes it — https://www.lee-mac.com/bulgeconversion.html. The
code here is written anew: it decides inside or outside by the chords'
crossings and the arcs' circle segments, and finds the nearest point on an
arc without turning the point into the arc's frame.

## Light, glow and shadow

`light` gathers techniques from these, each written anew in PyShader:

- "2D signed distance" on Shadertoy (https://www.shadertoy.com/view/4dfXDn):
  2D lights with a range falloff, soft shadows marched through a distance
  field, occlusion from the distance (`falloff_range`, `occlusion`, the docs'
  soft-shadow example).
- "Drop shadow of round rect" (https://www.shadertoy.com/view/NtVSW1): a
  shadow from a shape's distance (`drop_shadow`, here with a Gaussian's erf
  edge instead of a sigmoid).
- Tim Gott, "Neon" (https://timgott.github.io/neon): a line light as a sum of
  inverse-square point lights in closed form (`segment_light`, derived here
  again with a softening radius).
- Evan Wallace, "Fast Rounded Rectangle Shadows" (CC0) —
  https://madebyevan.com/shaders/fast-rounded-rectangle-shadows/ (`box_shadow`, `erf`).
- Inigo Quilez, "soft shadows in raymarched SDFs" —
  https://iquilezles.org/articles/rmshadows/ (`soft_shadow_step`).
- Sean Voisen, "Re-creating the 'breathing' LED" (2011): the exp(sin) curve (`breathe`).
- "Coffee & Tablet" by P_Malin (https://www.shadertoy.com/view/lssGzn):
  1 - exp2(-c) tone mapping (`tonemap_exposure`); Krzysztof Narkowicz, "ACES
  Filmic Tone Mapping Curve" —
  https://knarkowicz.wordpress.com/2016/01/06/aces-filmic-tone-mapping-curve/ (`tonemap_aces`).
- "Rotating Sphere" (https://www.shadertoy.com/view/4sj3zy): a flat disk lit
  as a ball (`sphere_normal` and the shading with it); Blinn-Phong; Christophe
  Schlick's Fresnel approximation (`fresnel`).

## Simplex noise: Ashima Arts and Stefan Gustavson

`noise.simplex_noise` and `noise.simplex_noise3`, from "webgl-noise" by Ian
McEwan (Ashima Arts) and Stefan Gustavson —
https://github.com/ashima/webgl-noise. Simplex noise itself is by Ken Perlin.

> Copyright (C) 2011 by Ashima Arts (Simplex noise)
> Copyright (C) 2011-2016 by Stefan Gustavson (Classic noise and others)
>
> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Hash without Sine: Dave Hoskins

`random.hash11` … `random.hash33` — https://www.shadertoy.com/view/4djSRW

> MIT License. Copyright (c) 2014 David Hoskins.
>
> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Others

- Golan Levin's shaping functions (`shaping`: seats, sigmoids, circular and
  Bézier curves) — https://www.flong.com/archive/texts/code/
- Robert Penner's easing equations (`easing`) — http://robertpenner.com/easing/ ,
  in the closed forms of Warren Moore's AHEasing — https://github.com/warrenm/AHEasing
- Sam Hocevar, branchless RGB to HSV (`color.rgb_to_hsb`) —
  https://lolengine.net/blog/2013/07/27/rgb-to-hsv-in-glsl
- W3C "Compositing and Blending Level 1" (`blend`) —
  https://www.w3.org/TR/compositing-1/#blending
- Steven Worley, "A Cellular Texture Basis Function", SIGGRAPH 1996 (`cellular`)
- Alan H. Barr, "Global and Local Deformations of Solid Primitives",
  SIGGRAPH 1984 (`vertex.deform`: twist, bend)
- Song Ho Ahn, "OpenGL Projection Matrix" (`vertex.transform`) —
  http://www.songho.ca/opengl/gl_projectionmatrix.html
- Sébastien Truchet, 1704 (`pattern.truchet`)
