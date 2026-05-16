import pandas as pd
import json
from pathlib import Path

#-------------------------------------------------------
# PATHS
#-------------------------------------------------------
# OUTPUT fica sempre dentro de Module_1/ (resolvido a partir da localização
# deste ficheiro), independentemente do CWD de quem corre o script.
ROOT       = Path(__file__).resolve().parent.parent
INPUT_CSV  = ROOT / "data" / "clean_air_quality.csv"
RULES_JSON = ROOT / "Module_1" / "regras.json"
OUTPUT_CSV = ROOT / "Module_1" / "resultados_alertas.csv"


# -------------------------------------------------------
# Aux para ordenar regras por prioridade na load_rules
# -------------------------------------------------------
def get_priority(rule):
    return rule["priority"]


# -------------------------------------------------------
# Leitura das regras
# -------------------------------------------------------
def load_rules(file_path):
    with open(file_path, 'r', encoding='UTF-8') as file:
        rules = json.load(file)
    regras = rules.get("rules", [])
    regras.sort(key=get_priority, reverse=True)# ordena da mais urgente (10) para a menos urgente (1)
    return regras


# -------------------------------------------------------
# Avalia uma condição simples: var OP valor
# -------------------------------------------------------
def evaluate_simple(condition, row):
    var      = condition["variable"]
    operator = condition["operator"]
    condition.get("threshold", condition.get("value"))
    value    = float(condition.get("threshold", condition.get("value")))# porque o nosso regras.json usa "threshold" na maioria das regras e value na R9 e R12

    if var not in row or row[var] == "" or pd.isna(row[var]):
        return False  # variável ausente ou vazia, regra não é satisfeita

    observed = float(row[var])

    if operator == ">=": return observed >= value
    if operator == ">":  return observed >  value
    if operator == "<=": return observed <= value
    if operator == "<":  return observed <  value
    if operator == "==": return observed == value
    if operator == "!=": return observed != value
    return False


# -------------------------------------------------------
# Avalia uma condição de faixa: min <= var < max
# -------------------------------------------------------
def evaluate_range(condition, row):
    var = condition["variable"]
    if var not in row or row[var] == "" or pd.isna(row[var]):
        return False

    observed = float(row[var])
    min_val  = condition.get("min")
    max_val  = condition.get("max")

    if min_val is not None and observed < float(min_val):
        return False
    if max_val is not None and observed >= float(max_val):  # corrigido: > → >=
        return False
    return True


# Avalia uma condição composta com AND
def evaluate_compound_and(condition, row):
    for sub in condition["conditions"]:
        if not evaluate_condition(sub, row):
            return False
    return True


# Avalia uma condição composta com OR
def evaluate_compound_or(condition, row):
    for sub in condition["conditions"]:
        if evaluate_condition(sub, row):
            return True
    return False


# -------------------------------------------------------
# Avalia qualquer tipo de condição
# -------------------------------------------------------
def evaluate_condition(condition, row):
    cond_type = condition.get("type", "simple_threshold")

    if cond_type == "simple_threshold":
        return evaluate_simple(condition, row)
    elif cond_type == "range":
        return evaluate_range(condition, row)
    elif cond_type == "compound_and":
        return evaluate_compound_and(condition, row)
    elif cond_type == "compound_or":
        return evaluate_compound_or(condition, row)
    elif "variable" in condition:
        # sub-condições para rule sem "type"(R09 e R12)
        return evaluate_simple(condition, row)
    else:
        raise ValueError(f"Tipo de condição desconhecido: {cond_type}")

# -------------------------------------------------------
# Aplica todas as regras a uma linha e retorna as 
# ações recomendadas
# -------------------------------------------------------
def apply_rules_to_row(row, rules):
    matched_actions = []

    for rule in rules:
        try:
            if evaluate_condition(rule["condition"], row):
                matched_actions.append({
                    "rule_id"    : rule["id"],
                    "description": rule["description"],
                    "risk_level" : rule["consequence"]["risk_level"],
                    "action"     : rule["consequence"]["action"],
                    "source"     : rule["consequence"]["source"],
                })
        except Exception as e:
            print(f"Erro ao avaliar regra {rule['id']}: {e}")

    return matched_actions


# -------------------------------------------------------
# Processa o dataset e guarda CSV de output
#  para a rede bayesiana ler os resultados
# -------------------------------------------------------
def run_inference(csv_path=INPUT_CSV, rules_path=RULES_JSON):
    rules = load_rules(rules_path)

    df = pd.read_csv(csv_path, delimiter=";")
    print(f"Dataset carregado: {len(df)} linhas")

    # calcular média de CO nas últimas 8 horas (necessário para a regra R06)
    df["CO_8h_avg"] = df["CO"].rolling(window=8, min_periods=1).mean()

    print("A aplicar regras a cada linha...\n")

    resultados = []

    for i, row in df.iterrows(): # corre pelas linhas do dataset
        actions = apply_rules_to_row(row.to_dict(), rules) # aplica as regras a cada linha e guarda as ações recomendadas

        if actions:
            principal = actions[0]  # alerta de maior prioridade (lista já ordenada)
            resultados.append({
                "cidade"   : row.get("city"),
                "datetime" : row.get("datetime"),
                "n_alertas": len(actions),
                "risco"    : principal["risk_level"],
                "regras"   : ", ".join(a["rule_id"] for a in actions),
                "acao"     : principal["action"],
            })
        else:
            resultados.append({
                "cidade"   : row.get("city"),
                "datetime" : row.get("datetime"),
                "n_alertas": 0,
                "risco"    : "NORMAL",
                "regras"   : "",
                "acao"     : "Sem ação necessária.",
            })

    df_out = pd.DataFrame(resultados)
    df_out.to_csv(OUTPUT_CSV, index=False, sep=";", encoding="utf-8")
    print(f"Output guardado em '{OUTPUT_CSV}'")
    return df_out


# -------------------------------------------------------
# Report dos resultados
# -------------------------------------------------------
def mostrar_relatorio(df_resultados):
    total      = len(df_resultados)
    com_alerta = (df_resultados["n_alertas"] > 0).sum()

    print()
    print("=" * 45)
    print("RESUMO DOS ALERTAS GERADOS")
    print("=" * 45)
    print(f"Total de observações : {total}")
    print(f"Com alerta           : {com_alerta} ({100*com_alerta/total:.1f}%)")
    print(f"Sem alerta           : {total - com_alerta} ({100*(total-com_alerta)/total:.1f}%)")
    print()
    print("Por nível de risco:")
    for nivel, count in df_resultados["risco"].value_counts().items():
        print(f"  {nivel:<10}  {count:>5}  ({100*count/total:.1f}%)")
    print()
    print("Regras mais disparadas (Top 5):")
    todas = []
    for r in df_resultados["regras"].dropna():
        if r:
            todas.extend(r.split(", "))
    for regra, count in pd.Series(todas).value_counts().head(5).items():
        print(f"  {regra:<30}  {count} vezes")
    print()
    print("Por cidade:")
    for cidade in sorted(df_resultados["cidade"].unique()):
        sub     = df_resultados[df_resultados["cidade"] == cidade]
        alertas = (sub["n_alertas"] > 0).sum()
        print(f"  {cidade:<15}  {alertas}/{len(sub)} observações com alerta")
    print("=" * 45)


if __name__ == "__main__":
    df_resultados = run_inference()
    mostrar_relatorio(df_resultados)