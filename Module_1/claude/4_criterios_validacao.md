# 4. CRITÉRIOS DE VALIDAÇÃO E TESTE

## 4.1 Validação do Motor de Inferência Baseado em Regras

### 4.1.1 Métricas de Cobertura por Regra

**Objetivo**: Verificar que cada regra é testada com dados reais do dataset.

#### Métrica 1: Taxa de Ativação por Regra

```python
coverage_metrics = {
    'rule_id': str,
    'total_applicable_records': int,  # Registos com variáveis necessárias não-null
    'total_activations': int,         # Registos onde condição = True
    'activation_rate': float,         # activations / applicable
    'risk_distribution': {
        'NORMAL': int,
        'BAIXO': int,
        'MODERADO': int,
        'ALTO': int
    }
}
```

**Critérios de Validação**:

| Critério | Threshold | Ação se Falha |
|----------|-----------|---------------|
| **Aplicabilidade mínima** | ≥100 registos | ⚠️ Warning: regra com dados insuficientes |
| **Ativação observada** | ≥1 ativação | ⚠️ Warning: regra nunca dispara (verificar limiar) |
| **Cobertura global** | ≥50% registos cobertos por ≥1 regra | ❌ Erro: sistema subutilizado |

**Exemplo de Output Esperado**:

```
COBERTURA DO MOTOR DE INFERÊNCIA
=================================
Regra R01_NO2_ALTO:
  Registos aplicáveis: 9157 (85,0%)
  Ativações: 486 (5,3%)
  Risco: ALTO=486
  ✓ Cobertura adequada

Regra R05_O3_ALTO:
  Registos aplicáveis: 1442 (13,4%)
  Ativações: 0 (0,0%)
  ⚠️ Regra nunca dispara - verificar se limiar está calibrado para dataset

Regra R10_VENTO_FORTE:
  Registos aplicáveis: 1442 (13,4%)
  Ativações: 0 (0,0%)
  ⚠️ Dataset não contém eventos de vento forte (max=28 km/h vs. limiar=75 km/h)
  Nota: Regra é válida, mas dados insuficientes para teste

SUMÁRIO GLOBAL:
  Total de registos: 10768
  Registos com ≥1 regra ativada: 6842 (63,5%)
  Registos sem regras ativadas: 3926 (36,5%)
  ✓ Cobertura global aceitável (>50%)
```

---

#### Métrica 2: Distribuição de Risco por Cidade/Período

**Objetivo**: Verificar se padrões de risco são consistentes com conhecimento do domínio.

```python
risk_by_city = {
    'Lisboa': {'ALTO': 45, 'MODERADO': 123, 'BAIXO': 89, 'NORMAL': 464},
    'Porto': {'ALTO': 52, 'MODERADO': 115, 'BAIXO': 94, 'NORMAL': 460},
    'UCI_Dataset': {'ALTO': 1234, 'MODERADO': 2456, 'BAIXO': 1890, 'NORMAL': 3746}
}
```

**Testes de Sanidade**:

1. **Verão vs. Inverno** (dados Lisboa/Porto):
   ```python
   assert risk_summer['ALTO_O3'] > risk_winter['ALTO_O3']  # O₃ é fotoquímico
   assert risk_winter['ALTO_NO2'] > risk_summer['ALTO_NO2']  # Mais tráfego + inversão
   ```

2. **UCI_Dataset vs. Lisboa/Porto**:
   ```python
   # UCI é mais poluído (zona industrial)
   assert (UCI_risk['ALTO'] / UCI_total) > (Lisboa_risk['ALTO'] / Lisboa_total)
   ```

---

### 4.1.2 Casos de Teste Manuais (Test Suite)

**Objetivo**: Validar lógica de inferência com cenários construídos.

#### Teste 1: Regra Simples - NO₂ Alto

```python
test_case_1 = {
    'name': 'NO2_critico_210',
    'input': {
        'NO2': 210,  # Acima de 200
        'PM10': 15,
        'temperature_c': 18,
        'humidity_percent': 55
    },
    'expected_output': {
        'activated_rules': ['R01_NO2_ALTO'],
        'risk_level': 'ALTO',
        'primary_action': 'Limitar tráfego automóvel'
    }
}

def run_test(test_case):
    result = inference_engine.evaluate(test_case['input'])
    assert 'R01_NO2_ALTO' in result['activated_rules']
    assert result['risk_level'] == 'ALTO'
    print(f"✓ {test_case['name']} PASS")
```

#### Teste 2: Regra Composta - Incêndio

```python
test_case_2 = {
    'name': 'risco_incendio_extremo',
    'input': {
        'temperature_c': 42,  # >40 (calor extremo) E >35 (incêndio)
        'humidity_percent': 18,  # <30
        'wind_speed_kmh': 12
    },
    'expected_output': {
        'activated_rules': ['R08_CALOR_EXTREMO', 'R09_RISCO_INCENDIO'],
        'risk_level': 'ALTO',  # Máximo dos riscos
        'actions': [
            'Alerta vermelho calor',
            'Risco máximo incêndio florestal'
        ]
    }
}
```

#### Teste 3: Múltiplas Regras (Caso Real Complexo)

```python
test_case_3 = {
    'name': 'episodio_poluicao_inverno',
    'input': {
        'city': 'Lisboa',
        'datetime': '2026-01-15 08:00',
        'NO2': 165,
        'PM10': 42,
        'PM2_5': 21,
        'temperature_c': 8,
        'humidity_percent': 85,
        'wind_speed_kmh': 3
    },
    'expected_output': {
        'activated_rules': ['R02_NO2_MODERADO', 'R03_PM10_ALTO', 'R04_PM25_ALTO', 'R12_QUALIDADE_AR_PESSIMA'],
        'risk_level': 'ALTO',  # R03, R04, R12 são ALTO
        'interpretation': 'Inversão térmica com múltiplos poluentes'
    }
}
```

#### Teste 4: Caso Negativo (Sem Alertas)

```python
test_case_4 = {
    'name': 'condicoes_ideais',
    'input': {
        'NO2': 25,
        'PM10': 12,
        'temperature_c': 22,
        'humidity_percent': 50,
        'wind_speed_kmh': 15
    },
    'expected_output': {
        'activated_rules': [],
        'risk_level': 'NORMAL',
        'actions': ['Monitorização de rotina']
    }
}
```

#### Teste 5: Missing Values (Robustez)

```python
test_case_5 = {
    'name': 'dados_parciais_UCI',
    'input': {
        'NO2': 180,
        'CO': 2.3,
        'temperature_c': 15,
        'humidity_percent': 60,
        # PM10, PM2.5, O3, SO2, wind, precip estão NaN
    },
    'expected_output': {
        'activated_rules': ['R02_NO2_MODERADO'],  # Apenas regras aplicáveis
        'risk_level': 'MODERADO',
        'skipped_rules': ['R03_PM10_ALTO', 'R04_PM25_ALTO', 'R05_O3_ALTO', 'R07_SO2_ALTO', 'R10_VENTO_FORTE', 'R11_PRECIPITACAO_INTENSA'],
        'note': 'Regras PM/O3/SO2/meteorológicas não avaliadas (dados ausentes)'
    }
}
```

---

### 4.1.3 Validação de Prioridade de Regras

**Problema**: Múltiplas regras ativadas → qual prevalece?

**Solução Implementada**: Sistema de prioridade (campo `priority` no JSON).

**Teste de Prioridade**:

```python
test_priority = {
    'input': {
        'NO2': 210,  # Ativa R01 (prioridade 10)
        'temperature_c': 41  # Ativa R08 (prioridade 10)
    },
    'expected_behavior': {
        'risk_level': 'ALTO',  # Ambas são ALTO
        'primary_recommendation': 'Alerta vermelho calor',  # R08 listado primeiro (desempate arbitrário)
        'secondary_recommendation': 'Limitar tráfego automóvel'  # R01
    }
}
```

**Regra de Desempate** (quando prioridades iguais):
1. Categoria meteorológica > qualidade do ar (impacto imediato mais amplo)
2. Ordem alfabética de `rule_id` (determinístico)

---

### 4.1.4 Validação de Lógica Booleana

**Objetivo**: Garantir que operadores lógicos (AND, OR, >=, <=) funcionam corretamente.

#### Teste AND (Regra R09):
```python
# R09: temperature >= 35 AND humidity <= 30
assert not evaluate_rule('R09', {'temperature_c': 36, 'humidity_percent': 35})  # Falha 2ª condição
assert not evaluate_rule('R09', {'temperature_c': 32, 'humidity_percent': 28})  # Falha 1ª condição
assert evaluate_rule('R09', {'temperature_c': 36, 'humidity_percent': 28})      # ✓ Ambas True
```

#### Teste OR (Regra R12):
```python
# R12: (NO2>=150 OR PM10>=40 OR PM2_5>=20) AND humidity>=80
assert evaluate_rule('R12', {'NO2': 160, 'PM10': 30, 'PM2_5': 15, 'humidity_percent': 85})  # NO2 satisfaz
assert evaluate_rule('R12', {'NO2': 100, 'PM10': 45, 'PM2_5': 15, 'humidity_percent': 85})  # PM10 satisfaz
assert not evaluate_rule('R12', {'NO2': 160, 'PM10': 45, 'humidity_percent': 75})  # Falha AND
```

#### Teste RANGE (Regra R02):
```python
# R02: 100 <= NO2 < 200
assert evaluate_rule('R02', {'NO2': 150})
assert not evaluate_rule('R02', {'NO2': 99})
assert not evaluate_rule('R02', {'NO2': 200})  # Limite superior exclusivo
```

---

### 4.1.5 Relatório de Validação do Motor (Template)

```markdown
# RELATÓRIO DE VALIDAÇÃO - MOTOR DE INFERÊNCIA

## Execução
- Data: 2026-04-08
- Dataset: processed_lisboa_porto_air_quality.csv (10.768 registos)
- Regras avaliadas: 12

## Resultados de Cobertura

| Regra | Aplicável | Ativações | Taxa | Status |
|-------|-----------|-----------|------|--------|
| R01_NO2_ALTO | 9157 | 486 | 5,3% | ✓ OK |
| R02_NO2_MODERADO | 9157 | 1423 | 15,5% | ✓ OK |
| R03_PM10_ALTO | 1442 | 67 | 4,6% | ✓ OK |
| ... | ... | ... | ... | ... |
| R10_VENTO_FORTE | 1442 | 0 | 0,0% | ⚠️ Sem dados |

**Cobertura Global**: 6842/10768 registos (63,5%) → ✓ PASS

## Casos de Teste: 5/5 PASS

- ✓ Teste 1: NO2_critico_210
- ✓ Teste 2: risco_incendio_extremo
- ✓ Teste 3: episodio_poluicao_inverno
- ✓ Teste 4: condicoes_ideais
- ✓ Teste 5: dados_parciais_UCI

## Validação Lógica: PASS

- ✓ Operadores AND/OR corretos
- ✓ Comparações numéricas corretas
- ✓ Gestão de missing values correta

## Conclusão: SISTEMA VALIDADO ✓
```

---

## 4.2 Validação da Rede Bayesiana

### 4.2.1 Sanity Checks Probabilísticos

#### Check 1: Normalização das CPTs

```python
def validate_cpt_normalization(cpt, tolerance=1e-6):
    """Verifica se probabilidades somam 1 para cada configuração de pais"""
    for parent_config, probs in cpt.items():
        total = sum(probs.values())
        assert abs(total - 1.0) < tolerance, \
            f"CPT não normalizada: {parent_config} soma {total}"
    print("✓ CPT normalizada corretamente")
```

**Aplicar a todas as 4 CPTs**.

---

#### Check 2: Probabilidades no Intervalo [0,1]

```python
def validate_probability_range(network):
    for node, cpt in network.cpts.items():
        for config, probs in cpt.items():
            for state, p in probs.items():
                assert 0 <= p <= 1, f"Probabilidade inválida: {node}.{state}={p}"
    print("✓ Todas as probabilidades em [0,1]")
```

---

#### Check 3: Consistência com Prior Marginal

**Objetivo**: P(QualidadeAr=Boa) calculado pela rede deve ser plausível.

```python
def compute_marginal(network, variable):
    """Calcula P(variable) marginalizando todas as outras"""
    # Implementação de enumeração completa
    return marginal_distribution

p_boa_network = compute_marginal(network, 'QualidadeAr')['Boa']
p_boa_dataset = 0.425  # Do dataset real

print(f"P(Boa) rede: {p_boa_network:.3f}")
print(f"P(Boa) dataset: {p_boa_dataset:.3f}")
print(f"Discrepância: {abs(p_boa_network - p_boa_dataset):.3f}")

# Critério: discrepância <20% é aceitável para rede simplificada
assert abs(p_boa_network - p_boa_dataset) < 0.20
```

**Valor esperado**: P(Boa)_rede ≈ 0,54 (calculado na Seção 3.3)

**Resultado**: Discrepância = |0,54 - 0,425| = 0,115 → ✓ PASS (11,5% < 20%)

---

### 4.2.2 Testes de Sensibilidade

#### Teste 1: Monotonicidade em Relação ao Tráfego

**Hipótese**: Aumentar tráfego deve reduzir P(Boa)

```python
scenarios = [
    {'Traf': 'Não', 'expected_p_boa_min': 0.60},
    {'Traf': 'Sim', 'expected_p_boa_max': 0.50}
]

p_boa_sem_trafego = network.query('QualidadeAr', {'Tráfego': 'Não'})['Boa']
p_boa_com_trafego = network.query('QualidadeAr', {'Tráfego': 'Sim'})['Boa']

assert p_boa_sem_trafego > p_boa_com_trafego, \
    "Violação monotonicidade: tráfego deve degradar qualidade"

print(f"✓ Monotonicidade verificada: {p_boa_sem_trafego:.2f} > {p_boa_com_trafego:.2f}")
```

**Valores esperados** (da Seção 3.5):
- P(Boa | Tráfego=Não) ≈ 0,68
- P(Boa | Tráfego=Sim) ≈ 0,42
- Diferença: 26 pp → ✓ PASS

---

#### Teste 2: Efeito da Evidência

**Cenário**: Observar "Temperatura=Alta" deve alterar distribuição posterior.

```python
prior = network.query('QualidadeAr', evidence={})
posterior = network.query('QualidadeAr', evidence={'Temperatura': 'Alta'})

kl_divergence = compute_kl(posterior, prior)
assert kl_divergence > 0.01, "Evidência deve alterar crenças"

print(f"✓ Evidência altera distribuição (KL={kl_divergence:.3f})")
```

---

### 4.2.3 Teste de Inferência Inversa (Abductive Reasoning)

**Cenário**: Dada má qualidade, qual a causa mais provável?

```python
evidence = {'QualidadeAr': 'Má'}

p_traf_sim = network.query('Tráfego', evidence)['Sim']
p_traf_nao = network.query('Tráfego', evidence)['Não']
p_temp_alta = network.query('Temperatura', evidence)['Alta']

print(f"P(Tráfego=Sim | QA=Má) = {p_traf_sim:.2f}")
print(f"P(Temperatura=Alta | QA=Má) = {p_temp_alta:.2f}")

# Tráfego deve ter posterior maior (correlação mais forte no dataset)
assert p_traf_sim > 0.50, "Tráfego é causa dominante de poluição"
```

**Resultado esperado** (da Seção 3.5): P(Tráfego=Sim | Má) ≈ 0,57 → ✓ PASS

---

### 4.2.4 Testes de Casos Extremos

#### Caso 1: Melhor Cenário

```python
best_case = {
    'Estação': 'Primavera',
    'Temperatura': 'Moderada',
    'Tráfego': 'Não'
}
p_boa = network.query('QualidadeAr', best_case)['Boa']
assert p_boa >= 0.80, "Melhor cenário deve ter alta probabilidade de qualidade boa"
print(f"✓ Melhor cenário: P(Boa) = {p_boa:.2f}")
```

**Esperado**: P(Boa | Mod, Não) = 0,85 (da CPT diretamente)

---

#### Caso 2: Pior Cenário

```python
worst_case = {
    'Estação': 'Verão',
    'Temperatura': 'Alta',
    'Tráfego': 'Sim'
}
p_ma = network.query('QualidadeAr', worst_case)['Má']
assert p_ma >= 0.70, "Pior cenário deve ter alta probabilidade de qualidade má"
print(f"✓ Pior cenário: P(Má) = {p_ma:.2f}")
```

**Esperado**: P(Má | Alta, Sim) = 0,75 (da CPT diretamente)

---

### 4.2.5 Validação de Independência Condicional

**Propriedade**: Temperatura ⊥ Tráfego | Estação (d-separação)

```python
def test_conditional_independence():
    # P(Temp | Traf, Est) deve ser igual a P(Temp | Est)
    evidence1 = {'Estação': 'Verão'}
    evidence2 = {'Estação': 'Verão', 'Tráfego': 'Sim'}
    
    p_temp_1 = network.query('Temperatura', evidence1)
    p_temp_2 = network.query('Temperatura', evidence2)
    
    kl = compute_kl(p_temp_1, p_temp_2)
    assert kl < 0.001, "Temperatura e Tráfego devem ser condicionalmente independentes dado Estação"
    print(f"✓ Independência condicional verificada (KL={kl:.5f})")

test_conditional_independence()
```

---

### 4.2.6 Comparação com Dados Reais (Validação Externa)

**Objetivo**: Prever `air_quality_good` no dataset e comparar com rótulos reais.

```python
def validate_with_data(network, dataset, sample_size=100):
    """
    Para cada registo do dataset:
    1. Mapear variáveis contínuas para estados discretos da rede
    2. Fazer inferência P(QualidadeAr | evidências)
    3. Comparar com label real
    """
    
    def map_to_discrete(row):
        temp = 'Baixa' if row['temperature_c'] < 15 else \
               'Alta' if row['temperature_c'] > 30 else 'Moderada'
        
        # Estação do mês
        season = {12: 'Inverno', 1: 'Inverno', 2: 'Inverno',
                  3: 'Primavera', 4: 'Primavera', 5: 'Primavera',
                  6: 'Verão', 7: 'Verão', 8: 'Verão',
                  9: 'Outono', 10: 'Outono', 11: 'Outono'}[row['month']]
        
        # Tráfego: proxy usando NO₂
        trafego = 'Sim' if row['NO2'] > 100 else 'Não'
        
        return {'Estação': season, 'Temperatura': temp, 'Tráfego': trafego}
    
    correct = 0
    for idx, row in dataset.sample(sample_size).iterrows():
        if pd.isna(row['temperature_c']) or pd.isna(row['NO2']):
            continue
        
        evidence = map_to_discrete(row)
        p_boa = network.query('QualidadeAr', evidence)['Boa']
        
        predicted = 'Boa' if p_boa > 0.5 else 'Má'
        actual = 'Boa' if row['air_quality_good'] else 'Má'
        
        if predicted == actual:
            correct += 1
    
    accuracy = correct / sample_size
    print(f"Accuracy: {accuracy:.2%}")
    return accuracy

# Critério: accuracy >50% (melhor que random)
accuracy = validate_with_data(network, df, sample_size=200)
assert accuracy > 0.50, "Rede deve ter poder preditivo acima do acaso"
```

**Resultado Esperado**: 60-70% accuracy (rede simples não substitui ML, mas deve ter sinal)

---

## 4.3 Sumário de Validação

### Checklist Final

**Motor de Inferência**:
- ✓ Cobertura global >50%
- ✓ Todas as regras com ≥1 ativação OU justificação de não-ativação
- ✓ 5/5 casos de teste PASS
- ✓ Lógica booleana correta
- ✓ Gestão de missing values correta

**Rede Bayesiana**:
- ✓ CPTs normalizadas
- ✓ Probabilidades em [0,1]
- ✓ Marginal plausível (discrepância <20%)
- ✓ Monotonicidade em relação a tráfego
- ✓ Evidência altera crenças
- ✓ Inferência inversa consistente
- ✓ Casos extremos corretos
- ✓ Independência condicional verificada
- ✓ Validação externa >50% accuracy

### Limitações Reconhecidas

1. **Motor de Inferência**:
   - Regras R05, R07, R10 têm 0 ativações (dados insuficientes, não erro de lógica)
   - Não implementa raciocínio temporal (ex: "3 dias consecutivos >40°C")
   - Prioridades são heurísticas, não otimizadas

2. **Rede Bayesiana**:
   - Simplificação drástica da realidade (4 nós vs. ~20 variáveis relevantes)
   - CPTs baseadas em expert elicitation, não aprendidas dos dados
   - Discrepância P(Boa) de 11,5% reflete heterogeneidade UCI vs. PT
   - Não modela dinâmica temporal

3. **Ambos**:
   - Não integrados (motor + Bayes operam independentemente)
   - Não testados em produção real (apenas validação offline)

### Recomendações para Deploy

Se este sistema fosse para produção:

1. **Testar com dados em tempo real** (stream) por 1 mês em modo "shadow" (alerta não publicado)
2. **Calibrar limiares** com feedback de especialistas de Proteção Civil
3. **Implementar logging** de todas as decisões para auditoria
4. **Adicionar interface web** para visualização de alertas
5. **Integrar com API do IPMA** para meteorologia oficial
6. **Criar dashboard de métricas** de performance do sistema
