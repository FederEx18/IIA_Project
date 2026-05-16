# -*- coding: utf-8 -*-
"""
Módulo 3 — IA Generativa
========================
Gera um relatório de qualidade do ar em linguagem natural a partir dos
outputs estruturados dos Módulos 1 e 2:
  - Module_1/resultados_alertas.csv  → motor de regras
  - Module_1/regras.json             → base de conhecimento
  - Module_2/resultados/metrics.csv  → métricas dos modelos ML

O script:
  1. Lê e agrega os factos numéricos.
  2. Constrói três variantes de prompt (baseline, estruturado, crítico-ético).
  3. Envia ao LLM e recolhe o texto gerado.
  4. Escreve o output em Markdown, contendo:
        - Resumo executivo (≤ 200 palavras)
        - 2-3 recomendações de ação
        - Secção de limitações e riscos

Princípio de desenho (grounding): o LLM recebe APENAS factos numéricos
pré-calculados; não tem acesso ao dataset bruto. Restringimos a sua função
à formatação textual e adaptação de linguagem, mitigando o risco de
alucinação. Toda decisão factual continua a vir dos Módulos 1 e 2.

Uso:
    python gen_report.py --variant critico_etico --output report.md

Dependências:
    pip install pandas anthropic
    export ANTHROPIC_API_KEY=...

Autores: Equipa Projeto IIA, ISCTE 2025/2026
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd

# ---------------------------------------------------------------------------
# Configuração de caminhos (ajustáveis por linha de comandos)
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALERTS = ROOT / "Module_1" / "resultados_alertas.csv"
DEFAULT_RULES = ROOT / "Module_1" / "regras.json"
DEFAULT_METRICS = ROOT / "Module_2" / "resultados" / "metrics.csv"

# ---------------------------------------------------------------------------
# Estrutura de factos: tudo o que o LLM verá é construído a partir disto
# ---------------------------------------------------------------------------


@dataclass
class ReportFacts:
    """Factos numéricos pré-calculados que alimentam o prompt."""

    # Contexto
    n_observations: int
    cities: List[str]
    period: str

    # Módulo 1
    alerts_by_level: Dict[str, int]   # ex: {"NORMAL": 1240, "ALTO": 195, "MODERADO": 7}
    top_rules: List[Dict]             # ex: [{"id": "R04_PM25_ALTO", "count": 140, "source": "..."}, ...]
    pct_alerts_by_city: Dict[str, float]

    # Módulo 2 (classificação)
    classification_metrics: List[Dict]   # uma linha por modelo
    best_classifier: str

    # Módulo 2 (regressão)
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

    # ---- Módulo 1: alertas (CSV usa separador ';' e nomes em PT)
    alerts = pd.read_csv(alerts_path, sep=";")
    # Normalizar nomes PT -> EN para o resto da função
    rename = {"cidade": "city", "risco": "risk_level", "regras": "rule_id",
              "n_alertas": "n_alerts", "acao": "action"}
    alerts = alerts.rename(columns={k: v for k, v in rename.items() if k in alerts.columns})
    n_obs = len(alerts)
    cities = sorted(alerts["city"].unique().tolist()) if "city" in alerts.columns else []

    # Determinar período a partir do datetime, se existir
    if "datetime" in alerts.columns:
        dt = pd.to_datetime(alerts["datetime"], format="%d/%m/%y %H:%M", errors="coerce")
        if dt.notna().any():
            period = f"{dt.min().date().isoformat()} a {dt.max().date().isoformat()}"
        else:
            period = "Período não disponível"
    else:
        period = "Período não disponível"

    # Distribuição de níveis de risco
    level_col = "risk_level" if "risk_level" in alerts.columns else (
        "nivel" if "nivel" in alerts.columns else None
    )
    if level_col is None:
        # Fallback: procurar coluna que contenha "level" ou "risco"
        candidates = [c for c in alerts.columns if "level" in c.lower() or "risco" in c.lower()]
        level_col = candidates[0] if candidates else None
    alerts_by_level = (
        alerts[level_col].fillna("NORMAL").value_counts().to_dict() if level_col else {}
    )

    # Top regras disparadas
    rules_col = None
    for c in ["rule_id", "regra_id", "rules_triggered", "regras"]:
        if c in alerts.columns:
            rules_col = c
            break
    top_rules = []
    if rules_col:
        # Pode haver várias regras por linha, separadas por ;
        rule_counts: Counter = Counter()
        for val in alerts[rules_col].dropna():
            for r in str(val).split(";"):
                r = r.strip()
                if r and r.upper() != "NORMAL":
                    rule_counts[r] += 1
        # Cruzar com regras.json para obter source
        rules_db = {}
        if rules_path.exists():
            with open(rules_path, encoding="utf-8") as f:
                rules_json = json.load(f)
            rules_db = {r["id"]: r for r in rules_json.get("rules", [])}
        for rule_id, count in rule_counts.most_common(5):
            entry = {"id": rule_id, "count": int(count)}
            if rule_id in rules_db:
                entry["description"] = rules_db[rule_id].get("description", "")
                entry["source"] = rules_db[rule_id]["consequence"].get("source", "")
                entry["action"] = rules_db[rule_id]["consequence"].get("action", "")
            top_rules.append(entry)

    # % alertas por cidade
    pct_alerts_by_city = {}
    if "city" in alerts.columns and level_col:
        for city in cities:
            sub = alerts[alerts["city"] == city]
            if len(sub) == 0:
                continue
            n_alert = (sub[level_col].fillna("NORMAL") != "NORMAL").sum()
            pct_alerts_by_city[city] = round(100 * n_alert / len(sub), 1)

    # ---- Módulo 2: métricas
    metrics = pd.read_csv(metrics_path)
    cls = metrics[metrics["tarefa"] == "classificacao"].copy()
    reg = metrics[metrics["tarefa"] == "regressao"].copy()

    # Selecionar campos relevantes para classificação
    cls_records = []
    for _, r in cls.iterrows():
        cls_records.append({
            "modelo": r["modelo"],
            "accuracy": round(float(r["accuracy"]), 3),
            "precision": round(float(r["precision"]), 3),
            "recall": round(float(r["recall"]), 3),
            "f1": round(float(r["f1"]), 3),
            "roc_auc": round(float(r["roc_auc"]), 3),
        })
    # Melhor classificador: maior F1 (foco na classe minoritária)
    best_cls = max(cls_records, key=lambda x: x["f1"])["modelo"] if cls_records else ""

    reg_records = []
    for _, r in reg.iterrows():
        reg_records.append({
            "modelo": r["modelo"],
            "r2": round(float(r["r2"]), 3),
            "mse": round(float(r["mse"]), 2),
            "mae": round(float(r["mae"]), 2),
        })
    best_reg = max(reg_records, key=lambda x: x["r2"])["modelo"] if reg_records else ""

    return ReportFacts(
        n_observations=n_obs,
        cities=cities,
        period=period,
        alerts_by_level=alerts_by_level,
        top_rules=top_rules,
        pct_alerts_by_city=pct_alerts_by_city,
        classification_metrics=cls_records,
        best_classifier=best_cls,
        regression_metrics=reg_records,
        best_regressor=best_reg,
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
    "baseline": PROMPT_BASELINE,
    "estruturado": PROMPT_ESTRUTURADO,
    "critico_etico": PROMPT_CRITICO_ETICO,
}


# ---------------------------------------------------------------------------
# Cliente LLM (Anthropic Claude). Permite fallback para um modo offline
# que produz template estático — útil para correção/avaliação sem chave API.
# ---------------------------------------------------------------------------


def call_llm(prompt: str, model: str = "claude-sonnet-4-5", max_tokens: int = 1500) -> str:
    """Envia o prompt ao LLM e devolve o texto gerado."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        return _offline_template(prompt)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _offline_template(prompt)

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    # Concatenar blocos de texto
    return "".join(getattr(b, "text", "") for b in response.content)


def _offline_template(prompt: str) -> str:
    """Fallback determinístico: extrai factos do prompt e formata em Markdown.
    Não substitui o LLM mas garante que o pipeline corre sem chave API.
    """
    # Extrair o bloco de factos (JSON após 'Factos:' ou 'Dados:')
    marker = "Factos:" if "Factos:" in prompt else "Dados:"
    facts_block = prompt.split(marker, 1)[-1].strip()
    try:
        facts = json.loads(facts_block)
    except json.JSONDecodeError:
        return ("# Relatório (modo offline)\n\nNão foi possível processar os "
                "factos. Defina ANTHROPIC_API_KEY e instale o pacote anthropic "
                "para gerar texto natural.")

    n = facts.get("n_observations", "?")
    cities = ", ".join(facts.get("cities", [])) or "não especificadas"
    period = facts.get("period", "?")
    levels = facts.get("alerts_by_level", {})
    n_alert = sum(v for k, v in levels.items() if str(k).upper() != "NORMAL")
    top_rules = facts.get("top_rules", [])
    cls = facts.get("classification_metrics", [])
    reg = facts.get("regression_metrics", [])

    md = []
    md.append("## Resumo executivo\n")
    md.append(
        f"Foram analisadas {n} observações horárias de qualidade do ar nas "
        f"cidades de {cities}, no período {period}. O motor de regras "
        f"identificou {n_alert} situações com risco acima do nível normal "
        f"({100*n_alert/max(n,1):.1f} % do total)."
    )
    if top_rules:
        rule = top_rules[0]
        md.append(
            f" A regra mais ativada foi {rule.get('id')} "
            f"({rule.get('count')} ocorrências), "
            f"associada a {rule.get('description', 'risco ambiental')}."
        )
    if cls:
        best = facts.get("best_classifier", "")
        best_row = next((r for r in cls if r["modelo"] == best), cls[0])
        md.append(
            f" Para a tarefa de classificação binária da qualidade do ar, "
            f"o modelo {best} obteve F1 = {best_row['f1']} e ROC-AUC = "
            f"{best_row['roc_auc']}, com recall = {best_row['recall']} na "
            f"classe minoritária."
        )
    if reg:
        best_r = facts.get("best_regressor", "")
        best_rrow = next((r for r in reg if r["modelo"] == best_r), reg[0])
        md.append(
            f" Para a previsão de NO₂, o modelo {best_r} atingiu R² = "
            f"{best_rrow['r2']} e MAE = {best_rrow['mae']} µg/m³."
        )
    md.append("\n\n## Recomendações\n")
    if top_rules:
        for i, rule in enumerate(top_rules[:3], 1):
            md.append(
                f"{i}. **{rule.get('id')}** — {rule.get('action', 'sem ação registada')} "
                f"(fonte: {rule.get('source', 'n/d')})."
            )
    md.append("\n## Limitações e riscos\n")
    md.append(
        "- O dataset cobre apenas duas cidades portuguesas e dois meses; "
        "generalização sazonal e geográfica é limitada.\n"
        "- A target air_quality_good é redefinida para gerar variabilidade "
        "(NO₂ ≥ 30 µg/m³ ∧ humidade ≥ 80 %), pelo que não é diretamente "
        "comparável com sistemas externos.\n"
        "- O sistema é apoio à decisão, não decisor autónomo: cada alerta "
        "deve ser validado pela Proteção Civil antes de comunicação ao "
        "público."
    )
    return "\n".join(md)


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------


def generate(facts: ReportFacts, variant: str) -> str:
    if variant not in PROMPTS:
        raise ValueError(f"Variante desconhecida: {variant}. Escolha entre {list(PROMPTS)}")
    prompt = PROMPTS[variant].format(facts=json.dumps(facts.to_dict(), ensure_ascii=False, indent=2))
    return call_llm(prompt)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera relatório de qualidade do ar via LLM.")
    parser.add_argument("--variant", choices=list(PROMPTS.keys()), default="critico_etico",
                        help="Variante de prompt a usar.")
    parser.add_argument("--alerts", type=Path, default=DEFAULT_ALERTS)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--output", type=Path, default=Path("report.md"))
    args = parser.parse_args(argv)

    facts = load_facts(args.alerts, args.rules, args.metrics)
    text = generate(facts, args.variant)

    args.output.write_text(text, encoding="utf-8")
    print(f"Gerado: {args.output} ({len(text)} caracteres, variante={args.variant})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
#  parser.parse_args(argv)

#     facts = load_facts(args.alerts, args.rules, args.metrics)
#     text = generate(facts, args.variant)

#     args.output.write_text(text, encoding="utf-8")
#     print(f"Gerado: {args.output} ({len(text)} caracteres, variante={args.variant})")
#     return 0


# if __name__ == "__main__":
#     sys.exit(main())
