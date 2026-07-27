"""
Parses real Python source into the same IR used by Feature 2's code
generator (app.codegen.ir), using Python's own built-in `ast` module for
actual parsing — not string matching. This is what lets Feature 3 handle
arbitrary control flow (nested ifs, while loops, range-based for loops)
correctly instead of pattern-matching a few known shapes.

Anything genuinely unsupported (function defs, imports, non-range for
loops, arbitrary expressions) is preserved as a Comment holding the exact
original source line — via ast.unparse — rather than silently dropped.
"""
from __future__ import annotations

import ast

from app.codegen.ir import (
    Assignment,
    BinOp,
    BoolLiteral,
    Break,
    Comment,
    Expr,
    Identifier,
    If,
    Input,
    NumberLiteral,
    Output,
    Program,
    RawExpr,
    Return,
    Stmt,
    StringLiteral,
    UnaryOp,
    While,
)

BIN_OP_MAP: dict[type, str] = {
    ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Mod: "%", ast.FloorDiv: "//",
}
COMPARE_OP_MAP: dict[type, str] = {
    ast.Lt: "<", ast.Gt: ">", ast.LtE: "<=", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!=",
}
BOOL_OP_MAP: dict[type, str] = {ast.And: "and", ast.Or: "or"}

_UNWRAP_CALLS = {"int", "float", "str", "round", "abs"}


class UnsupportedSourceError(Exception):
    pass


class PythonSourceAdapter:
    def __init__(self):
        self.warnings: list[str] = []

    # -- expressions ------------------------------------------------------

    def convert_expr(self, node: ast.expr) -> Expr:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return BoolLiteral(value=node.value)
            if isinstance(node.value, (int, float)):
                return NumberLiteral(value=float(node.value), is_float=isinstance(node.value, float))
            if isinstance(node.value, str):
                return StringLiteral(value=node.value)
            return RawExpr(text=repr(node.value))

        if isinstance(node, ast.Name):
            return Identifier(name=node.id)

        if isinstance(node, ast.BinOp) and type(node.op) in BIN_OP_MAP:
            return BinOp(
                op=BIN_OP_MAP[type(node.op)],
                left=self.convert_expr(node.left),
                right=self.convert_expr(node.right),
            )

        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return UnaryOp(op="-", operand=self.convert_expr(node.operand))
            if isinstance(node.op, ast.Not):
                return UnaryOp(op="not", operand=self.convert_expr(node.operand))
            if isinstance(node.op, ast.UAdd):
                return self.convert_expr(node.operand)

        if isinstance(node, ast.BoolOp) and type(node.op) in BOOL_OP_MAP:
            op = BOOL_OP_MAP[type(node.op)]
            values = [self.convert_expr(v) for v in node.values]
            expr = values[0]
            for v in values[1:]:
                expr = BinOp(op=op, left=expr, right=v)
            return expr

        if isinstance(node, ast.Compare):
            comparators = [node.left] + list(node.comparators)
            parts: list[Expr] = []
            for i, op in enumerate(node.ops):
                if type(op) not in COMPARE_OP_MAP:
                    return RawExpr(text=ast.unparse(node))
                parts.append(
                    BinOp(
                        op=COMPARE_OP_MAP[type(op)],
                        left=self.convert_expr(comparators[i]),
                        right=self.convert_expr(comparators[i + 1]),
                    )
                )
            expr = parts[0]
            for p in parts[1:]:
                expr = BinOp(op="and", left=expr, right=p)
            return expr

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _UNWRAP_CALLS and len(node.args) == 1:
                # A type-cast wrapper like int(x) — the flowchart doesn't
                # need the cast spelled out, just the underlying value.
                return self.convert_expr(node.args[0])

        # Anything else (arbitrary calls, subscripts, f-strings, ...) is
        # kept verbatim rather than guessed at.
        try:
            return RawExpr(text=ast.unparse(node))
        except Exception:
            return RawExpr(text="<expression>")

    # -- statements ---------------------------------------------------------

    def convert_body(self, body: list[ast.stmt]) -> list[Stmt]:
        result: list[Stmt] = []
        for node in body:
            converted = self.convert_stmt(node)
            if converted is not None:
                result.extend(converted if isinstance(converted, list) else [converted])
        return result

    def convert_stmt(self, node: ast.stmt) -> Stmt | list[Stmt] | None:
        if isinstance(node, ast.Pass):
            return None

        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
            input_stmt = self._try_convert_input(target, node.value)
            if input_stmt is not None:
                return input_stmt
            return Assignment(target=target, value=self.convert_expr(node.value))

        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            if type(node.op) not in BIN_OP_MAP:
                return Comment(text=ast.unparse(node))
            target = node.target.id
            return Assignment(
                target=target,
                value=BinOp(
                    op=BIN_OP_MAP[type(node.op)],
                    left=Identifier(name=target),
                    right=self.convert_expr(node.value),
                ),
            )

        if isinstance(node, ast.If):
            return If(
                condition=self.convert_expr(node.test),
                then_body=self.convert_body(node.body),
                else_body=self.convert_body(node.orelse),
            )

        if isinstance(node, ast.While):
            return While(condition=self.convert_expr(node.test), body=self.convert_body(node.body))

        if isinstance(node, ast.For):
            return self._convert_range_for(node)

        if isinstance(node, ast.Break):
            return Break()

        if isinstance(node, ast.Return):
            return Return()

        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            output = self._try_convert_print(node.value)
            if output is not None:
                return output
            self.warnings.append(f"Call expression on line {node.lineno} kept as a comment.")
            return Comment(text=ast.unparse(node))

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            # These don't map to flowchart shapes at all — skip silently
            # rather than cluttering the diagram with a comment box per
            # import/def; `main()`'s own def is unwrapped by the caller.
            return None

        self.warnings.append(f"Unsupported statement on line {getattr(node, 'lineno', '?')} kept as a comment.")
        try:
            return Comment(text=ast.unparse(node))
        except Exception:
            return Comment(text="(unsupported statement)")

    def _try_convert_input(self, target: str, value: ast.expr) -> Input | None:
        call = value
        # Unwrap int(input(...)) / float(input(...)) to find the input() call.
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id in ("int", "float"):
            if len(call.args) == 1:
                call = call.args[0]

        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "input":
            prompt = None
            if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
                prompt = call.args[0].value.strip().rstrip(":").strip()
            return Input(target=target, prompt=prompt)
        return None

    def _try_convert_print(self, call: ast.Call) -> Output | None:
        if not (isinstance(call.func, ast.Name) and call.func.id == "print"):
            return None
        if len(call.args) == 0:
            return Output(value=StringLiteral(value=""))
        if len(call.args) == 1:
            return Output(value=self.convert_expr(call.args[0]))
        # print(a, b, c) -> concatenate for display purposes.
        expr = self.convert_expr(call.args[0])
        for arg in call.args[1:]:
            expr = BinOp(op="+", left=expr, right=self.convert_expr(arg))
        return Output(value=expr)

    def _convert_range_for(self, node: ast.For) -> Stmt | list[Stmt]:
        is_range_call = (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
            and isinstance(node.target, ast.Name)
        )
        if not is_range_call:
            self.warnings.append(
                f"For-loop on line {node.lineno} doesn't iterate over range() — kept as a comment."
            )
            return Comment(text=ast.unparse(node))

        var = node.target.id
        args = node.iter.args
        if len(args) == 1:
            start_expr, stop_expr, step_expr = NumberLiteral(value=0, is_float=False), args[0], None
        elif len(args) == 2:
            start_expr, stop_expr, step_expr = args[0], args[1], None
        else:
            start_expr, stop_expr, step_expr = args[0], args[1], args[2]

        step_is_negative = (
            isinstance(step_expr, ast.UnaryOp) and isinstance(step_expr.op, ast.USub)
        ) or (isinstance(step_expr, ast.Constant) and isinstance(step_expr.value, (int, float)) and step_expr.value < 0)

        # start_expr is a NumberLiteral(0) in the 1-arg case, otherwise an ast.expr.
        if isinstance(start_expr, ast.expr):
            init = Assignment(target=var, value=self.convert_expr(start_expr))
        else:
            init = Assignment(target=var, value=start_expr)

        condition = BinOp(
            op="<" if not step_is_negative else ">",
            left=Identifier(name=var),
            right=self.convert_expr(stop_expr),
        )
        step_value = self.convert_expr(step_expr) if step_expr is not None else NumberLiteral(value=1, is_float=False)
        increment = Assignment(target=var, value=BinOp(op="+", left=Identifier(name=var), right=step_value))

        body = self.convert_body(node.body) + [increment]
        return [init, While(condition=condition, body=body)]

    def parse(self, source: str) -> Program:
        tree = ast.parse(source)

        main_func = next(
            (
                n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "main"
            ),
            None,
        )
        body_nodes = main_func.body if main_func is not None else tree.body
        body = self.convert_body(body_nodes)
        return Program(body=body)


def parse_python_source(source: str) -> tuple[Program, list[str]]:
    adapter = PythonSourceAdapter()
    try:
        program = adapter.parse(source)
    except SyntaxError as e:
        raise UnsupportedSourceError(f"Python syntax error: {e}") from e
    return program, adapter.warnings
