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


def add_co_8h_average(rows: list[dict[str, str]]) -> None:
	"""Add CO_8h_avg using rolling 8-row window per city (min 6 valid values)."""
	windows: dict[str, deque[float | None]] = defaultdict(lambda: deque(maxlen=8))

	for row in rows:
		city = row.get("city", "") or "__global__"
		window = windows[city]

		co_value = parse_float(row.get("CO"))
		window.append(co_value)

		valid = [v for v in window if v is not None]
		if len(valid) >= 6:
			row["CO_8h_avg"] = f"{sum(valid) / len(valid):.6f}"
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


def evaluate_condition_v2(row: dict[str, str], condition: dict[str, Any]) -> bool:
	"""Evaluate Claude-style conditions (simple/range/compound)."""
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
		return all(evaluate_condition_v2(row, child) for child in children)

	if cond_type == "compound_or":
		children = condition.get("conditions", [])
		return any(evaluate_condition_v2(row, child) for child in children)

	# Backward-compatible handling for old shape nested inside v2.
	if "variable" in condition and "operator" in condition and "value" in condition:
		legacy_condition = {
			"feature": condition["variable"],
			"operator": condition["operator"],
			"value": condition["value"],
		}
		return evaluate_condition(row, legacy_condition)

	raise ValueError(f"Unsupported condition type: {cond_type}")


def rule_matches(row: dict[str, str], rule: dict[str, Any]) -> bool:
	"""Evaluate either legacy rules or Claude-style rules."""
	if "conditions" in rule:
		return all(evaluate_condition(row, condition) for condition in rule["conditions"])
	if "condition" in rule:
		return evaluate_condition_v2(row, rule["condition"])
	raise ValueError("Rule has neither 'conditions' nor 'condition'")


def aggregate_risk(matched_rules: list[dict[str, Any]]) -> str:
	"""Return the highest risk level among matched rules."""
	if not matched_rules:
		return "none"
	return max(matched_rules, key=lambda x: RISK_ORDER.get(x["risk_level"], 0))["risk_level"]


def collect_actions(matched_rules: list[dict[str, Any]]) -> list[str]:
	"""Collect unique actions, ordered by rule priority (high to low)."""
	actions: list[str] = []
	seen: set[str] = set()
	ordered = sorted(matched_rules, key=lambda x: x.get("priority", 0), reverse=True)
	for rule in ordered:
		for action in rule.get("actions", []):
			if action not in seen:
				actions.append(action)
				seen.add(action)
	return actions


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
	return str(rule.get("id", "unknown_rule"))


def get_rule_name(rule: dict[str, Any]) -> str:
	return str(rule.get("name", rule.get("description", get_rule_id(rule))))


def get_rule_priority(rule: dict[str, Any]) -> int:
	return int(rule.get("priority", 0))


def get_rule_risk_level(rule: dict[str, Any]) -> str:
	if "risk_level" in rule:
		return normalize_risk_level(str(rule.get("risk_level")))
	consequence = rule.get("consequence", {})
	if isinstance(consequence, dict):
		return normalize_risk_level(consequence.get("risk_level"))
	return "none"


def get_rule_actions(rule: dict[str, Any]) -> list[str]:
	if "actions" in rule and isinstance(rule["actions"], list):
		return [str(action) for action in rule["actions"]]
	consequence = rule.get("consequence", {})
	if isinstance(consequence, dict) and consequence.get("action"):
		return [str(consequence["action"])]
	return []


def infer_for_row(row: dict[str, str], rules: list[dict[str, Any]]) -> dict[str, Any]:
	"""Run rule inference for one row and return output fields."""
	matched = [rule for rule in rules if rule_matches(row, rule)]
	matched_sorted = sorted(matched, key=get_rule_priority, reverse=True)
	matched_risks = [get_rule_risk_level(rule) for rule in matched_sorted]
	risk = "none"
	if matched_risks:
		risk = max(matched_risks, key=lambda x: RISK_ORDER.get(x, 0))

	actions: list[str] = []
	seen: set[str] = set()
	for rule in matched_sorted:
		for action in get_rule_actions(rule):
			if action not in seen:
				actions.append(action)
				seen.add(action)

	return {
		"matched_rule_ids": "|".join(get_rule_id(rule) for rule in matched_sorted),
		"matched_rule_names": "|".join(get_rule_name(rule) for rule in matched_sorted),
		"overall_risk": risk,
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

			result = infer_for_row(row, rules)
			row.update(result)
			rows_to_write.append(row)

			if result["matched_rule_ids"]:
				for rule_id in result["matched_rule_ids"].split("|"):
					if rule_id:
						rule_counter[rule_id] += 1
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
	for risk, count in sorted(risk_counter.items(), key=lambda x: RISK_ORDER.get(x[0], -1), reverse=True):
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
