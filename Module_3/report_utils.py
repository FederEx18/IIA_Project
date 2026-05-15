# -*- coding: utf-8 -*-
"""
Utilitários do Módulo 3 — partilhados com dev.ipynb.
Contém: ReportFacts, load_facts, variantes de prompt, generate_hf.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List

import pandas as pd


# ---------------------------------------------------------------------------
# Estrutura de factos
# ---------------------------------------------------------------------------

@dataclass
class ReportFacts:
    """Factos numéricos pré-calculados que alimentam o prompt."""
    n_observations: int
    cities: List[str]
    period: str
    alerts_by_level: Dict[str, int]
    top_rules: List[Dict]
    pct_alerts_by_city: Dict[str, float]
    classification_metrics: List[Dict]
    best_classifier: str
    regression_metrics: List[Dict]
    best_regressor: str

    def to_dict(self) -> dict:
        return {
            "n_observations": self.n_observations,
            "cities": self.cities,
            "period": self.period,
            "alerts_by_level": self.alerts_by_level,
            "top_rules": self.top_rules,
            "pct_alerts_by_city": self.pct_alerts_by_city,
            "classification_metrics": self.classification_metrics,
            "best_classifier": self.best_classifier,
            "regression_metrics": self.regression_metrics,
            "best_regressor": self.best_regressor,
        }


# ---------------------------------------------------------------------------
# Recolha de factos
# ---------------------------------------------------------------------------

def load_facts(alerts_path: Path, rules_path: Path, metrics_path: Path) -> ReportFacts:
    """Lê os três ficheiros de input e agrega-os num único objeto de factos."""
    alerts = pd.read_csv(alerts_path, sep=";")
    rename = {"cidade": "city", "risco": "risk_level", "regras": "rule_id",
              "n_alertas": "n_alerts", "acao": "action"}
    alerts = alerts.rename(columns={k: v for k, v in rename.items() if k in alerts.columns})
    n_obs  = len(alerts)
    cities = sorted(alerts["city"].unique().tolist()) if "city" in alerts.columns else []

    if "datetime" in alerts.columns:
        dt = pd.to_datetime(alerts["datetime"], errors="coerce")
        period = (f"{dt.min().date().isoformat()} a {dt.max().date().isoformat()}"
                  if dt.notna().any() else "Período não disponível")
    else:
        period = "Período não disponível"

    level_col = "risk_level" if "risk_level" in alerts.columns else (
        "nivel" if "nivel" in alerts.columns else None
    )
    if level_col is None:
        candidates = [c for c in alerts.columns if "level" in c.lower() or "risco" in c.lower()]
        level_col = candidates[0] if candidates else None
    alerts_by_level: Dict[str, int] = (
        {str(k): int(v) for k, v in alerts[level_col].fillna("NORMAL").value_counts().items()}
        if level_col else {}
    )

    rules_col = next((c for c in ["rule_id", "regra_id", "rules_triggered", "regras"]
                      if c in alerts.columns), None)
    top_rules: List[Dict] = []
    if rules_col:
        rule_counts: Counter = Counter()
        for val in alerts[rules_col].dropna():
            for r in str(val).split(";"):
                r = r.strip()
                if r and r.upper() != "NORMAL":
                    rule_counts[r] += 1
        rules_db: Dict[str, Dict] = {}
        if rules_path.exists():
            with open(rules_path, encoding="utf-8") as f:
                rules_json = json.load(f)
            rules_db = {r["id"]: r for r in rules_json.get("rules", [])}
        for rule_id, count in rule_counts.most_common(5):
            entry: Dict = {"id": rule_id, "count": int(count)}
            if rule_id in rules_db:
                entry["description"] = rules_db[rule_id].get("description", "")
                entry["source"] = rules_db[rule_id]["consequence"].get("source", "")
                entry["action"] = rules_db[rule_id]["consequence"].get("action", "")
            top_rules.append(entry)

    pct_alerts_by_city: Dict[str, float] = {}
    if "city" in alerts.columns and level_col:
        for city in cities:
            sub = alerts[alerts["city"] == city]
            if len(sub) == 0:
                continue
            n_alert = (sub[level_col].fillna("NORMAL") != "NORMAL").sum()
            pct_alerts_by_city[str(city)] = round(100 * n_alert / len(sub), 1)

    metrics = pd.read_csv(metrics_path)
    cls = metrics[metrics["tarefa"] == "classificacao"].copy()
    reg = metrics[metrics["tarefa"] == "regressao"].copy()

    cls_records = [
        {"modelo": r["modelo"], "accuracy": round(float(r["accuracy"]), 3),
         "precision": round(float(r["precision"]), 3), "recall": round(float(r["recall"]), 3),
         "f1": round(float(r["f1"]), 3), "roc_auc": round(float(r["roc_auc"]), 3)}
        for _, r in cls.iterrows()
    ]
    best_cls = max(cls_records, key=lambda x: x["f1"])["modelo"] if cls_records else ""

    reg_records = [
        {"modelo": r["modelo"], "r2": round(float(r["r2"]), 3),
         "mse": round(float(r["mse"]), 2), "mae": round(float(r["mae"]), 2)}
        for _, r in reg.iterrows()
    ]
    best_reg = max(reg_records, key=lambda x: x["r2"])["modelo"] if reg_records else ""

    return ReportFacts(
        n_observations=n_obs, cities=cities, period=period,
        alerts_by_level=alerts_by_level, top_rules=top_rules,
        pct_alerts_by_city=pct_alerts_by_city,
        classification_metrics=cls_records, best_classifier=best_cls,
        regression_metrics=reg_records, best_regressor=best_reg,
    )


# ---------------------------------------------------------------------------
# Variantes de prompt
# ---------------------------------------------------------------------------

PROMPT_BASELINE = """És um assistente que escreve relatórios curtos.
A partir destes dados sobre qualidade do ar, escreve:
- Um resumo executivo (≤ 200 palavras)
- 2 a 3 recomendações de ação
- Uma secção sobre limitações e riscos

Dados:
{facts}
"""

PROMPT_ESTRUTURADO = """És um analista técnico a redigir um relatório \
para a Proteção Civil. Usa exclusivamente os factos abaixo; não inventes \
números nem cidades. O relatório tem três secções com cabeçalho em \
Markdown ('## Resumo executivo', '## Recomendações', '## Limitações e \
riscos').

Regras:
1. Resumo executivo: máximo 200 palavras, prosa contínua, sem listas.
2. Recomendações: 2 a 3 ações concretas, cada uma indicando o gatilho \
quantitativo (ex: 'PM10 > 50 µg/m³') e a fonte regulamentar.
3. Limitações e riscos: enumerar pelo menos três limitações dos dados \
ou modelos, citando as métricas (recall, F1, R²) quando relevante.
4. Se não tiveres informação para uma alegação, escreve 'dados \
insuficientes'.

Factos:
{facts}
"""

PROMPT_CRITICO_ETICO = """És um analista de políticas públicas a \
redigir um relatório destinado simultaneamente a decisores municipais e \
a comunicação ao cidadão. O texto deve ser claro, sem jargão técnico \
excessivo, e ético: identifica explicitamente assimetrias de informação, \
risco de viés e incerteza dos modelos.

Estrutura obrigatória (cabeçalhos em Markdown):
## Resumo executivo (≤ 200 palavras)
## Recomendações (2 a 3 ações)
## Limitações, riscos e considerações éticas

Regras:
1. Usa apenas os factos fornecidos. Se algo não estiver nos factos, diz \
'não disponível nos dados deste relatório'.
2. Cada recomendação deve nomear (i) o gatilho quantitativo, (ii) a \
fonte regulamentar (Diretiva 2008/50/CE, OMS 2021, IPMA), (iii) o grupo \
de risco específico (asmáticos, idosos, crianças, trabalhadores ao ar \
livre).
3. Na secção crítica, discute pelo menos: o desbalanço de classes \
(~10 % de registos 'má'), a cobertura geográfica e sazonal limitada, e \
o risco de falsos negativos em saúde pública.
4. Não atribuas intenção, opinião ou previsão fora do que os dados \
suportam. Trata os modelos como ferramentas de apoio, nunca como \
decisores autónomos.

Factos:
{facts}
"""

PROMPTS = {
    "baseline":      PROMPT_BASELINE,
    "estruturado":   PROMPT_ESTRUTURADO,
    "critico_etico": PROMPT_CRITICO_ETICO,
}


# ---------------------------------------------------------------------------
# Geração de relatório
# ---------------------------------------------------------------------------

def generate_hf(
    facts: ReportFacts,
    variant: str,
    call_fn: Callable[..., str],
    temperature: float = 0.2,
    max_tokens: int = 1500,
) -> str:
    """Constrói o prompt da variante escolhida e envia via call_fn (HuggingFace)."""
    if variant not in PROMPTS:
        raise ValueError(f"Variante desconhecida: {variant!r}. Opções: {list(PROMPTS)}")
    prompt = PROMPTS[variant].format(
        facts=json.dumps(facts.to_dict(), ensure_ascii=False, indent=2)
    )
    return call_fn(prompt, temperature=temperature, max_tokens=max_tokens)
