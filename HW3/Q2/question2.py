from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
from itertools import count
from pathlib import Path
from typing import List


def fraction_from_decimal(text: str) -> Fraction:
    whole, frac = text.split(".")
    return Fraction(int(whole + frac), 10 ** len(frac))


def fraction_from_binary(bits: str) -> Fraction:
    return sum(Fraction(int(bit), 2**index) for index, bit in enumerate(bits, start=1))


def format_fraction(value: Fraction) -> str:
    return f"{value} ({float(value):.10f})"


@dataclass(frozen=True)
class Expr:
    def probability(self) -> Fraction:
        raise NotImplementedError


@dataclass(frozen=True)
class Source(Expr):
    label: str
    p: Fraction

    def probability(self) -> Fraction:
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
class Or(Expr):
    left: Expr
    right: Expr

    def probability(self) -> Fraction:
        p_left = self.left.probability()
        p_right = self.right.probability()
        return p_left + p_right - p_left * p_right

    def __str__(self) -> str:
        return f"({self.left} | {self.right})"


@dataclass(frozen=True)
class Mux(Expr):
    select: Expr
    when_one: Expr
    when_zero: Expr

    def probability(self) -> Fraction:
        p_select = self.select.probability()
        return p_select * self.when_one.probability() + (1 - p_select) * self.when_zero.probability()

    def __str__(self) -> str:
        return f"mux({self.select}, {self.when_one}, {self.when_zero})"


def mux(select: Expr, when_one: Expr, when_zero: Expr) -> Expr:
    return Mux(select, when_one, when_zero)


def expr_gate_count(expr: Expr) -> int:
    if isinstance(expr, (Source, Const)):
        return 0
    if isinstance(expr, Not):
        return 1 + expr_gate_count(expr.inner)
    if isinstance(expr, (And, Or)):
        return 1 + expr_gate_count(expr.left) + expr_gate_count(expr.right)
    if isinstance(expr, Mux):
        return 1 + expr_gate_count(expr.select) + expr_gate_count(expr.when_one) + expr_gate_count(expr.when_zero)
    raise TypeError(type(expr))


def binary_expansion_expr(bits: str) -> Expr:
    half = Source("h", Fraction(1, 2))
    acc: Expr = Const(int(bits[-1]))
    for bit in reversed(bits[:-1]):
        acc = mux(half, Const(int(bit)), acc)
    return acc


def decimal_expansion_expr(digits: str) -> Expr:
    a = Source("a", Fraction(2, 5))
    b = Source("b", Fraction(1, 2))

    p01 = And(And(a, b), b)
    p02 = And(a, b)
    p025 = And(b, b)
    p0125 = And(b, And(b, b))
    p05 = b
    p06 = Not(a)
    p08 = Not(And(a, b))
    p09 = Not(And(And(a, b), b))

    def append_digit(digit: str, suffix: Expr) -> Expr:
        if digit == "0":
            return And(p01, suffix)
        if digit == "1":
            return Not(Or(p08, And(p05, Not(suffix))))
        if digit == "2":
            return Or(p02, And(p0125, suffix))
        if digit == "3":
            return Not(Or(p06, And(p025, Not(suffix))))
        if digit == "4":
            return Not(Or(p05, And(p02, Not(suffix))))
        if digit == "5":
            return Or(p05, And(p02, suffix))
        if digit == "6":
            return Or(p06, And(p025, suffix))
        if digit == "7":
            return Not(Or(p02, And(p0125, Not(suffix))))
        if digit == "8":
            return Or(p08, And(p05, suffix))
        if digit == "9":
            return Or(p09, suffix)
        raise ValueError(f"Unsupported decimal digit '{digit}'")

    acc: Expr = Const(0)
    for digit in reversed(digits):
        acc = append_digit(digit, acc)
    return acc


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

        if isinstance(expr, (And, Or)):
            left = self._compile_expr(expr.left, preferred="a")
            right = self._compile_expr(expr.right, preferred="b")
            name = self._next_name(preferred or expr.__class__.__name__.lower())
            self.initial_lines.append(f"{name}1 0 N")
            self.initial_lines.append(f"{name}0 0 N")
            for left_bit in (0, 1):
                for right_bit in (0, 1):
                    if isinstance(expr, And):
                        out_bit = left_bit & right_bit
                    else:
                        out_bit = left_bit | right_bit
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


def write_model_files(root: Path, stem: str, expr: Expr) -> None:
    model = AleaeBuilder().compile(expr, name=stem)
    (root / f"{stem}.in").write_text("\n".join(model.initial_lines) + "\n", encoding="ascii")
    (root / f"{stem}.r").write_text("\n".join(model.reaction_lines) + "\n", encoding="ascii")


PART_A_TARGETS = ["8881188", "2119209", "5555555"]
PART_B_TARGETS = ["1011111", "1101111", "1010111"]


def print_question2_answer() -> None:
    print("Question 2")
    print("(a)")
    print("Use source probabilities a = 0.4 and b = 0.5.")
    print("Useful derived constants:")
    print("- 0.1 = (a & b) & b")
    print("- 0.2 = a & b")
    print("- 0.3 = ~(a | b)")
    print("- 0.6 = ~a")
    print("- 0.7 = a | b")
    print("- 0.8 = ~(a & b)")
    print("- 0.9 = ~((a & b) & b)")
    print("OR(x, y) is shorthand for ~(~x & ~y), so every construction still uses only AND and NOT.")
    print("Exact synthesized formulas:")
    for digits in PART_A_TARGETS:
        print(f"- 0.{digits}")
        print(f"  {decimal_expansion_expr(digits)}")
    print()
    print("(b)")
    print("Use a single source h = 0.5.")
    print("Recursive binary construction:")
    print("- if the next bit is 0, use h & R")
    print("- if the next bit is 1, use ~(h & ~R)")
    print("where R is the circuit for the remaining suffix bits.")
    print("This gives:")
    for bits in PART_B_TARGETS:
        print(f"- 0.{bits}_2 = {fraction_from_binary(bits)} = {float(fraction_from_binary(bits)):.7f}")
        print(f"  {binary_expansion_expr(bits)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Question 2 helper for HW3.")
    parser.add_argument("--write-models", action="store_true", help="Write q2b_1/q2b_2/q2b_3 Aleae .in/.r files.")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Output directory for generated models.",
    )
    args = parser.parse_args()

    for index, bits in enumerate(PART_B_TARGETS, start=1):
        expr = binary_expansion_expr(bits)
        if args.write_models:
            stem = f"q2b_{index}"
            write_model_files(args.outdir, stem, expr)
    print_question2_answer()


if __name__ == "__main__":
    main()
