# Module 1 - Knowledge-Based Emergency Alerts

## Scope

This folder contains the Module 1 deliverable:

1. Rule-based inference engine.
2. Bayesian network with inference by enumeration.
3. JSON knowledge base for alert rules.

## Main Files

1. `regras.json`
- Rule base used by the symbolic engine.
- Includes `rules`, `risk_levels`, and `metadata`.

2. `rules_engine.py`
- Reads a semicolon-separated CSV dataset.
- Applies symbolic rules row by row.
- Supports both rule schemas:
  - legacy `conditions` list
  - structured `condition` (`simple_threshold`, `range`, `compound_and`, `compound_or`)
- Writes enriched output with matched rules, risk level, and recommended actions.

3. `bayes_alerts.py`
- Implements a 4-node Bayesian network.
- Uses exact inference by enumeration.
- Writes posterior probabilities for fire risk.

4. `rules_sources.md`
- Sources and caveats for threshold definitions.

5. `dev.ipynb` and `eda1.ipynb`
- Notebook support for EDA, preprocessing checks, and evaluation/report material.

## Default Input and Output Paths

From project root, the scripts use:

1. Input CSV (both scripts)
- `data/processed_lisboa_porto_air_quality.csv`

2. Rules engine output
- `Module_1/outputs/rules_inference_output.csv`

3. Bayesian output
- `Module_1/outputs/bayes_inference_output.csv`

## Output Columns Added

1. `rules_inference_output.csv`
- `CO_8h_avg`
- `matched_rule_ids`
- `matched_rule_names`
- `overall_risk`
- `recommended_actions`

2. `bayes_inference_output.csv`
- `p_fire_risk_true`
- `p_fire_risk_false`

## Preprocessing Logic Implemented in Code

Current runtime preprocessing behavior:

1. Safe numeric parsing (empty/invalid values become missing).
2. Feature alias handling for rule compatibility (`PM2_5` -> `PM2.5`).
3. `CO_8h_avg` created in `rules_engine.py`:
- Rolling window of 8 rows per city.
- Requires at least 6 valid CO values.
- Leaves empty value if insufficient data.

Notes:
- No global row removal is performed inside the scripts.
- If a rule depends on a missing variable, that condition evaluates to `False`.

## How to Run

From project root:

```bash
python Module_1/rules_engine.py
python Module_1/bayes_alerts.py
```

Windows (recommended in this repository setup):

```bash
.\.venv\Scripts\python.exe Module_1/rules_engine.py
.\.venv\Scripts\python.exe Module_1/bayes_alerts.py
```


## Optional Custom Inputs/Outputs

Both scripts support CLI overrides.

Example using a notebook-generated preprocessed file:

```bash
python Module_1/rules_engine.py --input Module_1/outputs/preprocessed_for_rules.csv --output Module_1/outputs/rules_inference_output.csv
python Module_1/bayes_alerts.py --input Module_1/outputs/preprocessed_for_rules.csv --output Module_1/outputs/bayes_inference_output.csv
```

## Delivery Checklist (Module 1)

1. `regras.json` present and loadable.
2. `rules_engine.py` executable from project root.
3. `bayes_alerts.py` executable from project root.
4. Output files generated in `Module_1/outputs`.

## Notebook Roles

1. `eda1.ipynb` - exploratory data analysis and preprocessing decisions.
2. `dev.ipynb` - Module 1 execution flow, validation, and critical discussion.

