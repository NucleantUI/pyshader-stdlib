"""The examples compile, for Vulkan (SPIR-V) and for OpenGL ES 2, against the
library as it is here, and what they compile to validates where spirv-val and
glslangValidator are installed."""

import ast
from pathlib import Path

import pytest
from pyshader_builder._compiler import Compiler

from test_compile import library, validate

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def fragment_examples() -> list[Path]:
    """The examples with a `main`: the fragment target's (spinning_quads is a graphics target's)."""
    return [path for path in sorted(EXAMPLES.glob("*.py"))
            if any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in ast.parse(path.read_text(encoding="utf-8")).body)]


@pytest.fixture(scope="module")
def compiler() -> Compiler:
    return Compiler()


@pytest.mark.parametrize("format", ["spirv", "gles2"])
@pytest.mark.parametrize("example", fragment_examples(), ids=lambda p: p.stem)
def test_example_compiles(compiler, example, format, tmp_path):
    output, vertex = compiler.compile(example.read_text(encoding="utf-8"), f"target=fragment format={format}", library())
    assert output
    if format == "spirv":
        validate(tmp_path / "shader.spv", output, ["spirv-val", "--target-env", "vulkan1.0"])
    else:
        validate(tmp_path / "shader.frag", output, ["glslangValidator"])
        validate(tmp_path / "shader.vert", vertex, ["glslangValidator"])
