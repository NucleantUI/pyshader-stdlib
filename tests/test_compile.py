"""Every public function of `sdf` and `light` compiles, called from a shader, for Vulkan
(SPIR-V) and for OpenGL ES 2, through PyShader's compiler (pyshader_builder's
WebAssembly build; PYSHADER_WASM points at another). Where spirv-val and
glslangValidator are installed, what it writes is validated too."""

import ast
import shutil
import subprocess
from pathlib import Path

import pytest
from pyshader_builder._compiler import Compiler

SOURCES = Path(__file__).resolve().parent.parent / "src"
FRAGMENT = SOURCES / "pyshader" / "stdlib" / "fragment"
MODULES = ["sdf", "light"]

# A value of each parameter type, read at run time so nothing folds away.
ARGUMENTS = {
    "float": "(0.5 + 0.1 * sin(time))",
    "int": "5",
    "float2": "float2(0.4, 0.3 + 0.1 * cos(time))",
    "float3": "float3(0.4, 0.3, 0.2 * sin(time))",
    "float4": "float4(0.1, 0.2, 0.3, 0.1 * sin(time))",
    "list[float2]": "CORNERS2",
    "list[float3]": "CORNERS3",
}
RESULTS = {"float": "float4(r)", "float2": "float4(r, 0.0, 1.0)", "float3": "float4(r, 1.0)", "float4": "r"}

SHADER = """\
from pyshader import *
import pyshader.stdlib.fragment.{module} as lib

CORNERS2 = [float2(-0.5, -0.4), float2(0.5, -0.4), float2(0.0, 0.5)]
CORNERS3 = [float3(-0.5, -0.4, 0.0), float3(0.5, -0.4, 0.5), float3(0.0, 0.5, -0.3)]


def main(uv: float2, time: float) -> float4:
    p = uv * 2.0 - 1.0
    r = lib.{name}({args})
    return {result}
"""


def library() -> dict[str, str]:
    """The library's modules by dotted name, as the compiler imports them."""
    modules = {}
    for path in sorted((SOURCES / "pyshader" / "stdlib").rglob("*.py")):
        parts = path.relative_to(SOURCES).with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules[".".join(parts)] = path.read_text(encoding="utf-8")
    return modules


def public_functions(module: str) -> list[tuple[str, ast.FunctionDef]]:
    tree = ast.parse((FRAGMENT / f"{module}.py").read_text(encoding="utf-8"))
    return [(module, node) for node in tree.body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")]


def call(module: str, function: ast.FunctionDef) -> str:
    args = [ARGUMENTS[ast.unparse(a.annotation)] for a in function.args.args if a.annotation is not None]
    # The point argument is the pixel's, so the shape is evaluated per pixel.
    names = [a.arg for a in function.args.args]
    if "p" in names:
        args[names.index("p")] = "p"
    assert function.returns is not None
    return SHADER.format(module=module, name=function.name, args=", ".join(args), result=RESULTS[ast.unparse(function.returns)])


@pytest.fixture(scope="module")
def compiler() -> Compiler:
    return Compiler()


FUNCTIONS = [f for module in MODULES for f in public_functions(module)]


@pytest.mark.parametrize("format", ["spirv", "gles2"])
@pytest.mark.parametrize("function", FUNCTIONS, ids=[f"{m}.{f.name}" for m, f in FUNCTIONS])
def test_compiles(compiler, function, format, tmp_path):
    output, vertex = compiler.compile(call(*function), f"target=fragment format={format}", library())
    assert output
    if format == "spirv":
        validate(tmp_path / "shader.spv", output, ["spirv-val", "--target-env", "vulkan1.0"])
    else:
        validate(tmp_path / "shader.frag", output, ["glslangValidator"])
        validate(tmp_path / "shader.vert", vertex, ["glslangValidator"])


def validate(path: Path, data: bytes, command: list[str]) -> None:
    if shutil.which(command[0]) is None:
        return
    path.write_bytes(data)
    run = subprocess.run([*command, str(path)], capture_output=True, text=True)
    assert run.returncode == 0, f"{command[0]}:\n{run.stdout}{run.stderr}\n{data.decode(errors='replace')[:4000]}"
