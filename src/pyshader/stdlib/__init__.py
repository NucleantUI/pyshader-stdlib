"""PyShader's standard library: PyShader modules for shader code.

    from pyshader.stdlib.fragment.noise import simplex_noise
    from pyshader.stdlib.fragment import shapes      # shapes.circle(...)
    import pyshader.stdlib.vertex.transform as transform

Two levels: `fragment` (per-pixel helpers: shaping, color, shapes, matrices,
patterns, random, noise, cellular noise) and `vertex` (transforms, quads,
coordinate spaces, deformations). Only what a shader uses is compiled into it.

See CREDITS.md for where each technique comes from.
"""
