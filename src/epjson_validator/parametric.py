"""Parametric expansion for epJSON inputs."""

from __future__ import annotations

import ast
import copy
import math
import re
from dataclasses import dataclass
from typing import Any

_VAR_PATTERN = re.compile(r"\$[A-Za-z][A-Za-z0-9_]*")
_NUMBER_PATTERN = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_YES_VALUES = {"yes", "true", "1"}
_ALLOWED_FUNCTIONS = {
    "ABS": abs,
    "COS": math.cos,
    "EXP": math.exp,
    "LOG": math.log,
    "MAX": max,
    "MIN": min,
    "SIN": math.sin,
    "SQRT": math.sqrt,
    "TAN": math.tan,
}
_ALLOWED_CONSTANTS = {
    "PI": math.pi,
}


class ParametricExpansionError(ValueError):
    """Raised when parametric inputs cannot be expanded."""


@dataclass(slots=True)
class ParametricExpansionResult:
    data: dict[str, Any]
    run_index: int | None
    available_runs: int
    enabled_runs: tuple[int, ...]
    expanded: bool


def expand_parametric_data(
    data: dict[str, Any],
    *,
    run_index: int | None = None,
) -> ParametricExpansionResult:
    if not _has_parametric_objects(data):
        return ParametricExpansionResult(
            data=copy.deepcopy(data),
            run_index=None,
            available_runs=0,
            enabled_runs=(),
            expanded=False,
        )

    available_runs = _determine_run_count(data)
    if available_runs <= 0:
        raise ParametricExpansionError("Parametric objects are present, but no runs were defined.")
    enabled_runs = _enabled_runs(data, available_runs)
    selected_run = _select_run(run_index, enabled_runs, available_runs)
    variables = _build_run_variables(data, selected_run)
    _execute_logic(data, variables)

    expanded = copy.deepcopy(data)
    _replace_placeholders(expanded, variables)
    return ParametricExpansionResult(
        data=expanded,
        run_index=selected_run,
        available_runs=available_runs,
        enabled_runs=enabled_runs,
        expanded=True,
    )


def _has_parametric_objects(data: dict[str, Any]) -> bool:
    return any(
        category in data
        for category in (
            "Parametric:Logic",
            "Parametric:RunControl",
            "Parametric:SetValueForRun",
        )
    )


def _determine_run_count(data: dict[str, Any]) -> int:
    counts: list[int] = []
    run_control = data.get("Parametric:RunControl", {})
    if isinstance(run_control, dict):
        for control in run_control.values():
            runs = control.get("runs")
            if isinstance(runs, list):
                counts.append(len(runs))

    set_value = data.get("Parametric:SetValueForRun", {})
    if isinstance(set_value, dict):
        for parameter in set_value.values():
            values = parameter.get("values")
            if isinstance(values, list):
                counts.append(len(values))

    return max(counts, default=0)


def _enabled_runs(data: dict[str, Any], available_runs: int) -> tuple[int, ...]:
    statuses: dict[int, bool] = {}
    run_control = data.get("Parametric:RunControl", {})
    if isinstance(run_control, dict):
        for control in run_control.values():
            runs = control.get("runs")
            if not isinstance(runs, list):
                continue
            for index, run_data in enumerate(runs, start=1):
                if not isinstance(run_data, dict):
                    continue
                perform_run = str(run_data.get("perform_run", "Yes")).strip().lower()
                statuses[index] = perform_run in _YES_VALUES

    if not statuses:
        return tuple(range(1, available_runs + 1))
    enabled = tuple(index for index in range(1, available_runs + 1) if statuses.get(index, False))
    return enabled


def _select_run(run_index: int | None, enabled_runs: tuple[int, ...], available_runs: int) -> int:
    if run_index is None:
        if enabled_runs:
            return enabled_runs[0]
        return 1
    if run_index < 1 or run_index > available_runs:
        raise ParametricExpansionError(
            f"Parametric run {run_index} is out of range. Available runs: 1..{available_runs}."
        )
    if enabled_runs and run_index not in enabled_runs:
        raise ParametricExpansionError(f"Parametric run {run_index} is disabled by Parametric:RunControl.")
    return run_index


def _build_run_variables(data: dict[str, Any], run_index: int) -> dict[str, Any]:
    variables: dict[str, Any] = {}
    set_value = data.get("Parametric:SetValueForRun", {})
    if not isinstance(set_value, dict):
        return variables
    for parameter_name, parameter_data in set_value.items():
        if not isinstance(parameter_data, dict):
            continue
        if not isinstance(parameter_name, str) or not parameter_name.startswith("$"):
            raise ParametricExpansionError(f"Invalid parametric parameter name: {parameter_name!r}.")
        values = parameter_data.get("values")
        if not isinstance(values, list) or run_index > len(values):
            raise ParametricExpansionError(
                f"Parameter {parameter_name} does not define a value for run {run_index}."
            )
        value_entry = values[run_index - 1]
        if not isinstance(value_entry, dict):
            raise ParametricExpansionError(
                f"Parameter {parameter_name} has an invalid value entry for run {run_index}."
            )
        raw_value = value_entry.get("value_for_run")
        variables[parameter_name] = _coerce_run_value(raw_value, variables)
    return variables


def _coerce_run_value(raw_value: Any, variables: dict[str, Any]) -> Any:
    if isinstance(raw_value, (int, float)):
        return raw_value
    if not isinstance(raw_value, str):
        return raw_value
    value = raw_value.strip()
    if _NUMBER_PATTERN.fullmatch(value):
        number = float(value)
        return int(number) if number.is_integer() else number
    if value.startswith("="):
        return _evaluate_expression(value[1:], variables)
    if _looks_like_expression(value):
        return _evaluate_expression(value, variables)
    return value


def _execute_logic(data: dict[str, Any], variables: dict[str, Any]) -> None:
    logic_objects = data.get("Parametric:Logic", {})
    if not isinstance(logic_objects, dict):
        return
    for object_name, object_data in logic_objects.items():
        if not isinstance(object_data, dict):
            continue
        lines = object_data.get("lines")
        if not isinstance(lines, list):
            continue
        for line_data in lines:
            if not isinstance(line_data, dict):
                continue
            raw_line = line_data.get("parametric_logic_line")
            if not isinstance(raw_line, str):
                continue
            line = raw_line.strip()
            if not line:
                continue
            if line.upper().startswith("PARAMETER "):
                parameter_name = line[10:].strip()
                if not _VAR_PATTERN.fullmatch(parameter_name):
                    raise ParametricExpansionError(
                        f"Invalid PARAMETER declaration {parameter_name!r} in Parametric:Logic {object_name}."
                    )
                variables.setdefault(parameter_name, None)
                continue
            if "=" not in line:
                raise ParametricExpansionError(
                    f"Unsupported Parametric:Logic line {line!r} in {object_name}."
                )
            target, expression = line.split("=", 1)
            target_name = target.strip()
            if not _VAR_PATTERN.fullmatch(target_name):
                raise ParametricExpansionError(
                    f"Invalid parametric assignment target {target_name!r} in {object_name}."
                )
            variables[target_name] = _evaluate_expression(expression.strip(), variables)


def _replace_placeholders(node: Any, variables: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        for key, value in list(node.items()):
            node[key] = _replace_placeholders(value, variables)
        return node
    if isinstance(node, list):
        for index, value in enumerate(node):
            node[index] = _replace_placeholders(value, variables)
        return node
    if isinstance(node, str):
        value = node.strip()
        if value.startswith("="):
            return _evaluate_expression(value[1:], variables)
    return node


def _looks_like_expression(value: str) -> bool:
    if "$" in value:
        return True
    if any(token in value for token in ("+", "-", "*", "/", "(", ")")):
        return True
    upper = value.upper()
    return any(f"{name}(" in upper for name in _ALLOWED_FUNCTIONS)


def _evaluate_expression(expression: str, variables: dict[str, Any]) -> Any:
    substituted = _substitute_variables(expression)
    try:
        parsed = ast.parse(substituted, mode="eval")
    except SyntaxError as exc:
        raise ParametricExpansionError(f"Invalid parametric expression {expression!r}.") from exc
    evaluator = _ExpressionEvaluator(variables)
    return evaluator.visit(parsed.body)


def _substitute_variables(expression: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        return _python_var_name(match.group(0))

    return _VAR_PATTERN.sub(_replace, expression)


def _python_var_name(variable_name: str) -> str:
    return f"__param_{variable_name[1:]}"


class _ExpressionEvaluator(ast.NodeVisitor):
    def __init__(self, variables: dict[str, Any]) -> None:
        self.variables = variables

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left**right
        raise ParametricExpansionError("Unsupported operator in parametric expression.")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ParametricExpansionError("Unsupported unary operator in parametric expression.")

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ParametricExpansionError("Unsupported function call in parametric expression.")
        function_name = node.func.id.upper()
        function = _ALLOWED_FUNCTIONS.get(function_name)
        if function is None:
            raise ParametricExpansionError(f"Unsupported parametric function {node.func.id!r}.")
        args = [self.visit(arg) for arg in node.args]
        return function(*args)

    def visit_Name(self, node: ast.Name) -> Any:
        for variable_name, value in self.variables.items():
            if _python_var_name(variable_name) == node.id:
                if value is None:
                    raise ParametricExpansionError(
                        f"Parametric variable {variable_name} was referenced before it was assigned."
                    )
                return value
        constant = _ALLOWED_CONSTANTS.get(node.id.upper())
        if constant is not None:
            return constant
        raise ParametricExpansionError(f"Unknown symbol {node.id!r} in parametric expression.")

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ParametricExpansionError("Only numeric constants are supported in parametric expressions.")

    def generic_visit(self, node: ast.AST) -> Any:
        raise ParametricExpansionError("Unsupported syntax in parametric expression.")
