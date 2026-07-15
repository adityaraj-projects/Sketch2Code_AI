"""
These tests build the same two canonical flowcharts (an if/else "sign
checker" and a while-loop "sum 1..n") and generate real code for all ten
languages. Where a toolchain is available in this environment (Python,
Node, gcc, g++), the generated program is actually compiled/run and its
output is checked against the expected result — not just eyeballed. For
languages without an available toolchain here (Java, C#, Go, Rust, PHP),
we assert on the structural syntax markers that make the output valid in
each language, and the emitter logic itself is already covered by the
shared IR/structurer tests.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from app.codegen.pipeline import generate_code


def sign_checker_flowchart():
    nodes = [
        {"id": "start", "type": "start", "text": "Start"},
        {"id": "in", "type": "input", "text": "Read n"},
        {"id": "dec", "type": "decision", "text": "n > 0"},
        {"id": "t", "type": "process", "text": 'Print "positive"'},
        {"id": "f", "type": "process", "text": 'Print "not positive"'},
        {"id": "end", "type": "end", "text": "End"},
    ]
    edges = [
        {"id": "e1", "fromNodeId": "start", "toNodeId": "in"},
        {"id": "e2", "fromNodeId": "in", "toNodeId": "dec"},
        {"id": "e3", "fromNodeId": "dec", "toNodeId": "t", "label": "yes"},
        {"id": "e4", "fromNodeId": "dec", "toNodeId": "f", "label": "no"},
        {"id": "e5", "fromNodeId": "t", "toNodeId": "end"},
        {"id": "e6", "fromNodeId": "f", "toNodeId": "end"},
    ]
    return nodes, edges


def sum_loop_flowchart():
    nodes = [
        {"id": "start", "type": "start", "text": "Start"},
        {"id": "init_i", "type": "process", "text": "i = 1"},
        {"id": "init_sum", "type": "process", "text": "sum = 0"},
        {"id": "dec", "type": "decision", "text": "i <= 5"},
        {"id": "add", "type": "process", "text": "sum = sum + i"},
        {"id": "inc", "type": "process", "text": "i = i + 1"},
        {"id": "out", "type": "output", "text": "Print sum"},
        {"id": "end", "type": "end", "text": "End"},
    ]
    edges = [
        {"id": "e1", "fromNodeId": "start", "toNodeId": "init_i"},
        {"id": "e2", "fromNodeId": "init_i", "toNodeId": "init_sum"},
        {"id": "e3", "fromNodeId": "init_sum", "toNodeId": "dec"},
        {"id": "e4", "fromNodeId": "dec", "toNodeId": "add", "label": "yes"},
        {"id": "e5", "fromNodeId": "add", "toNodeId": "inc"},
        {"id": "e6", "fromNodeId": "inc", "toNodeId": "dec"},
        {"id": "e7", "fromNodeId": "dec", "toNodeId": "out", "label": "no"},
        {"id": "e8", "fromNodeId": "out", "toNodeId": "end"},
    ]
    return nodes, edges


def run(cmd, cwd=None, input_text=None):
    return subprocess.run(
        cmd, cwd=cwd, input=input_text, capture_output=True, text=True, timeout=15
    )


# --- Python: actually run it -------------------------------------------

def test_python_sign_checker_runs_correctly():
    nodes, edges = sign_checker_flowchart()
    result = generate_code(nodes, edges, "python")
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "prog.py"
        f.write_text(result.code)
        proc = run([sys.executable, str(f)], input_text="7\n")
        assert proc.returncode == 0, proc.stderr
        assert "positive" in proc.stdout
        assert "not positive" not in proc.stdout


def test_python_sum_loop_runs_correctly():
    nodes, edges = sum_loop_flowchart()
    result = generate_code(nodes, edges, "python")
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "prog.py"
        f.write_text(result.code)
        proc = run([sys.executable, str(f)])
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == "15"  # 1+2+3+4+5


# --- JavaScript: actually run it with node ------------------------------

def test_javascript_sum_loop_runs_correctly():
    nodes, edges = sum_loop_flowchart()
    result = generate_code(nodes, edges, "javascript")
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "prog.js"
        # Swap the prompt-sync input helper for a no-op since this
        # flowchart never calls Input, so no dependency install is needed.
        f.write_text(result.code.replace('require("prompt-sync")()', "() => \"0\""))
        proc = run(["node", str(f)], cwd=tmp)
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == "15"


# --- C: actually compile and run with gcc --------------------------------

def test_c_sum_loop_compiles_and_runs():
    nodes, edges = sum_loop_flowchart()
    result = generate_code(nodes, edges, "c")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "prog.c"
        binary = Path(tmp) / "prog"
        src.write_text(result.code)
        compile_proc = run(["gcc", str(src), "-o", str(binary)])
        assert compile_proc.returncode == 0, compile_proc.stderr
        run_proc = run([str(binary)])
        assert run_proc.returncode == 0
        assert run_proc.stdout.strip() == "15"


def test_c_sign_checker_compiles_and_runs():
    nodes, edges = sign_checker_flowchart()
    result = generate_code(nodes, edges, "c")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "prog.c"
        binary = Path(tmp) / "prog"
        src.write_text(result.code)
        compile_proc = run(["gcc", str(src), "-o", str(binary)])
        assert compile_proc.returncode == 0, compile_proc.stderr
        run_proc = run([str(binary)], input_text="7\n")
        assert "positive" in run_proc.stdout


# --- C++: actually compile and run with g++ -------------------------------

def test_cpp_sum_loop_compiles_and_runs():
    nodes, edges = sum_loop_flowchart()
    result = generate_code(nodes, edges, "cpp")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "prog.cpp"
        binary = Path(tmp) / "prog"
        src.write_text(result.code)
        compile_proc = run(["g++", str(src), "-o", str(binary), "-std=c++17"])
        assert compile_proc.returncode == 0, compile_proc.stderr
        run_proc = run([str(binary)])
        assert run_proc.stdout.strip() == "15"


# --- Java: real javac/java aren't available in this sandbox, but a real
# JRE is — sanity-check brace balance and required constructs structurally.

@pytest.mark.parametrize("flow", [sign_checker_flowchart, sum_loop_flowchart])
def test_java_output_is_well_formed(flow):
    nodes, edges = flow()
    result = generate_code(nodes, edges, "java")
    code = result.code
    assert code.count("{") == code.count("}")
    assert "public class Main" in code
    assert "public static void main(String[] args)" in code
    assert code.strip().endswith("}")


# --- Go / Rust / C# / PHP: no toolchain in this sandbox — structural checks

def test_go_output_is_well_formed():
    nodes, edges = sum_loop_flowchart()
    result = generate_code(nodes, edges, "go")
    code = result.code
    assert code.count("{") == code.count("}")
    assert code.startswith("package main")
    assert 'import "fmt"' in code
    assert "func main() {" in code
    assert "for " in code  # while-loops compile to Go's `for`


def test_rust_output_is_well_formed():
    nodes, edges = sum_loop_flowchart()
    result = generate_code(nodes, edges, "rust")
    code = result.code
    assert code.count("{") == code.count("}")
    assert "fn main() {" in code
    assert "let mut" in code
    assert "while " in code


def test_csharp_output_is_well_formed():
    nodes, edges = sign_checker_flowchart()
    result = generate_code(nodes, edges, "csharp")
    code = result.code
    assert code.count("{") == code.count("}")
    assert "class Program" in code
    assert "static void Main(string[] args)" in code


def test_php_output_is_well_formed():
    nodes, edges = sign_checker_flowchart()
    result = generate_code(nodes, edges, "php")
    code = result.code
    assert code.count("{") == code.count("}")
    assert code.startswith("<?php")
    assert "$n" in code  # variables get a $ sigil


def test_typescript_output_is_well_formed():
    nodes, edges = sum_loop_flowchart()
    result = generate_code(nodes, edges, "typescript")
    code = result.code
    assert code.count("{") == code.count("}")
    assert "let sum: number" in code
    assert "function main(): void" in code


def test_unsupported_language_raises():
    nodes, edges = sign_checker_flowchart()
    with pytest.raises(ValueError):
        generate_code(nodes, edges, "cobol")
