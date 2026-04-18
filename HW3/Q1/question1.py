from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from itertools import count
from pathlib import Path
from typing import Dict, List, Sequence


def format_fraction(value: Fraction) -> str:
    return f"{value} ({float(value):.10f})"


@dataclass(frozen=True)
class Expr:
    def probability(self) -> Fraction:
        raise NotImplementedError


@dataclass(frozen=True)
class Source(Expr):
    label: str
    p: Fraction | None

    def probability(self) -> Fraction:
        if self.p is None:
            raise ValueError(f"Source '{self.label}' is unassigned")
        return self.p

    def __str__(self) -> str:
        return self.label


@dataclass(frozen=True)
class Const(Expr):
    value: int

    def probability(self) -> Fraction:
        return Fraction(self.value, 1)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Not(Expr):
    inner: Expr

    def probability(self) -> Fraction:
        return 1 - self.inner.probability()

    def __str__(self) -> str:
        return f"~({self.inner})"


@dataclass(frozen=True)
class And(Expr):
    left: Expr
    right: Expr

    def probability(self) -> Fraction:
        return self.left.probability() * self.right.probability()

    def __str__(self) -> str:
        return f"({self.left} & {self.right})"


@dataclass(frozen=True)
class Mux(Expr):
    select: Expr
    when_one: Expr
    when_zero: Expr

    def probability(self) -> Fraction:
        p_select = self.select.probability()
        p_when_one = self.when_one.probability()
        p_when_zero = self.when_zero.probability()
        return p_select * p_when_one + (1 - p_select) * p_when_zero

    def __str__(self) -> str:
        return f"mux({self.select}, {self.when_one}, {self.when_zero})"


def mux(select: Expr, when_one: Expr, when_zero: Expr) -> Expr:
    return Mux(select, when_one, when_zero)


def bernstein_expr(coeffs: Sequence[Fraction], source_name: str = "x") -> Expr:
    if len(coeffs) == 1:
        value = coeffs[0]
        if value in (0, 1):
            return Const(int(value))
        return Source(f"c_{value.numerator}_{value.denominator}", value)

    x = Source(source_name, None)
    return mux(x, bernstein_expr(coeffs[1:], source_name), bernstein_expr(coeffs[:-1], source_name))


def q1a_expr() -> Expr:
    x = Source("x", None)
    half_1 = Source("h", Fraction(1, 2))
    half_2 = Source("h", Fraction(1, 2))
    quarter_x = And(half_1, And(half_2, x))
    return And(x, Not(quarter_x))


def assign_sources(expr: Expr, assignments: Dict[str, Fraction]) -> Expr:
    if isinstance(expr, Source):
        if expr.label in assignments:
            return Source(expr.label, assignments[expr.label])
        if expr.p is not None:
            return expr
        raise KeyError(f"Missing assignment for '{expr.label}'")
    if isinstance(expr, Const):
        return expr
    if isinstance(expr, Not):
        return Not(assign_sources(expr.inner, assignments))
    if isinstance(expr, And):
        return And(assign_sources(expr.left, assignments), assign_sources(expr.right, assignments))
    if isinstance(expr, Mux):
        return Mux(
            assign_sources(expr.select, assignments),
            assign_sources(expr.when_one, assignments),
            assign_sources(expr.when_zero, assignments),
        )
    raise TypeError(type(expr))


def expr_gate_count(expr: Expr) -> int:
    if isinstance(expr, (Source, Const)):
        return 0
    if isinstance(expr, Not):
        return 1 + expr_gate_count(expr.inner)
    if isinstance(expr, And):
        return 1 + expr_gate_count(expr.left) + expr_gate_count(expr.right)
    if isinstance(expr, Mux):
        return 1 + expr_gate_count(expr.select) + expr_gate_count(expr.when_one) + expr_gate_count(expr.when_zero)
    raise TypeError(type(expr))


@dataclass
class CompiledWire:
    name: str
    expr: Expr


@dataclass
class AleaeModel:
    initial_lines: List[str]
    reaction_lines: List[str]


class AleaeBuilder:
    def __init__(self, scale: int = 96, rate: int = 1000) -> None:
        self.scale = scale
        self.rate = rate
        self._counter = count(1)
        self.initial_lines: List[str] = []
        self.reaction_lines: List[str] = []

    def compile(self, expr: Expr, name: str) -> AleaeModel:
        self._compile_expr(expr, preferred=name)
        return AleaeModel(self.initial_lines, self.reaction_lines)

    def _next_name(self, stem: str) -> str:
        return f"{stem}_{next(self._counter)}"

    def _compile_expr(self, expr: Expr, preferred: str | None = None) -> CompiledWire:
        if isinstance(expr, Source):
            name = self._next_name(preferred or expr.label)
            ones = round(float(expr.probability()) * self.scale)
            zeros = self.scale - ones
            self.initial_lines.append(f"{name}1 {ones} N")
            self.initial_lines.append(f"{name}0 {zeros} N")
            return CompiledWire(name, expr)

        if isinstance(expr, Const):
            name = self._next_name(preferred or f"const_{expr.value}")
            ones = self.scale if expr.value else 0
            zeros = 0 if expr.value else self.scale
            self.initial_lines.append(f"{name}1 {ones} N")
            self.initial_lines.append(f"{name}0 {zeros} N")
            return CompiledWire(name, expr)

        if isinstance(expr, Not):
            inner = self._compile_expr(expr.inner, preferred="n")
            name = self._next_name(preferred or "not")
            self.initial_lines.append(f"{name}1 0 N")
            self.initial_lines.append(f"{name}0 0 N")
            self.reaction_lines.append(f"{inner.name}1 1 : {name}0 1 : {self.rate}")
            self.reaction_lines.append(f"{inner.name}0 1 : {name}1 1 : {self.rate}")
            return CompiledWire(name, expr)

        if isinstance(expr, And):
            left = self._compile_expr(expr.left, preferred="a")
            right = self._compile_expr(expr.right, preferred="b")
            name = self._next_name(preferred or "and")
            self.initial_lines.append(f"{name}1 0 N")
            self.initial_lines.append(f"{name}0 0 N")
            for left_bit in (0, 1):
                for right_bit in (0, 1):
                    out_bit = left_bit & right_bit
                    self.reaction_lines.append(
                        f"{left.name}{left_bit} 1 {right.name}{right_bit} 1 : {name}{out_bit} 1 : {self.rate}"
                    )
            return CompiledWire(name, expr)

        if isinstance(expr, Mux):
            select = self._compile_expr(expr.select, preferred="s")
            when_one = self._compile_expr(expr.when_one, preferred="a")
            when_zero = self._compile_expr(expr.when_zero, preferred="b")
            name = self._next_name(preferred or "mux")
            self.initial_lines.append(f"{name}1 0 N")
            self.initial_lines.append(f"{name}0 0 N")
            for select_bit in (0, 1):
                for one_bit in (0, 1):
                    for zero_bit in (0, 1):
                        out_bit = one_bit if select_bit else zero_bit
                        self.reaction_lines.append(
                            f"{select.name}{select_bit} 1 {when_one.name}{one_bit} 1 {when_zero.name}{zero_bit} 1 : {name}{out_bit} 1 : {self.rate}"
                        )
            return CompiledWire(name, expr)

        raise TypeError(type(expr))


X_CASES = [
    ("00", Fraction(0, 1)),
    ("025", Fraction(1, 4)),
    ("050", Fraction(1, 2)),
    ("075", Fraction(3, 4)),
    ("100", Fraction(1, 1)),
]


def build_question1_models():
    return (
        ("q1a", q1a_expr(), {"h": Fraction(1, 2)}),
        (
            "q1b",
            bernstein_expr(
                [Fraction(1, 1), Fraction(1, 1), Fraction(11, 12), Fraction(3, 4), Fraction(13, 24)]
            ),
            {},
        ),
        (
            "q1c",
            bernstein_expr(
                [Fraction(1, 2), Fraction(1, 4), Fraction(1, 8), Fraction(1, 16), Fraction(1, 32), Fraction(1, 1)]
            ),
            {},
        ),
    )


def write_case_files(root: Path, stem: str, expr_template: Expr, extra_assignments: Dict[str, Fraction]) -> None:
    reaction_lines: List[str] | None = None
    for suffix, x_value in X_CASES:
        expr = assign_sources(expr_template, {"x": x_value, **extra_assignments})
        model = AleaeBuilder().compile(expr, name=stem)
        (root / f"{stem}_{suffix}.in").write_text("\n".join(model.initial_lines) + "\n", encoding="ascii")
        if reaction_lines is None:
            reaction_lines = model.reaction_lines
            (root / f"{stem}.r").write_text("\n".join(reaction_lines) + "\n", encoding="ascii")


def print_model_summary() -> None:
    descriptions = {
        "q1a": "part (a): f(x) = x - x^2 / 4",
        "q1b": "part (b): cos(x) approximation via degree-4 Bernstein polynomial",
        "q1c": "part (c): Bernstein implementation of the given degree-5 polynomial",
    }
    print("Question 1 from 03.pdf")
    for stem, expr_template, extra_assignments in build_question1_models():
        print(descriptions[stem])
        print(f"  expression: {expr_template}")
        print(f"  gates: {expr_gate_count(expr_template)}")
        for suffix, x_value in X_CASES:
            expr = assign_sources(expr_template, {"x": x_value, **extra_assignments})
            print(f"  x={format_fraction(x_value)} -> {format_fraction(expr.probability())} [{stem}_{suffix}.in]")


def write_models(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for stem, expr_template, extra_assignments in build_question1_models():
        write_case_files(outdir, stem, expr_template, extra_assignments)


def run_aleae(outdir: Path, trials: int, time_limit: int, verbosity: int) -> None:
    aleae = Path(__file__).resolve().parent.parent / "aleae"
    if not aleae.exists():
        raise FileNotFoundError(f"Missing aleae binary at {aleae}")

    for stem, _, _ in build_question1_models():
        reaction_file = outdir / f"{stem}.r"
        for suffix, _ in X_CASES:
            input_file = outdir / f"{stem}_{suffix}.in"
            subprocess.run(
                [str(aleae), str(input_file), str(reaction_file), str(trials), str(time_limit), str(verbosity)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


def sample_rows(expr_template: Expr, extra_assignments: Dict[str, Fraction]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for _, x_value in X_CASES:
        expr = assign_sources(expr_template, {"x": x_value, **extra_assignments})
        rows.append((f"{float(x_value):.2f}", f"{float(expr.probability()):.6f}"))
    return rows


def print_question1_answer() -> None:
    q1a, q1b, q1c = build_question1_models()

    print("Question 1")
    print("(a)")
    print("Use")
    print("f(x) = x - x^2/4 = x(1 - x/4).")
    print("A direct stochastic circuit is:")
    print("1. Split x into a scaled copy x/4 using two successive 1/2 scalers.")
    print("2. Invert that stream to get 1 - x/4.")
    print("3. Feed x and 1 - x/4 into an AND gate.")
    print("This gives the exact target function.")
    print("Equivalent Bernstein form, degree 2:")
    print("f(x) = 0·B_0^2(x) + 1/2·B_1^2(x) + 3/4·B_2^2(x).")
    print("x     f(x)")
    for x_text, y_text in sample_rows(q1a[1], q1a[2]):
        print(f"{x_text}  {y_text}")
    print("Files:")
    print("- q1a.r")
    print("- q1a_00.in")
    print("- q1a_025.in")
    print("- q1a_050.in")
    print("- q1a_075.in")
    print("- q1a_100.in")
    print()

    print("(b)")
    print("Approximate cos(x) on [0, 1] with")
    print("cos(x) ≈ 1 - x^2/2 + x^4/24.")
    print("This stays inside [0, 1] on [0, 1], so it is valid for stochastic synthesis.")
    print("Bernstein form, degree 4:")
    print("p(x) = 1·B_0^4(x) + 1·B_1^4(x) + 11/12·B_2^4(x) + 3/4·B_3^4(x) + 13/24·B_4^4(x).")
    print("x     cos(x) (approx.)")
    for x_text, y_text in sample_rows(q1b[1], q1b[2]):
        print(f"{x_text}  {y_text}")
    print("Files:")
    print("- q1b.r")
    print("- q1b_00.in")
    print("- q1b_025.in")
    print("- q1b_050.in")
    print("- q1b_075.in")
    print("- q1b_100.in")
    print()

    print("(c)")
    print("Given")
    print("p(x) = 31/32 x^5 + 5/32 x^4 - 5/8 x^3 + 5/4 x^2 - 5/4 x + 1/2,")
    print("the Bernstein form is")
    print("p(x) = 1/2·B_0^5(x) + 1/4·B_1^5(x) + 1/8·B_2^5(x) + 1/16·B_3^5(x) + 1/32·B_4^5(x) + 1·B_5^5(x).")
    print("Sample values:")
    for x_text, y_text in sample_rows(q1c[1], q1c[2]):
        print(f"- x = {x_text} -> {y_text}")
    print("Files:")
    print("- q1c.r")
    print("- q1c_00.in")
    print("- q1c_025.in")
    print("- q1c_050.in")
    print("- q1c_075.in")
    print("- q1c_100.in")


def main() -> None:
    parser = argparse.ArgumentParser(description="Question 1 helper for HW3.")
    parser.add_argument("--write-models", action="store_true", help="Write q1a/q1b/q1c Aleae .in/.r files.")
    parser.add_argument("--no-aleae", action="store_true", help="Skip running aleae after generating models.")
    parser.add_argument("--trials", type=int, default=1000, help="Aleae trial count.")
    parser.add_argument("--time-limit", type=int, default=-1, help="Aleae time limit argument.")
    parser.add_argument("--verbosity", type=int, default=0, help="Aleae verbosity argument.")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Output directory for generated models.",
    )
    args = parser.parse_args()

    write_models(args.outdir)
    if not args.no_aleae:
        run_aleae(args.outdir, args.trials, args.time_limit, args.verbosity)
    print_question1_answer()


if __name__ == "__main__":
    main()
