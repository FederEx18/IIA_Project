import pandas as pd
import json

# leitura das regras 
def load_rules_from_json(file_path):
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