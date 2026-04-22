import pandas as pd
import json

# leitura das regras 
def load_rules(file_path):
    with open(file_path, 'r') as file:
        rules = json.load(file)
    return rules.get("rules", [])

# Avaliação do tipo de condição para cada regra
# Avalia uma condição simples: var OP valor
def evaluate_simple(condition, row):
    var = condition["variable"]
    operator = condition["operator"]
    
    # Aceitar "threshold" (condições raiz) ou "value" (sub-condições)
    # Só existe value na R09 e R12
    value = float(condition.get("threshold", condition.get("value")))

    if var not in row or row[var] == "" or pd.isna(row[var]):
        return False  # Variável ausente ou vazia, regra não é satisfeita
    
    observed = float(row[var])
    
    if operator == ">=": return observed >= value
    if operator == ">":  return observed > value
    if operator == "<=": return observed <= value
    if operator == "<":  return observed < value
    if operator == "==": return observed == value
    if operator == "!=": return observed != value
    return False

# Avalia uma condição de faixa: min <= var < max
def evaluate_range(condition, row):
    var = condition["variable"]
    if var not in row or row[var] == "":
        return False

    observed = float(row[var])
    min_val = condition.get("min")
    max_val = condition.get("max")
    
    if min_val is not None and observed < float(min_val):  
        return False
    if max_val is not None and observed >= float(max_val):
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

#Avalia qualquer tipo de condição
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
    else:
        raise ValueError(f"Tipo de condição desconhecido: {cond_type}")

# Avalia todas as regras para um dado registro
import pandas as pd
import json

# leitura das regras 
def load_rules(file_path):
    with open(file_path, 'r') as file:
        rules = json.load(file)
    return rules.get("rules", [])

# Avaliação do tipo de condição para cada regra
# Avalia uma condição simples: var OP valor
def evaluate_simple(condition, row):
    var = condition["variable"]
    operator = condition["operator"]
    value = float(condition["value"])

    if var not in row or row[var] == "":
        return False  # Variável ausente ou vazia, regra não é satisfeita
    
    observed = float(row[var])
    
    if operator == ">=": return observed >= value
    if operator == ">":  return observed > value
    if operator == "<=": return observed <= value
    if operator == "<":  return observed < value
    if operator == "==": return observed == value
    if operator == "!=": return observed != value
    return False

# Avalia uma condição de faixa: min <= var < max
def evaluate_range(condition, row):
    var = condition["variable"]
    if var not in row or row[var] == "":
        return False

    observed = float(row[var])
    min_val = condition.get("min")
    max_val = condition.get("max")
    
    if min_val is not None and observed < float(min_val):  
        return False
    if max_val is not None and observed > float(max_val):
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

#Avalia qualquer tipo de condição
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
    else:
        raise ValueError(f"Tipo de condição desconhecido: {cond_type}")

# Avalia todas as regras para um dado registro
import pandas as pd
import json

# leitura das regras 
def load_rules(file_path):
    with open(file_path, 'r') as file:
        rules = json.load(file)
    return rules.get("rules", [])

# Avaliação do tipo de condição para cada regra
# Avalia uma condição simples: var OP valor
def evaluate_simple(condition, row):
    var = condition["variable"]
    operator = condition["operator"]
    value = float(condition["value"])

    if var not in row or row[var] == "":
        return False  # Variável ausente ou vazia, regra não é satisfeita
    
    observed = float(row[var])
    
    if operator == ">=": return observed >= value
    if operator == ">":  return observed > value
    if operator == "<=": return observed <= value
    if operator == "<":  return observed < value
    if operator == "==": return observed == value
    if operator == "!=": return observed != value
    return False

# Avalia uma condição de faixa: min <= var < max
def evaluate_range(condition, row):
    var = condition["variable"]
    if var not in row or row[var] == "":
        return False

    observed = float(row[var])
    min_val = condition.get("min")
    max_val = condition.get("max")
    
    if min_val is not None and observed < float(min_val):  
        return False
    if max_val is not None and observed > float(max_val):
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

#Avalia qualquer tipo de condição
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
    else:
        raise ValueError(f"Tipo de condição desconhecido: {cond_type}")

# Aplica todas as regras a uma linha e retorna as ações recomendadas
def apply_rules_to_row(row, rules):
    matched_actions = []

    for rule in rules:
        try:
            if evaluate_condition(rule["condition"], row):
                matched_actions.append({
                    "rule_id": rule["id"],
                    "description": rule["description"],
                    "action": rule["consequence"]["action"]
                })
        except Exception as e:
            print(f"Erro ao avaliar regra {rule['id']}: {e}")

    return matched_actions

# Lê o dataset e aplica todas as regras a cada linha
def run_inference(csv_path, rules_path):
    # Carregar regras
    rules = load_rules(rules_path)
    df = pd.read_csv(csv_path, delimiter=";")

    print("A aplicar regras a cada linha...\n")

    # Iterar pelas linhas
    for i, row in df.iterrows():
        actions = apply_rules_to_row(row.to_dict(), rules)

        # Mostrar resultados apenas se houver ações
        if actions:
            print(f"Linha {i + 1}:")
            for a in actions:
                print(f"   ➤ [{a['rule_id']}] {a['action']}")
            print("-" * 50)

if __name__ == "__main__":
    run_inference("data/processed_lisboa_porto_air_quality.csv", "Module_1/regras.json")