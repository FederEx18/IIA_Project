from __future__ import annotations

"""Simple Bayesian alert system using inference by enumeration.

The network estimates fire risk from weather-related evidence extracted
from each dataset row.
"""

import argparse
import csv
from pathlib import Path
from typing import Any


class BayesNode:
	"""Single Bayesian network node with a conditional probability table."""
	def __init__(self, name: str, parents: list[str], cpt: dict[tuple[bool, ...], float]) -> None:
		self.name = name
		self.parents = parents
		self.cpt = cpt

	def p_true(self, evidence: dict[str, bool]) -> float:
		"""Return P(node=True | parent assignments from evidence)."""
		key = tuple(evidence[parent] for parent in self.parents)
		return self.cpt[key]


class BayesNetwork:
	"""Container for nodes and a fast name-to-node lookup."""
	def __init__(self, nodes: list[BayesNode]) -> None:
		self.nodes = nodes
		self.by_name = {node.name: node for node in nodes}


def normalize(distribution: dict[bool, float]) -> dict[bool, float]:
	"""Scale probabilities so they sum to 1."""
	total = sum(distribution.values())
	if total == 0:
		return distribution
	return {k: v / total for k, v in distribution.items()}


def enumerate_all(variables: list[str], evidence: dict[str, bool], bn: BayesNetwork) -> float:
	"""Recursive enumeration used to compute joint probabilities."""
	if not variables:
		return 1.0

	first = variables[0]
	rest = variables[1:]
	node = bn.by_name[first]

	if first in evidence:
		# If variable is observed, use only that branch.
		p_true = node.p_true(evidence)
		p = p_true if evidence[first] else (1 - p_true)
		return p * enumerate_all(rest, evidence, bn)

	total = 0.0
	# If variable is hidden, sum over both True/False branches.
	for value in (True, False):
		extended = dict(evidence)
		extended[first] = value
		p_true = node.p_true(extended)
		p = p_true if value else (1 - p_true)
		total += p * enumerate_all(rest, extended, bn)
	return total


def enumeration_ask(query_var: str, evidence: dict[str, bool], bn: BayesNetwork) -> dict[bool, float]:
	"""Compute posterior distribution for query_var given evidence."""
	dist: dict[bool, float] = {}
	variables = [node.name for node in bn.nodes]
	for value in (True, False):
		extended = dict(evidence)
		extended[query_var] = value
		dist[value] = enumerate_all(variables, extended, bn)
	return normalize(dist)


def build_fire_risk_network() -> BayesNetwork:
	"""Create a 4-node network: heatwave, humidity, wind -> fire_risk."""
	# Node order matters for enumeration: parents must appear first.
	heatwave = BayesNode("heatwave", [], {(): 0.20})
	low_humidity = BayesNode("low_humidity", [], {(): 0.30})
	strong_wind = BayesNode("strong_wind", [], {(): 0.25})

	fire_risk = BayesNode(
		"fire_risk",
		["heatwave", "low_humidity", "strong_wind"],
		{
			(True, True, True): 0.95,
			(True, True, False): 0.85,
			(True, False, True): 0.80,
			(False, True, True): 0.75,
			(True, False, False): 0.50,
			(False, True, False): 0.40,
			(False, False, True): 0.35,
			(False, False, False): 0.05,
		},
	)
	return BayesNetwork([heatwave, low_humidity, strong_wind, fire_risk])


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


def evidence_from_row(row: dict[str, str]) -> dict[str, bool]:
	"""Map dataset values into boolean evidence variables for the network."""
	temp = parse_float(row.get("temperature_c"))
	humidity = parse_float(row.get("humidity_percent"))
	wind = parse_float(row.get("wind_speed_kmh"))

	evidence: dict[str, bool] = {}
	# If a feature is missing, we simply leave that evidence variable unknown.
	if temp is not None:
		evidence["heatwave"] = temp >= 30
	if humidity is not None:
		evidence["low_humidity"] = humidity <= 35
	if wind is not None:
		evidence["strong_wind"] = wind >= 35
	return evidence


def infer_for_row(row: dict[str, str], bn: BayesNetwork) -> dict[str, float]:
	"""Return posterior probabilities for one row."""
	evidence = evidence_from_row(row)
	posterior = enumeration_ask("fire_risk", evidence, bn)
	return {
		"p_fire_risk_true": posterior[True],
		"p_fire_risk_false": posterior[False],
	}


def run_batch(input_csv: Path, output_csv: Path, limit: int | None = None) -> None:
	"""Run Bayesian inference for many rows and save probabilities to CSV."""
	bn = build_fire_risk_network()

	with input_csv.open("r", encoding="utf-8", newline="") as source:
		reader = csv.DictReader(source, delimiter=";")
		fieldnames = list(reader.fieldnames or []) + ["p_fire_risk_true", "p_fire_risk_false"]

		rows_out: list[dict[str, str]] = []
		count = 0
		for row in reader:
			# Optional limit for fast debug runs.
			if limit is not None and count >= limit:
				break
			probs = infer_for_row(row, bn)
			row["p_fire_risk_true"] = f"{probs['p_fire_risk_true']:.4f}"
			row["p_fire_risk_false"] = f"{probs['p_fire_risk_false']:.4f}"
			rows_out.append(row)
			count += 1

	output_csv.parent.mkdir(parents=True, exist_ok=True)
	with output_csv.open("w", encoding="utf-8", newline="") as sink:
		writer = csv.DictWriter(sink, fieldnames=fieldnames, delimiter=";")
		writer.writeheader()
		writer.writerows(rows_out)

	print(f"Processed rows: {count}")
	print(f"Output written to: {output_csv}")


def run_single(input_csv: Path, row_index: int) -> None:
	"""Run Bayesian inference for a single row and print details."""
	bn = build_fire_risk_network()
	with input_csv.open("r", encoding="utf-8", newline="") as source:
		reader = list(csv.DictReader(source, delimiter=";"))

	if row_index < 0 or row_index >= len(reader):
		raise IndexError(f"row_index {row_index} is outside valid range 0..{len(reader)-1}")

	row = reader[row_index]
	evidence = evidence_from_row(row)
	posterior = enumeration_ask("fire_risk", evidence, bn)

	print(f"Row index: {row_index}")
	print(f"City: {row.get('city', '')} | Datetime: {row.get('datetime', '')}")
	print(f"Evidence: {evidence if evidence else 'none (priors only)'}")
	print(f"P(fire_risk=True | evidence)  = {posterior[True]:.4f}")
	print(f"P(fire_risk=False | evidence) = {posterior[False]:.4f}")


def build_parser() -> argparse.ArgumentParser:
	"""Build CLI arguments."""
	parser = argparse.ArgumentParser(
		description="Bayesian fire risk alerts with inference by enumeration."
	)
	parser.add_argument(
		"--input",
		type=Path,
		default=Path("data/processed_lisboa_porto_air_quality.csv"),
		help="Path to input CSV with environmental measurements.",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=Path("Module_1/outputs/bayes_inference_output.csv"),
		help="Path to batch output CSV.",
	)
	parser.add_argument(
		"--limit",
		type=int,
		default=None,
		help="Optional number of rows to process in batch mode.",
	)
	parser.add_argument(
		"--row-index",
		type=int,
		default=None,
		help="If provided, runs inference for a single row index and prints posterior.",
	)
	return parser


def main() -> None:
	"""CLI entry point."""
	args = build_parser().parse_args()
	if args.row_index is not None:
		run_single(args.input, args.row_index)
	else:
		run_batch(args.input, args.output, args.limit)


if __name__ == "__main__":
	main()
