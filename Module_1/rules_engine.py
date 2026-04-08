from __future__ import annotations

"""Rule-based inference engine for environmental risk alerts.

This script reads a CSV file, evaluates rules from a JSON knowledge base,
and writes risk/action recommendations for each row.
"""

import argparse
import csv
import json
from collections import defaultdict, deque
from collections import Counter
from pathlib import Path
from typing import Any


RISK_ORDER = {"none": 0, "low": 1, "moderate": 2, "high": 3, "critical": 4}

# Aliases allow rules to use alternate names while still matching CSV columns.
FEATURE_ALIASES = {
	"PM2_5": "PM2.5",
}

RISK_ALIASES = {
	"NORMAL": "none",
	"BAIXO": "low",
	"MODERADO": "moderate",
	"ALTO": "high",
}


def build_city_window() -> deque[float | None]:
	"""Factory for rolling CO windows used by defaultdict.

	This helper exists to avoid lambda usage and keep behavior explicit.
	"""
	return deque(maxlen=8)


def parse_float(value: Any) -> float | None:
	"""Convert raw value to float; return None for empty/invalid values."""
	if value is None:
		return None
	text = str(value).strip()
	if text == "":
		return None
	try:
		return float(text)
	except ValueError:
		return None


def normalize_risk_level(raw_level: str | None) -> str:
	"""Normalize risk labels from different schemas to a shared set."""
	if raw_level is None:
		return "none"
	text = str(raw_level).strip()
	if text == "":
		return "none"
	upper = text.upper()
	if upper in RISK_ALIASES:
		return RISK_ALIASES[upper]
	return text.lower()


def resolve_feature_name(raw_name: str) -> str:
	"""Resolve aliases like PM2_5 to real dataset column names."""
	return FEATURE_ALIASES.get(raw_name, raw_name)


def get_row_value(row: dict[str, str], variable: str) -> float | None:
	"""Read numeric value from row using supported feature aliases."""
	# First try exact variable name (important for derived columns like CO_8h_avg).
	if variable in row:
		value = parse_float(row.get(variable))
		if value is not None:
			return value

	column = resolve_feature_name(variable)
	return parse_float(row.get(column))


def compare_numeric(observed: float, operator: str, threshold: float) -> bool:
	"""Evaluate a numeric comparison in a fully explicit way."""
	if operator == ">":
		return observed > threshold
	if operator == ">=":
		return observed >= threshold
	if operator == "<":
		return observed < threshold
	if operator == "<=":
		return observed <= threshold
	if operator == "==":
		return observed == threshold
	if operator == "!=":
		return observed != threshold
	raise ValueError(f"Unsupported operator: {operator}")


def add_co_8h_average(rows: list[dict[str, str]]) -> None:
	"""Add CO_8h_avg using rolling 8-row window per city (min 6 valid values)."""
	windows: dict[str, deque[float | None]] = defaultdict(build_city_window)

	for row in rows:
		city = row.get("city", "") or "__global__"
		window = windows[city]

		co_value = parse_float(row.get("CO"))
		window.append(co_value)

		valid_values: list[float] = []
		for value in window:
			if value is not None:
				valid_values.append(value)

		if len(valid_values) >= 6:
			row["CO_8h_avg"] = f"{sum(valid_values) / len(valid_values):.6f}"
		else:
			row["CO_8h_avg"] = ""


def evaluate_condition(row: dict[str, str], condition: dict[str, Any]) -> bool:
	"""Check one simple comparison condition against one CSV row."""
	feature = condition["feature"]
	operator = condition["operator"]
	threshold = float(condition["value"])
	observed = get_row_value(row, feature)

	# Missing data cannot satisfy numeric threshold conditions.
	if observed is None:
		return False

	return compare_numeric(observed, operator, threshold)


def evaluate_condition_v2(row: dict[str, str], condition: dict[str, Any]) -> bool:
	"""Evaluate structured conditions (simple threshold, range, AND, OR)."""
	cond_type = condition.get("type")

	if cond_type == "simple_threshold":
		variable = condition["variable"]
		operator = condition.get("operator", ">=")
		threshold_raw = condition.get("threshold", condition.get("value"))
		if threshold_raw is None:
			raise ValueError("simple_threshold condition must define threshold/value")
		threshold = float(threshold_raw)
		observed = get_row_value(row, variable)
		if observed is None:
			return False

		return compare_numeric(observed, operator, threshold)

	if cond_type == "range":
		variable = condition["variable"]
		observed = get_row_value(row, variable)
		if observed is None:
			return False
		min_v = parse_float(condition.get("min"))
		max_v = parse_float(condition.get("max"))
		if min_v is not None and observed < min_v:
			return False
		if max_v is not None and observed >= max_v:
			return False
		return True

	if cond_type == "compound_and":
		children = condition.get("conditions", [])
		for child in children:
			if not evaluate_condition_v2(row, child):
				return False
		return True

	if cond_type == "compound_or":
		children = condition.get("conditions", [])
		for child in children:
			if evaluate_condition_v2(row, child):
				return True
		return False

	# Keep backward compatibility if a legacy condition appears here.
	if "variable" in condition and "operator" in condition and "value" in condition:
		legacy_condition = {
			"feature": condition["variable"],
			"operator": condition["operator"],
			"value": condition["value"],
		}
		return evaluate_condition(row, legacy_condition)

	raise ValueError(f"Unsupported condition type: {cond_type}")


def rule_matches(row: dict[str, str], rule: dict[str, Any]) -> bool:
	"""Check if one rule is true for the current row."""
	if "conditions" in rule:
		# Legacy format: a list where all conditions must be true.
		conditions = rule["conditions"]
		for condition in conditions:
			if not evaluate_condition(row, condition):
				return False
		return True
	if "condition" in rule:
		# Structured format: nested condition tree.
		return evaluate_condition_v2(row, rule["condition"])
	raise ValueError("Rule has neither 'conditions' nor 'condition'")


def load_rules(path: Path) -> list[dict[str, Any]]:
	"""Load and validate the rule list from JSON."""
	with path.open("r", encoding="utf-8") as file:
		payload = json.load(file)

	if isinstance(payload, list):
		return payload
	if isinstance(payload, dict) and isinstance(payload.get("rules"), list):
		return payload["rules"]
	raise ValueError("Rules file must contain a rule list or a dict with key 'rules'.")


def get_rule_id(rule: dict[str, Any]) -> str:
	"""Return rule id, or a safe fallback if missing."""
	return str(rule.get("id", "unknown_rule"))


def get_rule_name(rule: dict[str, Any]) -> str:
	"""Return a human-readable rule name used in outputs."""
	return str(rule.get("name", rule.get("description", get_rule_id(rule))))


def get_rule_priority(rule: dict[str, Any]) -> int:
	"""Return priority used to sort matched rules (higher first)."""
	return int(rule.get("priority", 0))


def get_rule_risk_level(rule: dict[str, Any]) -> str:
	"""Read risk level from either legacy or structured rule format."""
	if "risk_level" in rule:
		return normalize_risk_level(str(rule.get("risk_level")))
	consequence = rule.get("consequence", {})
	if isinstance(consequence, dict):
		return normalize_risk_level(consequence.get("risk_level"))
	return "none"


def get_rule_actions(rule: dict[str, Any]) -> list[str]:
	"""Return action messages from a rule in a consistent list format."""
	if "actions" in rule and isinstance(rule["actions"], list):
		actions: list[str] = []
		for action in rule["actions"]:
			actions.append(str(action))
		return actions
	consequence = rule.get("consequence", {})
	if isinstance(consequence, dict) and consequence.get("action"):
		return [str(consequence["action"])]
	return []


def collect_matched_rules(row: dict[str, str], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""Return every rule that matches the current row."""
	matched: list[dict[str, Any]] = []
	for rule in rules:
		if rule_matches(row, rule):
			matched.append(rule)
	return matched


def sort_rules_by_priority(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""Sort rules by priority in descending order without lambda."""
	def priority_key(rule: dict[str, Any]) -> int:
		return get_rule_priority(rule)

	return sorted(rules, key=priority_key, reverse=True)


def determine_highest_risk(sorted_rules: list[dict[str, Any]]) -> str:
	"""Pick the maximum risk level from matched rules."""
	highest_risk = "none"
	highest_rank = RISK_ORDER.get("none", 0)

	for rule in sorted_rules:
		risk_level = get_rule_risk_level(rule)
		rank = RISK_ORDER.get(risk_level, 0)
		if rank > highest_rank:
			highest_rank = rank
			highest_risk = risk_level

	return highest_risk


def collect_unique_actions(sorted_rules: list[dict[str, Any]]) -> list[str]:
	"""Collect actions in priority order without duplicates."""
	actions: list[str] = []
	seen: set[str] = set()

	for rule in sorted_rules:
		rule_actions = get_rule_actions(rule)
		for action in rule_actions:
			if action not in seen:
				actions.append(action)
				seen.add(action)

	return actions


def join_rule_ids(sorted_rules: list[dict[str, Any]]) -> str:
	"""Join matched rule IDs into a pipe-separated string."""
	rule_ids: list[str] = []
	for rule in sorted_rules:
		rule_ids.append(get_rule_id(rule))
	return "|".join(rule_ids)


def join_rule_names(sorted_rules: list[dict[str, Any]]) -> str:
	"""Join matched rule names into a pipe-separated string."""
	rule_names: list[str] = []
	for rule in sorted_rules:
		rule_names.append(get_rule_name(rule))
	return "|".join(rule_names)


def infer_for_row(row: dict[str, str], rules: list[dict[str, Any]]) -> dict[str, Any]:
	"""Run rule inference for one row and return output fields."""
	matched_rules = collect_matched_rules(row, rules)
	matched_sorted = sort_rules_by_priority(matched_rules)
	overall_risk = determine_highest_risk(matched_sorted)
	actions = collect_unique_actions(matched_sorted)

	return {
		"matched_rule_ids": join_rule_ids(matched_sorted),
		"matched_rule_names": join_rule_names(matched_sorted),
		"overall_risk": overall_risk,
		"recommended_actions": " | ".join(actions),
	}


def run_inference(
	input_csv: Path,
	rules_path: Path,
	output_csv: Path,
	limit: int | None = None,
) -> None:
	"""Run inference for all rows and save enriched output CSV."""
	rules = load_rules(rules_path)
	rule_counter: Counter[str] = Counter()
	risk_counter: Counter[str] = Counter()

	with input_csv.open("r", encoding="utf-8", newline="") as source:
		reader = csv.DictReader(source, delimiter=";")
		raw_rows = list(reader)
		fieldnames = list(reader.fieldnames or [])
		if "CO_8h_avg" not in fieldnames:
			fieldnames.append("CO_8h_avg")

		# Preprocess derived variables before applying rules.
		add_co_8h_average(raw_rows)

		out_fields = fieldnames + [
			"matched_rule_ids",
			"matched_rule_names",
			"overall_risk",
			"recommended_actions",
		]

		rows_to_write: list[dict[str, str]] = []
		processed = 0
		for row in raw_rows:
			# Optional row limit is useful for fast testing.
			if limit is not None and processed >= limit:
				break

			# Compute fields produced by the rule engine for this row.
			result = infer_for_row(row, rules)
			row.update(result)
			rows_to_write.append(row)

			if result["matched_rule_ids"]:
				# Track rule frequency for an execution summary.
				for rule_id in result["matched_rule_ids"].split("|"):
					if rule_id:
						rule_counter[rule_id] += 1
			# Track risk distribution for the same summary.
			risk_counter[result["overall_risk"]] += 1
			processed += 1

	output_csv.parent.mkdir(parents=True, exist_ok=True)
	with output_csv.open("w", encoding="utf-8", newline="") as sink:
		writer = csv.DictWriter(sink, fieldnames=out_fields, delimiter=";")
		writer.writeheader()
		writer.writerows(rows_to_write)

	print(f"Processed rows: {processed}")
	print(f"Output written to: {output_csv}")
	# Print a small execution summary for report/debug usage.
	print("Risk distribution:")

	def risk_sort_key(item: tuple[str, int]) -> int:
		risk_level = item[0]
		return RISK_ORDER.get(risk_level, -1)

	for risk, count in sorted(risk_counter.items(), key=risk_sort_key, reverse=True):
		print(f"  {risk}: {count}")

	print("Most triggered rules:")
	for rule_id, count in rule_counter.most_common(10):
		print(f"  {rule_id}: {count}")


def build_parser() -> argparse.ArgumentParser:
	"""Build CLI arguments."""
	parser = argparse.ArgumentParser(description="Rule-based emergency alert inference engine.")
	parser.add_argument(
		"--input",
		type=Path,
		default=Path("data/processed_lisboa_porto_air_quality.csv"),
		help="Path to input CSV with environmental measurements.",
	)
	parser.add_argument(
		"--rules",
		type=Path,
		default=Path("Module_1/regras.json"),
		help="Path to JSON rules knowledge base.",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=Path("Module_1/outputs/rules_inference_output.csv"),
		help="Path to output CSV with inferred risks and actions.",
	)
	parser.add_argument(
		"--limit",
		type=int,
		default=None,
		help="Optional number of rows to process for quick tests.",
	)
	return parser


def main() -> None:
	"""CLI entry point."""
	args = build_parser().parse_args()
	run_inference(args.input, args.rules, args.output, args.limit)


if __name__ == "__main__":
	main()
