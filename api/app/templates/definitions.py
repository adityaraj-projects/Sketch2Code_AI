"""
Every template is built directly as IR (the same Program/Stmt/Expr
classes from app.codegen.ir), not as a JSON blob of hand-placed shapes.
That means:
  - positions are never hand-computed — FlowchartLayout (Feature 3)
    lays every template out fresh, the same tested engine used
    everywhere else in the app.
  - the "DSA basics" templates are real, runnable algorithms — they can
    be (and are, in tests) executed by the real interpreter to verify
    they compute the correct answer, not just that they look plausible.

A few templates (sorting/searching over arrays, OS/networking/compiler
diagrams) use array indexing or purely conceptual steps that this tool's
scalar-only expression model can't actually execute — those are marked
`executable=False` and use RawExpr/Comment nodes for their illustrative
steps. The flowchart structure (branches, loops) is still real and
correct; only step-by-step numeric simulation is out of scope for them,
and that's surfaced to the user rather than hidden.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.codegen.ir import (
    Assignment,
    BinOp,
    BoolLiteral,
    Comment,
    Identifier,
    If,
    Input,
    NumberLiteral,
    Output,
    Program,
    RawExpr,
    StringLiteral,
    While,
)


@dataclass
class TemplateMeta:
    id: str
    name: str
    category: str
    description: str
    executable: bool
    builder: Callable[[], Program]


def _n(value: float) -> NumberLiteral:
    return NumberLiteral(value=value, is_float=False)


def factorial_program() -> Program:
    return Program(body=[
        Input(target="n", prompt="Enter a number"),
        Assignment(target="fact", value=_n(1)),
        Assignment(target="i", value=_n(1)),
        While(
            condition=BinOp("<=", Identifier("i"), Identifier("n")),
            body=[
                Assignment(target="fact", value=BinOp("*", Identifier("fact"), Identifier("i"))),
                Assignment(target="i", value=BinOp("+", Identifier("i"), _n(1))),
            ],
        ),
        Output(value=Identifier("fact")),
    ])


def fibonacci_program() -> Program:
    return Program(body=[
        Input(target="n", prompt="How many terms?"),
        Assignment(target="a", value=_n(0)),
        Assignment(target="b", value=_n(1)),
        Assignment(target="i", value=_n(1)),
        While(
            condition=BinOp("<=", Identifier("i"), Identifier("n")),
            body=[
                Output(value=Identifier("a")),
                Assignment(target="next_val", value=BinOp("+", Identifier("a"), Identifier("b"))),
                Assignment(target="a", value=Identifier("b")),
                Assignment(target="b", value=Identifier("next_val")),
                Assignment(target="i", value=BinOp("+", Identifier("i"), _n(1))),
            ],
        ),
    ])


def gcd_program() -> Program:
    return Program(body=[
        Input(target="a", prompt="Enter first number"),
        Input(target="b", prompt="Enter second number"),
        While(
            condition=BinOp("!=", Identifier("b"), _n(0)),
            body=[
                Assignment(target="temp", value=Identifier("b")),
                Assignment(target="b", value=BinOp("%", Identifier("a"), Identifier("b"))),
                Assignment(target="a", value=Identifier("temp")),
            ],
        ),
        Output(value=Identifier("a")),
    ])


def prime_check_program() -> Program:
    return Program(body=[
        Input(target="n", prompt="Enter a number"),
        Assignment(target="i", value=_n(2)),
        Assignment(target="is_prime", value=BoolLiteral(True)),
        While(
            condition=BinOp("<", Identifier("i"), Identifier("n")),
            body=[
                If(
                    condition=BinOp("==", BinOp("%", Identifier("n"), Identifier("i")), _n(0)),
                    then_body=[Assignment(target="is_prime", value=BoolLiteral(False))],
                    else_body=[],
                ),
                Assignment(target="i", value=BinOp("+", Identifier("i"), _n(1))),
            ],
        ),
        If(
            condition=BinOp("and", Identifier("is_prime"), BinOp(">", Identifier("n"), _n(1))),
            then_body=[Output(value=StringLiteral("Prime"))],
            else_body=[Output(value=StringLiteral("Not Prime"))],
        ),
    ])


def sum_of_digits_program() -> Program:
    return Program(body=[
        Input(target="n", prompt="Enter a number"),
        Assignment(target="total", value=_n(0)),
        While(
            condition=BinOp(">", Identifier("n"), _n(0)),
            body=[
                Assignment(target="digit", value=BinOp("%", Identifier("n"), _n(10))),
                Assignment(target="total", value=BinOp("+", Identifier("total"), Identifier("digit"))),
                Assignment(target="n", value=BinOp("//", Identifier("n"), _n(10))),
            ],
        ),
        Output(value=Identifier("total")),
    ])


def armstrong_check_program() -> Program:
    return Program(body=[
        Input(target="n", prompt="Enter a number"),
        Assignment(target="original", value=Identifier("n")),
        Assignment(target="total", value=_n(0)),
        While(
            condition=BinOp(">", Identifier("n"), _n(0)),
            body=[
                Assignment(target="digit", value=BinOp("%", Identifier("n"), _n(10))),
                Assignment(
                    target="total",
                    value=BinOp("+", Identifier("total"), BinOp("*", BinOp("*", Identifier("digit"), Identifier("digit")), Identifier("digit"))),
                ),
                Assignment(target="n", value=BinOp("//", Identifier("n"), _n(10))),
            ],
        ),
        If(
            condition=BinOp("==", Identifier("total"), Identifier("original")),
            then_body=[Output(value=StringLiteral("Armstrong Number"))],
            else_body=[Output(value=StringLiteral("Not an Armstrong Number"))],
        ),
    ])


def bubble_sort_program() -> Program:
    return Program(body=[
        Comment(text="Read array of n elements"),
        Assignment(target="i", value=_n(0)),
        While(
            condition=RawExpr(text="i < n - 1"),
            body=[
                Assignment(target="j", value=_n(0)),
                While(
                    condition=RawExpr(text="j < n - i - 1"),
                    body=[
                        If(
                            condition=RawExpr(text="arr[j] > arr[j+1]"),
                            then_body=[Comment(text="Swap arr[j] and arr[j+1]")],
                            else_body=[],
                        ),
                        Assignment(target="j", value=BinOp("+", Identifier("j"), _n(1))),
                    ],
                ),
                Assignment(target="i", value=BinOp("+", Identifier("i"), _n(1))),
            ],
        ),
        Comment(text="Array is now sorted"),
    ])


def selection_sort_program() -> Program:
    return Program(body=[
        Comment(text="Read array of n elements"),
        Assignment(target="i", value=_n(0)),
        While(
            condition=RawExpr(text="i < n - 1"),
            body=[
                Assignment(target="min_index", value=Identifier("i")),
                Assignment(target="j", value=BinOp("+", Identifier("i"), _n(1))),
                While(
                    condition=RawExpr(text="j < n"),
                    body=[
                        If(
                            condition=RawExpr(text="arr[j] < arr[min_index]"),
                            then_body=[Assignment(target="min_index", value=Identifier("j"))],
                            else_body=[],
                        ),
                        Assignment(target="j", value=BinOp("+", Identifier("j"), _n(1))),
                    ],
                ),
                Comment(text="Swap arr[i] and arr[min_index]"),
                Assignment(target="i", value=BinOp("+", Identifier("i"), _n(1))),
            ],
        ),
    ])


def linear_search_program() -> Program:
    return Program(body=[
        Comment(text="Read array of n elements"),
        Input(target="key", prompt="Value to search for"),
        Assignment(target="i", value=_n(0)),
        Assignment(target="found", value=BoolLiteral(False)),
        While(
            condition=RawExpr(text="i < n and not found"),
            body=[
                If(
                    condition=RawExpr(text="arr[i] == key"),
                    then_body=[Assignment(target="found", value=BoolLiteral(True))],
                    else_body=[],
                ),
                Assignment(target="i", value=BinOp("+", Identifier("i"), _n(1))),
            ],
        ),
        If(
            condition=Identifier("found"),
            then_body=[Output(value=StringLiteral("Found"))],
            else_body=[Output(value=StringLiteral("Not Found"))],
        ),
    ])


def binary_search_program() -> Program:
    return Program(body=[
        Comment(text="Read sorted array of n elements"),
        Input(target="key", prompt="Value to search for"),
        Assignment(target="low", value=_n(0)),
        Assignment(target="high", value=RawExpr(text="n - 1")),
        Assignment(target="found", value=BoolLiteral(False)),
        While(
            condition=RawExpr(text="low <= high and not found"),
            body=[
                Assignment(target="mid", value=RawExpr(text="(low + high) // 2")),
                If(
                    condition=RawExpr(text="arr[mid] == key"),
                    then_body=[Assignment(target="found", value=BoolLiteral(True))],
                    else_body=[
                        If(
                            condition=RawExpr(text="arr[mid] < key"),
                            then_body=[Assignment(target="low", value=BinOp("+", Identifier("mid"), _n(1)))],
                            else_body=[Assignment(target="high", value=BinOp("-", Identifier("mid"), _n(1)))],
                        )
                    ],
                ),
            ],
        ),
        If(
            condition=Identifier("found"),
            then_body=[Output(value=StringLiteral("Found"))],
            else_body=[Output(value=StringLiteral("Not Found"))],
        ),
    ])


def fcfs_scheduling_program() -> Program:
    return Program(body=[
        Comment(text="Read n processes with arrival & burst times"),
        Comment(text="Sort processes by arrival time"),
        Assignment(target="i", value=_n(0)),
        While(
            condition=RawExpr(text="i < n"),
            body=[
                Comment(text="Completion time = start time + burst time"),
                Comment(text="Waiting time = start time - arrival time"),
                Assignment(target="i", value=BinOp("+", Identifier("i"), _n(1))),
            ],
        ),
        Output(value=StringLiteral("Average waiting time computed")),
    ])


def tcp_handshake_program() -> Program:
    return Program(body=[
        Comment(text="Client sends SYN"),
        Comment(text="Server receives SYN"),
        Comment(text="Server sends SYN-ACK"),
        Comment(text="Client receives SYN-ACK"),
        Comment(text="Client sends ACK"),
        Comment(text="Server receives ACK"),
        Output(value=StringLiteral("Connection established")),
    ])


def compiler_phases_program() -> Program:
    return Program(body=[
        Comment(text="Source code"),
        Comment(text="Lexical Analysis — tokenize source"),
        Comment(text="Syntax Analysis — build parse tree"),
        Comment(text="Semantic Analysis — type/scope checking"),
        Comment(text="Intermediate Code Generation"),
        Comment(text="Code Optimization"),
        Comment(text="Target Code Generation"),
        Output(value=StringLiteral("Executable output")),
    ])


def login_flow_program() -> Program:
    return Program(body=[
        Input(target="username", prompt="Enter username"),
        Input(target="password", prompt="Enter password"),
        Comment(text="Query database for username"),
        If(
            condition=RawExpr(text="user exists"),
            then_body=[
                If(
                    condition=RawExpr(text="password matches"),
                    then_body=[Output(value=StringLiteral("Login successful"))],
                    else_body=[Output(value=StringLiteral("Incorrect password"))],
                )
            ],
            else_body=[Output(value=StringLiteral("User not found"))],
        ),
    ])


TEMPLATE_REGISTRY: list[TemplateMeta] = [
    TemplateMeta("factorial", "Factorial of a Number", "DSA Basics", "Iterative factorial using a while loop.", True, factorial_program),
    TemplateMeta("fibonacci", "Fibonacci Series", "DSA Basics", "Prints the first n Fibonacci numbers.", True, fibonacci_program),
    TemplateMeta("gcd", "GCD (Euclidean Algorithm)", "DSA Basics", "Greatest common divisor of two numbers.", True, gcd_program),
    TemplateMeta("prime_check", "Prime Number Check", "DSA Basics", "Checks whether a number is prime.", True, prime_check_program),
    TemplateMeta("sum_of_digits", "Sum of Digits", "DSA Basics", "Adds up the digits of a number.", True, sum_of_digits_program),
    TemplateMeta("armstrong", "Armstrong Number Check", "DSA Basics", "Checks whether a number is an Armstrong number.", True, armstrong_check_program),
    TemplateMeta("bubble_sort", "Bubble Sort", "Sorting Algorithms", "Classic bubble sort structure.", False, bubble_sort_program),
    TemplateMeta("selection_sort", "Selection Sort", "Sorting Algorithms", "Classic selection sort structure.", False, selection_sort_program),
    TemplateMeta("linear_search", "Linear Search", "Searching Algorithms", "Scans each element for a match.", False, linear_search_program),
    TemplateMeta("binary_search", "Binary Search", "Searching Algorithms", "Halves the search range each step.", False, binary_search_program),
    TemplateMeta("fcfs_scheduling", "FCFS Process Scheduling", "Operating Systems", "First-come-first-served CPU scheduling.", False, fcfs_scheduling_program),
    TemplateMeta("tcp_handshake", "TCP Three-Way Handshake", "Networking", "SYN / SYN-ACK / ACK connection setup.", False, tcp_handshake_program),
    TemplateMeta("compiler_phases", "Phases of a Compiler", "Compiler Design", "Source code to executable, phase by phase.", False, compiler_phases_program),
    TemplateMeta("login_flow", "Login / Authentication Flow", "Database", "A typical username/password check against a database.", False, login_flow_program),
]


def get_template(template_id: str) -> TemplateMeta | None:
    return next((t for t in TEMPLATE_REGISTRY if t.id == template_id), None)
