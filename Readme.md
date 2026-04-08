# IIA Project - IA for Sustainable Cities

## Project Overview

This repository is organized in 3 modules:

1. `Module_1` - Knowledge-based emergency alerts (rules + Bayesian network).
2. `Module_2` - Supervised learning for air quality and mobility.
3. `Module_3` - Generative AI reporting.

Current validated deliverable: **Module 1**.

## Repository Structure

1. `data/`
- Input dataset used across modules.

2. `Module_1/`
- Rule engine, Bayesian alerts, notebooks, and outputs.

3. `Module_2/`
- Classification/regression module files.

4. `Module_3/`
- Generative report module files.

## How to Run Module 1

From project root:

```bash
python Module_1/rules_engine.py
python Module_1/bayes_alerts.py
```

Windows with virtual environment:

```bash
.\.venv\Scripts\python.exe Module_1/rules_engine.py
.\.venv\Scripts\python.exe Module_1/bayes_alerts.py
```

Generated outputs:

1. `Module_1/outputs/rules_inference_output.csv`
2. `Module_1/outputs/bayes_inference_output.csv`

## Notes

1. Detailed Module 1 documentation is in `Module_1/readme.md`.
2. Module 2 and Module 3 files are present in the repository for full project organization.
