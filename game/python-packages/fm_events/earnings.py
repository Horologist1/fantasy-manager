"""Safe, deterministic payout evaluation for daily stories."""

import ast
import operator


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}
_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_ALLOWED_NAMES = {"skill", "level", "roll"}
_POSITIVE_OUTCOMES = {"success", "critical_success"}


class EarningsFormulaError(ValueError):
    """Raised when a daily-story earnings formula is invalid or unsafe."""


def _evaluate_node(node, environment):
    if isinstance(node, ast.Expression):
        return _evaluate_node(node.body, environment)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise EarningsFormulaError("constants must be numeric")
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in _ALLOWED_NAMES:
            raise EarningsFormulaError("unknown name %r" % node.id)
        return environment[node.id]
    if isinstance(node, ast.BinOp):
        operation = _BINARY_OPERATORS.get(type(node.op))
        if operation is None:
            raise EarningsFormulaError("operator %s is not allowed" % type(node.op).__name__)
        return operation(_evaluate_node(node.left, environment), _evaluate_node(node.right, environment))
    if isinstance(node, ast.UnaryOp):
        operation = _UNARY_OPERATORS.get(type(node.op))
        if operation is None:
            raise EarningsFormulaError("operator %s is not allowed" % type(node.op).__name__)
        return operation(_evaluate_node(node.operand, environment))
    raise EarningsFormulaError("expression %s is not allowed" % type(node).__name__)


def evaluate_earnings_formula(formula, *, skill, level, roll):
    """Evaluate a numeric formula using only arithmetic and known variables."""
    if not isinstance(formula, str) or not formula.strip():
        raise EarningsFormulaError("formula must be a non-empty string")
    try:
        expression = ast.parse(formula, mode="eval")
        value = _evaluate_node(
            expression,
            {"skill": skill, "level": level, "roll": roll},
        )
    except EarningsFormulaError:
        raise
    except Exception as error:
        raise EarningsFormulaError(str(error)) from error
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EarningsFormulaError("formula result must be numeric")
    return int(value)


def _fallback_earnings(outcome, skill):
    skill = max(0, int(skill or 0))
    if outcome == "critical_success":
        return max(1, skill * 2)
    if outcome == "success":
        return max(1, skill)
    if outcome == "mediocre":
        return skill
    return -10


def resolve_story_earnings(story, outcome, *, skill, level, roll):
    """Return ``(earnings, error)`` without silently erasing malformed payouts.

    Stories with no earnings mapping are intentional no-payout activities such
    as rest or training and remain at zero. A present but malformed/missing
    outcome formula receives a deterministic fallback and an error for logging.
    """
    story = story or {}
    earnings = story.get("earnings")
    if not isinstance(earnings, dict):
        return 0, None

    formula = earnings.get(outcome)
    try:
        return evaluate_earnings_formula(
            formula,
            skill=skill,
            level=level,
            roll=roll,
        ), None
    except EarningsFormulaError as error:
        story_id = story.get("id", "<unknown>")
        fallback = _fallback_earnings(outcome, skill)
        message = (
            "daily story %s earnings.%s formula %r failed: %s; fallback=%s"
            % (story_id, outcome, formula, error, fallback)
        )
        return fallback, message


def protect_positive_payout(outcome, *, base_earnings, final_earnings):
    """Keep a valid positive success payout from becoming zero downstream."""
    final_earnings = int(final_earnings)
    if outcome in _POSITIVE_OUTCOMES and base_earnings > 0 and final_earnings <= 0:
        return max(1, int(base_earnings)), True
    return final_earnings, False
