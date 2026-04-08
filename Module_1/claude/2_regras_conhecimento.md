# 2. REGRAS DE CONHECIMENTO - SISTEMA BASEADO EM REGRAS

## 2.1 Fundamentação Teórica

### Lógica de Predicados de Primeira Ordem

O sistema de regras baseia-se em **cláusulas de Horn** do tipo:

```
antecedente₁ ∧ antecedente₂ ∧ ... ∧ antecedenteₙ → consequente
```

Onde:
- **Antecedentes**: condições sobre variáveis ambientais (temperatura, poluentes)
- **Consequente**: ação recomendada ou classificação de risco
- **Conectivo lógico**: conjunção (∧) - todas as condições devem ser verdadeiras

### Modelo de Risco em Quatro Níveis

Seguindo a metodologia da **European Environment Agency (EEA)** e **IPMA**:

| Nível | Código | Cor | Descrição | Ação Típica |
|-------|--------|-----|-----------|-------------|
| 0 | `NORMAL` | Verde | Sem risco | Monitorização de rotina |
| 1 | `BAIXO` | Amarelo | Risco limitado | Alerta preventivo |
| 2 | `MODERADO` | Laranja | Risco significativo | Ação recomendada |
| 3 | `ALTO` | Vermelho | Risco grave | Ação obrigatória |

---

## 2.2 Definição das 12 Regras

### GRUPO A: Qualidade do Ar - Poluentes Primários

#### **REGRA 1: NO₂ - Risco de Tráfego Alto**

**Formato Lógico**:
```prolog
∀x ( NO2(x) ≥ 200 μg/m³ → AlertaNO2Alto(x) )
```

**Formato SE-ENTÃO**:
```
SE NO2 ≥ 200 μg/m³
ENTÃO classificar como RISCO_ALTO
     E recomendar "Limitar tráfego automóvel. Grupos sensíveis evitem exposição prolongada."
```

**Objetivo**: Detetar violações do limite horário de NO₂ estabelecido pela UE.

**Limiar**: 200 μg/m³ (horário)

**Racional**:
- NO₂ é indicador primário de poluição por tráfego automóvel
- Exposições >200 μg/m³ causam inflamação das vias respiratórias
- Grupos vulneráveis: crianças, idosos, asmáticos

**Fonte Normativa**: 
- Diretiva 2008/50/CE, Anexo XI: limite horário 200 μg/m³ (não exceder >18h/ano)
- WHO Air Quality Guidelines 2021: 25 μg/m³ (média anual) - mais restritivo

**Tipo de Média Temporal**: Horária (1h)

**Aplicabilidade no Dataset**: 
- Aplicável a 84,5% dos registos (9.157 registos com NO₂ válido)
- Valor máximo observado: 340 μg/m³ (UCI_Dataset)
- P95 = 194 μg/m³ → regra dispara em ~5% dos casos

**Limitação**: 
- Limite horário UE permite 18 excedências/ano - nossa regra não tem contexto anual
- Recomendação: implementar contador de excedências por ano para conformidade completa

---

#### **REGRA 2: NO₂ - Risco Moderado**

**Formato Lógico**:
```prolog
∀x ( NO2(x) ≥ 100 ∧ NO2(x) < 200 → AlertaNO2Moderado(x) )
```

**Formato SE-ENTÃO**:
```
SE NO2 ≥ 100 μg/m³ E NO2 < 200 μg/m³
ENTÃO classificar como RISCO_MODERADO
     E recomendar "Monitorizar evolução. Sensíveis reduzam atividade ao ar livre."
```

**Objetivo**: Alerta preventivo antes de atingir limite legal.

**Limiar**: 100-200 μg/m³ (50% do limite horário)

**Racional**: Sistema de alerta antecipado permite intervenção antes de violação.

**Fonte Normativa**: 
- IPMA: amarelo a 50% do limiar vermelho
- Princípio de precaução (Tratado UE, art. 191)

**Tipo de Média Temporal**: Horária (1h)

**Aplicabilidade**: ~15-20% dos registos (intervalo P50-P95)

**Limitação**: Limiar arbitrário (50%) sem base epidemiológica direta.

---

#### **REGRA 3: PM₁₀ - Partículas Inaláveis**

**Formato Lógico**:
```prolog
∀x ( PM10(x) ≥ 50 μg/m³ → AlertaPM10Alto(x) )
```

**Formato SE-ENTÃO**:
```
SE PM10 ≥ 50 μg/m³
ENTÃO classificar como RISCO_ALTO
     E recomendar "Evitar exercício ao ar livre. Fechar janelas em ambientes internos."
```

**Objetivo**: Conformidade com limite diário de PM₁₀.

**Limiar**: 50 μg/m³ (24h, mas aplicado horário por precaução)

**Racional**:
- PM₁₀ penetra vias respiratórias superiores
- Associado a mortalidade cardiovascular e respiratória (+0,6% por 10 μg/m³)
- Fontes: tráfego, construção, poeiras do Saara (PT)

**Fonte Normativa**: 
- Diretiva 2008/50/CE: 50 μg/m³ (média 24h, máx 35 excedências/ano)
- WHO 2021: 45 μg/m³ (24h) - limite mais restritivo

**Tipo de Média Temporal**: 
- **NOTA CRÍTICA**: Limite é 24h, mas dados são horários
- **Solução implementada**: aplicar limite horário (conservador) OU calcular média móvel 24h

**Aplicabilidade**: 
- Apenas Lisboa/Porto (1.442 registos, 13,4%)
- Máximo observado: 58,57 μg/m³
- P95 = 39,11 μg/m³ → poucos disparos esperados

**Limitação**: 
- Aplicação de limite 24h a dados horários é **ultra-conservadora**
- Recomendação: calcular `PM10_24h_avg = rolling(24h).mean()` para precisão

---

#### **REGRA 4: PM₂.₅ - Partículas Finas**

**Formato Lógico**:
```prolog
∀x ( PM2_5(x) ≥ 25 μg/m³ → AlertaPM25Alto(x) )
```

**Formato SE-ENTÃO**:
```
SE PM2.5 ≥ 25 μg/m³
ENTÃO classificar como RISCO_ALTO
     E recomendar "Grupos sensíveis permaneçam em ambientes internos. Usar máscara FFP2 se necessário."
```

**Objetivo**: Proteger contra partículas ultrafinas (diâmetro <2,5 μm).

**Limiar**: 25 μg/m³ (anual UE, mas aplicado horário)

**Racional**:
- PM₂.₅ atravessa alvéolos pulmonares, entra na corrente sanguínea
- **Mais perigoso que PM₁₀**: associação com cancro do pulmão, AVC, Alzheimer
- Sem limiar seguro conhecido ("no safe threshold" - WHO)

**Fonte Normativa**: 
- Diretiva 2008/50/CE: 25 μg/m³ (média anual)
- WHO 2021: **5 μg/m³** (média anual) - 5× mais restritivo!
- WHO 2021: 15 μg/m³ (24h)

**Tipo de Média Temporal**: 
- Limite UE é **anual**, não horário
- Limite WHO (15 μg/m³) é mais apropriado para alertas curto prazo

**Aplicabilidade**: Lisboa/Porto apenas (13,4%)

**Limitação**: 
- Usar limite anual (25) para alertas horários é **metodologicamente questionável**
- Solução: usar 15 μg/m³ (limite 24h WHO) seria mais defensável
- **DECISÃO FINAL**: manter 25 μg/m³ para conformidade UE, mas documentar limitação

---

#### **REGRA 5: O₃ - Ozono Troposférico**

**Formato Lógico**:
```prolog
∀x ( O3(x) ≥ 180 μg/m³ → AlertaO3Alto(x) )
```

**Formato SE-ENTÃO**:
```
SE O3 ≥ 180 μg/m³
ENTÃO classificar como RISCO_ALTO
     E recomendar "Limiar de informação excedido. Evitar atividade física intensa ao ar livre 14-20h."
```

**Objetivo**: Alertar para níveis perigosos de ozono (formado por reação fotoquímica).

**Limiar**: 180 μg/m³ (horário)

**Racional**:
- O₃ causa irritação respiratória, reduz função pulmonar
- Pico no verão, horas de maior insolação (14-20h)
- Paradoxo: alta poluição (NO) reduz O₃ (reação química)

**Fonte Normativa**: 
- Diretiva 2008/50/CE: 180 μg/m³ (limiar informação, horário)
- 240 μg/m³ (limiar alerta)
- Valor-alvo: 120 μg/m³ (média 8h, máx 25 dias/ano média 3 anos)

**Tipo de Média Temporal**: Horária (1h) para limiar informação

**Aplicabilidade**: Lisboa/Porto (13,4%)

**Limitação**: 
- Dataset tem P99 = 107,95 μg/m³ → **regra pode nunca disparar** nos dados atuais
- Considerar adicionar regra a 120 μg/m³ (valor-alvo 8h)

---

#### **REGRA 6: CO - Monóxido de Carbono**

**Formato Lógico**:
```prolog
∀x ( CO_8h_avg(x) ≥ 10 mg/m³ → AlertaCOAlto(x) )
```

**Formato SE-ENTÃO**:
```
SE CO (média móvel 8h) ≥ 10 mg/m³
ENTÃO classificar como RISCO_ALTO
     E recomendar "Nível crítico de CO. Evitar túneis e vias de tráfego intenso. Ventilar ambientes."
```

**Objetivo**: Proteger contra intoxicação por monóxido de carbono.

**Limiar**: 10 mg/m³ (média 8h)

**Racional**:
- CO reduz capacidade de transporte de oxigénio no sangue (liga-se hemoglobina)
- Exposição prolongada → cefaleia, náusea, perda de consciência
- Fonte: combustão incompleta (tráfego, aquecimento)

**Fonte Normativa**: 
- Diretiva 2008/50/CE: 10 mg/m³ (máxima média diária de 8h)
- WHO 2021: 4 mg/m³ (24h) - mais restritivo

**Tipo de Média Temporal**: **Média móvel 8 horas**

**Aplicabilidade**: 
- 84,7% do dataset (principalmente UCI_Dataset)
- **REQUER PRÉ-PROCESSAMENTO**: calcular média móvel 8h

**Limitação**: 
- Missing CO (15,3%) → algumas janelas 8h incompletas
- Solução: `rolling(8, min_periods=6)` - aceitar 6/8 valores

---

#### **REGRA 7: SO₂ - Dióxido de Enxofre**

**Formato Lógico**:
```prolog
∀x ( SO2(x) ≥ 350 μg/m³ → AlertaSO2Alto(x) )
```

**Formato SE-ENTÃO**:
```
SE SO2 ≥ 350 μg/m³
ENTÃO classificar como RISCO_ALTO
     E recomendar "Nível crítico SO₂. Asmáticos evitem exposição. Investigar fonte de emissão."
```

**Objetivo**: Detetar emissões industriais ou combustão de combustíveis fósseis.

**Limiar**: 350 μg/m³ (horário)

**Racional**:
- SO₂ causa broncoconstrição (espasmo brônquios) em minutos
- Especialmente perigoso para asmáticos
- Fonte: centrais térmicas, indústria pesada

**Fonte Normativa**: 
- Diretiva 2008/50/CE: 350 μg/m³ (horário, máx 24 excedências/ano)
- 125 μg/m³ (24h, máx 3 excedências/ano)

**Tipo de Média Temporal**: Horária (1h)

**Aplicabilidade**: Lisboa/Porto (13,4%)

**Limitação**: 
- Máximo observado: 18,36 μg/m³ → **regra nunca dispara** no dataset atual
- SO₂ em forte declínio na Europa (dessulfurização de combustíveis)
- **QUESTÃO**: manter regra por completude normativa ou remover por irrelevância prática?
- **DECISÃO**: manter, mas documentar como "salvaguarda histórica"

---

### GRUPO B: Riscos Meteorológicos

#### **REGRA 8: Onda de Calor Extremo**

**Formato Lógico**:
```prolog
∀x ( temperature(x) ≥ 40°C → AlertaCalorExtremo(x) )
```

**Formato SE-ENTÃO**:
```
SE temperatura ≥ 40°C
ENTÃO classificar como RISCO_ALTO
     E recomendar "Alerta vermelho calor. Ativar Plano de Contingência. Populações vulneráveis em risco."
```

**Objetivo**: Proteger saúde pública durante ondas de calor.

**Limiar**: 40°C

**Racional**:
- Risco de exaustão térmica e golpe de calor (hipertermia)
- Mortalidade aumenta exponencialmente >35°C (sobretudo >65 anos)
- Exemplo histórico: onda de calor 2003 (Europa, 70.000 mortes)

**Fonte Normativa**: 
- IPMA: alerta vermelho temperatura >40°C
- DGS: Plano de Contingência Temperaturas Extremas Adversas

**Tipo de Média Temporal**: Instantânea (horária)

**Aplicabilidade**: 
- 96,9% do dataset (boa cobertura)
- Máximo observado: 44,6°C → **regra dispara** em casos extremos
- P99 = 38,9°C → ~1% dos dados

**Limitação**: 
- Não considera **duração** da onda de calor (IPMA: >5 dias consecutivos >5°C acima normal)
- Não usa heat index (sensação térmica considerando humidade)

---

#### **REGRA 9: Risco de Incêndio (Temperatura + Humidade)**

**Formato Lógico**:
```prolog
∀x ( temperature(x) ≥ 35°C ∧ humidity(x) ≤ 30% → AlertaIncendioAlto(x) )
```

**Formato SE-ENTÃO**:
```
SE temperatura ≥ 35°C E humidade ≤ 30%
ENTÃO classificar como RISCO_ALTO
     E recomendar "Risco máximo incêndio florestal. Proibir queimadas. Vigilância reforçada."
```

**Objetivo**: Prever condições propícias a incêndios florestais.

**Limiares**: 
- Temperatura: 35°C
- Humidade relativa: ≤30%

**Racional**:
- Combinação calor + baixa humidade → vegetação desidratada (combustível)
- Regra inspira-se no **Canadian Forest Fire Weather Index (FWI)**
- Portugal: 95% dos grandes incêndios ocorrem com T>30°C e HR<40%

**Fonte Normativa**: 
- IPMA: Índice FWI (Fire Weather Index) - mais complexo que esta regra
- Sistema Nacional de Defesa da Floresta contra Incêndios (DECIR 03/2019)

**Tipo de Média Temporal**: Horária (condições instantâneas)

**Aplicabilidade**: 
- 96,9% do dataset (T e HR disponíveis)
- Condição rara: T>35°C ocorre em <5% dos dados; HR<30% também rara
- **Probabilidade de conjunção**: ~1-2% dos registos

**Limitação**: 
- FWI real considera vento, precipitação acumulada, tipo de vegetação
- Esta regra é **simplificação drástica** - útil como alerta, mas não substitui FWI oficial

---

#### **REGRA 10: Vento Forte**

**Formato Lógico**:
```prolog
∀x ( wind_speed(x) ≥ 75 km/h → AlertaVentoForte(x) )
```

**Formato SE-ENTÃO**:
```
SE velocidade do vento ≥ 75 km/h
ENTÃO classificar como RISCO_ALTO
     E recomendar "Alerta laranja vento. Risco de queda de árvores e estruturas. Evitar deslocações."
```

**Objetivo**: Alertar para ventos destrutivos (rajadas).

**Limiar**: 75 km/h (rajadas)

**Racional**:
- Ventos >75 km/h derrubam árvores, danificam telhados
- Agrava propagação de incêndios florestais (regra combinada possível)

**Fonte Normativa**: 
- IPMA: laranja 75-90 km/h, vermelho >90 km/h
- Escala Beaufort: força 9 (75-88 km/h) = "strong gale"

**Tipo de Média Temporal**: Rajada (máximo horário ideal; usamos média)

**Aplicabilidade**: 
- Apenas Lisboa/Porto (13,4%)
- **PROBLEMA**: dataset tem `wind_speed_kmh` mas não rajadas
- Máximo observado: 28 km/h → **regra nunca dispara**

**Limitação**: 
- Dados disponíveis são **velocidade média**, não rajadas (que são 30-50% superiores)
- **DECISÃO**: manter regra para completude, mas esperar 0 ativações no dataset atual
- Alternativa: baixar limiar para 40 km/h (vento moderado-forte) se quisermos ativações

---

#### **REGRA 11: Precipitação Intensa**

**Formato Lógico**:
```prolog
∀x ( precipitation(x) ≥ 10 mm/h → AlertaPrecipitacaoIntensa(x) )
```

**Formato SE-ENTÃO**:
```
SE precipitação ≥ 10 mm/hora
ENTÃO classificar como RISCO_MODERADO
     E recomendar "Precipitação intensa. Risco de inundações em zonas baixas. Evitar viajar."
```

**Objetivo**: Alertar para chuvas torrenciais (risco de cheias).

**Limiar**: 10 mm/h

**Racional**:
- Precipitação >10 mm/h sobrecarrega sistemas de drenagem urbana
- Causa inundações rápidas ("flash floods") em bacias pequenas

**Fonte Normativa**: 
- IPMA: amarelo 10-30 mm/h, laranja 30-60 mm/h, vermelho >60 mm/h
- OMM: >7,6 mm/h = "heavy rain"

**Tipo de Média Temporal**: Horária (acumulação 1h)

**Aplicabilidade**: 
- Lisboa/Porto (13,4%)
- Máximo: 15,6 mm → **regra dispara ocasionalmente**
- P99 = 0,56 mm → precipitação é evento raro no dataset

**Limitação**: 
- Precipitação é **variável espacialmente heterogénea** (célula convectiva <10 km)
- 1 estação pode não captar evento localizado

---

### GRUPO C: Regras Compostas (Risco Sinérgico)

#### **REGRA 12: Qualidade do Ar Péssima (Múltiplos Poluentes)**

**Formato Lógico**:
```prolog
∀x ( (NO2(x) ≥ 150 ∨ PM10(x) ≥ 40 ∨ PM2_5(x) ≥ 20) ∧ humidity(x) ≥ 80% 
     → AlertaQualidadeArPessima(x) )
```

**Formato SE-ENTÃO**:
```
SE (NO2 ≥ 150 μg/m³ OU PM10 ≥ 40 μg/m³ OU PM2.5 ≥ 20 μg/m³)
   E humidade ≥ 80%
ENTÃO classificar como RISCO_ALTO
     E recomendar "Qualidade do ar muito degradada agravada por humidade alta. Grupos de risco evitem saídas."
```

**Objetivo**: Detetar episódios de poluição multi-poluente agravados por inversão térmica/estagnação.

**Limiares**: 
- NO₂: 150 μg/m³ (75% do limite)
- PM₁₀: 40 μg/m³ (80% do limite 24h)
- PM₂.₅: 20 μg/m³ (80% do limite anual UE)
- Humidade: ≥80% (indicador de estagnação atmosférica)

**Racional**:
- Humidade alta + ausência de vento → acumulação de poluentes
- Condições típicas de inversão térmica (inverno, madrugada)
- Efeito sinérgico: múltiplos poluentes elevados simultaneamente

**Fonte Normativa**: 
- Conceito de "episódio de poluição" (Diretiva 2008/50/CE, art. 24)
- Air Quality Index (AQI) da EEA

**Tipo de Média Temporal**: Horária (condições instantâneas)

**Aplicabilidade**: 
- Requer NO₂ OU PM10/PM2.5 + humidade
- Lisboa/Porto: pode avaliar todos os poluentes (13,4%)
- UCI_Dataset: apenas NO₂ + humidade (84,5%)

**Limitação**: 
- Disjunção (∨) dificulta interpretação causal específica
- Limiar humidade (80%) é **heurístico**, não baseado em estudo específico
- Não substitui AQI oficial (que pondera poluentes diferentemente)

---

## 2.3 Ficheiro JSON - Base de Conhecimento

```json
{
  "rules": [
    {
      "id": "R01_NO2_ALTO",
      "description": "Alerta NO₂ crítico - limite horário UE",
      "condition": {
        "type": "simple_threshold",
        "variable": "NO2",
        "operator": ">=",
        "threshold": 200,
        "unit": "μg/m³"
      },
      "consequence": {
        "risk_level": "ALTO",
        "action": "Limitar tráfego automóvel. Grupos sensíveis evitem exposição prolongada.",
        "rationale": "Violação limite horário Diretiva 2008/50/CE",
        "source": "Diretiva 2008/50/CE, Anexo XI"
      }
    },
    {
      "id": "R02_NO2_MODERADO",
      "description": "Alerta NO₂ preventivo",
      "condition": {
        "type": "range",
        "variable": "NO2",
        "min": 100,
        "max": 200,
        "unit": "μg/m³"
      },
      "consequence": {
        "risk_level": "MODERADO",
        "action": "Monitorizar evolução. Sensíveis reduzam atividade ao ar livre.",
        "rationale": "50% do limite horário - alerta antecipado",
        "source": "Princípio de precaução (IPMA)"
      }
    },
    {
      "id": "R03_PM10_ALTO",
      "description": "Partículas inaláveis PM₁₀ excedem limite 24h",
      "condition": {
        "type": "simple_threshold",
        "variable": "PM10",
        "operator": ">=",
        "threshold": 50,
        "unit": "μg/m³",
        "note": "Limite é 24h, aplicado conservadoramente a dados horários"
      },
      "consequence": {
        "risk_level": "ALTO",
        "action": "Evitar exercício ao ar livre. Fechar janelas em ambientes internos.",
        "rationale": "Partículas inaláveis afetam vias respiratórias",
        "source": "Diretiva 2008/50/CE (50 μg/m³, 24h)"
      }
    },
    {
      "id": "R04_PM25_ALTO",
      "description": "Partículas finas PM₂.₅ excedem limite anual UE",
      "condition": {
        "type": "simple_threshold",
        "variable": "PM2_5",
        "operator": ">=",
        "threshold": 25,
        "unit": "μg/m³",
        "note": "Limite anual aplicado a dados horários por precaução"
      },
      "consequence": {
        "risk_level": "ALTO",
        "action": "Grupos sensíveis permaneçam em ambientes internos. Usar máscara FFP2 se necessário.",
        "rationale": "Partículas ultrafinas atravessam alvéolos pulmonares",
        "source": "Diretiva 2008/50/CE (25 μg/m³, anual); WHO 2021 (15 μg/m³, 24h)"
      }
    },
    {
      "id": "R05_O3_ALTO",
      "description": "Ozono troposférico - limiar de informação",
      "condition": {
        "type": "simple_threshold",
        "variable": "O3",
        "operator": ">=",
        "threshold": 180,
        "unit": "μg/m³"
      },
      "consequence": {
        "risk_level": "ALTO",
        "action": "Limiar de informação excedido. Evitar atividade física intensa ao ar livre 14-20h.",
        "rationale": "O₃ causa irritação respiratória; pico fotoquímico diurno",
        "source": "Diretiva 2008/50/CE, art. 18 (180 μg/m³, limiar informação)"
      }
    },
    {
      "id": "R06_CO_ALTO",
      "description": "Monóxido de carbono - média 8h crítica",
      "condition": {
        "type": "simple_threshold",
        "variable": "CO_8h_avg",
        "operator": ">=",
        "threshold": 10,
        "unit": "mg/m³",
        "preprocessing": "Calcular média móvel 8h antes de avaliar"
      },
      "consequence": {
        "risk_level": "ALTO",
        "action": "Nível crítico de CO. Evitar túneis e vias de tráfego intenso. Ventilar ambientes.",
        "rationale": "CO liga-se hemoglobina, reduz transporte de O₂",
        "source": "Diretiva 2008/50/CE (10 mg/m³, máxima média diária 8h)"
      }
    },
    {
      "id": "R07_SO2_ALTO",
      "description": "Dióxido de enxofre - limite horário",
      "condition": {
        "type": "simple_threshold",
        "variable": "SO2",
        "operator": ">=",
        "threshold": 350,
        "unit": "μg/m³"
      },
      "consequence": {
        "risk_level": "ALTO",
        "action": "Nível crítico SO₂. Asmáticos evitem exposição. Investigar fonte de emissão.",
        "rationale": "SO₂ causa broncoconstrição aguda (minutos)",
        "source": "Diretiva 2008/50/CE (350 μg/m³, horário)"
      }
    },
    {
      "id": "R08_CALOR_EXTREMO",
      "description": "Onda de calor extremo",
      "condition": {
        "type": "simple_threshold",
        "variable": "temperature_c",
        "operator": ">=",
        "threshold": 40,
        "unit": "°C"
      },
      "consequence": {
        "risk_level": "ALTO",
        "action": "Alerta vermelho calor. Ativar Plano de Contingência. Populações vulneráveis em risco.",
        "rationale": "Risco de exaustão térmica e golpe de calor",
        "source": "IPMA (vermelho >40°C); DGS Plano Contingência Temperaturas Extremas"
      }
    },
    {
      "id": "R09_RISCO_INCENDIO",
      "description": "Risco máximo de incêndio florestal",
      "condition": {
        "type": "compound_and",
        "conditions": [
          {"variable": "temperature_c", "operator": ">=", "value": 35},
          {"variable": "humidity_percent", "operator": "<=", "value": 30}
        ]
      },
      "consequence": {
        "risk_level": "ALTO",
        "action": "Risco máximo incêndio florestal. Proibir queimadas. Vigilância reforçada.",
        "rationale": "Calor + baixa humidade = vegetação desidratada (combustível)",
        "source": "IPMA Índice FWI (simplificado); DECIR 03/2019"
      }
    },
    {
      "id": "R10_VENTO_FORTE",
      "description": "Vento forte - alerta laranja",
      "condition": {
        "type": "simple_threshold",
        "variable": "wind_speed_kmh",
        "operator": ">=",
        "threshold": 75,
        "unit": "km/h",
        "note": "Ideal seria usar rajadas, não velocidade média"
      },
      "consequence": {
        "risk_level": "ALTO",
        "action": "Alerta laranja vento. Risco de queda de árvores e estruturas. Evitar deslocações.",
        "rationale": "Ventos destrutivos (Beaufort força 9)",
        "source": "IPMA (laranja 75-90 km/h); Escala Beaufort"
      }
    },
    {
      "id": "R11_PRECIPITACAO_INTENSA",
      "description": "Precipitação horária intensa",
      "condition": {
        "type": "simple_threshold",
        "variable": "precipitation_mm",
        "operator": ">=",
        "threshold": 10,
        "unit": "mm/h"
      },
      "consequence": {
        "risk_level": "MODERADO",
        "action": "Precipitação intensa. Risco de inundações em zonas baixas. Evitar viajar.",
        "rationale": "Sobrecarga sistemas drenagem; flash floods",
        "source": "IPMA (amarelo 10-30 mm/h); OMM (>7,6 mm/h = heavy rain)"
      }
    },
    {
      "id": "R12_QUALIDADE_AR_PESSIMA",
      "description": "Episódio de poluição multi-poluente com estagnação",
      "condition": {
        "type": "compound_and",
        "conditions": [
          {
            "type": "compound_or",
            "conditions": [
              {"variable": "NO2", "operator": ">=", "value": 150},
              {"variable": "PM10", "operator": ">=", "value": 40},
              {"variable": "PM2_5", "operator": ">=", "value": 20}
            ]
          },
          {"variable": "humidity_percent", "operator": ">=", "value": 80}
        ]
      },
      "consequence": {
        "risk_level": "ALTO",
        "action": "Qualidade do ar muito degradada agravada por humidade alta. Grupos de risco evitem saídas.",
        "rationale": "Múltiplos poluentes + estagnação atmosférica (inversão térmica)",
        "source": "Diretiva 2008/50/CE art. 24 (episódios poluição); conceito EEA AQI"
      }
    }
  ],
  "metadata": {
    "version": "1.0",
    "date": "2026-04-08",
    "author": "Equipa Projeto IA Cidades Sustentáveis",
    "total_rules": 12,
    "rule_categories": {
      "air_quality": 7,
      "meteorological": 4,
      "compound": 1
    },
    "notes": "Regras baseadas em Diretiva 2008/50/CE (UE), IPMA, WHO Guidelines 2021, DGS Portugal"
  }
}
```

---

## 2.4 Sumário: Regras vs. Cobertura de Dados

| Regra | Variáveis | Cobertura Dataset | Disparos Esperados | Notas |
|-------|-----------|-------------------|-------------------|-------|
| R01 | NO₂ | 84,5% | ~5% (P95=194) | ✅ Alta aplicabilidade |
| R02 | NO₂ | 84,5% | ~15-20% | ✅ Preventivo funcional |
| R03 | PM₁₀ | 13,4% | <5% (P95=39) | ⚠️ Limite 24h em dados 1h |
| R04 | PM₂.₅ | 13,4% | Raro (P95=28) | ⚠️ Limite anual em dados 1h |
| R05 | O₃ | 13,4% | 0% (max=115) | ⚠️ Pode nunca disparar |
| R06 | CO (8h avg) | 84,7% | <1% (P99=6,6) | ✅ Requer preprocessamento |
| R07 | SO₂ | 13,4% | 0% (max=18) | ⚠️ Salvaguarda histórica |
| R08 | Temperatura | 96,9% | ~1% (P99=38,9) | ✅ Eventos raros críticos |
| R09 | T + RH | 96,9% | ~1-2% | ✅ Regra composta funcional |
| R10 | Vento | 13,4% | 0% (max=28) | ❌ Dados inadequados (média vs. rajada) |
| R11 | Precipitação | 13,4% | <1% (P99=0,56) | ✅ Eventos raros |
| R12 | Multi-poluente + RH | 13,4%/84,5% | ~5-10% | ✅ Sinergias realistas |

**Conclusão**: 8/12 regras têm aplicabilidade prática no dataset; 4 regras (R05, R07, R10, partes de R03/R04) são teoricamente corretas mas com baixa/nula ativação nos dados atuais. Isto é **esperado e aceitável** num sistema de alertas de emergência (eventos extremos são raros por definição).
