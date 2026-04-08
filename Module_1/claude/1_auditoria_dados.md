# 1. AUDITORIA DE DADOS - MÓDULO 1

## 1.1 Identificação de Subdatasets e Fontes

O dataset `processed_lisboa_porto_air_quality.csv` contém **10.768 registos** de três fontes distintas:

### Composição do Dataset

| Fonte | Registos | Período | Características |
|-------|----------|---------|-----------------|
| **UCI_Dataset** | 9.326 (86,6%) | 2004-03-10 a 2005-04-04 | Dataset histórico de Itália, sem dados meteorológicos complementares |
| **Lisboa** | 721 (6,7%) | 2025-09-05 a 2025-10-05 | Dados recentes com meteorologia completa |
| **Porto** | 721 (6,7%) | 2025-09-05 a 2025-10-05 | Dados recentes com meteorologia completa |

**Total**: 21,6 anos de amplitude temporal, mas com características heterogéneas.

---

## 1.2 Missing Values por Subset e Impacto nas Regras

### Análise Crítica por Variável

| Variável | Missing Global | Lisboa | Porto | UCI_Dataset | Decisão para Regras |
|----------|----------------|---------|-------|-------------|---------------------|
| **NMHC** | 91,5% | 100% | 100% | 90,2% | ❌ **EXCLUIR** - cobertura insuficiente |
| **PM2.5** | 86,6% | 0% | 0% | 100% | ⚠️ **USAR** apenas Lisboa/Porto |
| **O3** | 86,6% | 0% | 0% | 100% | ⚠️ **USAR** apenas Lisboa/Porto |
| **SO2** | 86,6% | 0% | 0% | 100% | ⚠️ **USAR** apenas Lisboa/Porto |
| **Meteorologia*** | 86,6% | 0% | 0% | 100% | ⚠️ **USAR** apenas Lisboa/Porto |
| **NOx** | 28,3% | 100% | 100% | 17,2% | ⚠️ **USAR** apenas UCI_Dataset |
| **C6H6** | 16,5% | 100% | 100% | 3,6% | ⚠️ **USAR** apenas UCI_Dataset |
| **CO** | 15,3% | 0% | 0% | 17,7% | ✅ **USAR** - boa cobertura UCI |
| **NO2** | 15,0% | 0% | 0% | 17,3% | ✅ **USAR** - boa cobertura global |
| **temperature_c** | 3,1% | 0% | 0% | 3,6% | ✅ **USAR** - excelente cobertura |
| **humidity_percent** | 3,1% | 0% | 0% | 3,6% | ✅ **USAR** - excelente cobertura |

*Meteorologia = wind_speed_kmh, wind_direction_deg, pressure_hpa, precipitation_mm

### Implicações para o Sistema de Regras

1. **Regras de Qualidade do Ar**:
   - PM10, PM2.5, O3, SO2 → **aplicáveis apenas a Lisboa/Porto** (1.442 registos)
   - NO2, CO → **aplicáveis a todo o dataset** (≈9.100 registos)
   - NOx, C6H6 → **aplicáveis apenas a UCI_Dataset** (7.549-9.326 registos)

2. **Regras Meteorológicas**:
   - Temperatura, humidade → **aplicáveis globalmente** (10.433 registos)
   - Vento, precipitação → **aplicáveis apenas a Lisboa/Porto** (1.442 registos)

3. **Regras Combinadas** (ex: temperatura ∧ PM10):
   - Limitadas aos **1.442 registos de Lisboa/Porto**
   - Representam apenas **13,4% do dataset total**

---

## 1.3 Variáveis a Usar e Excluir com Justificação

### ✅ Variáveis INCLUÍDAS no Sistema de Regras

#### Poluentes Atmosféricos

| Variável | Justificação | Fonte Normativa | Cobertura |
|----------|--------------|-----------------|-----------|
| **NO2** | Indicador primário de tráfego automóvel; limite UE 200 μg/m³ (horário) | Diretiva 2008/50/CE | 85% do dataset |
| **PM10** | Partículas inaláveis; limite UE 50 μg/m³ (24h) | Diretiva 2008/50/CE | 13,4% (Lisboa/Porto) |
| **PM2.5** | Partículas finas mais perigosas; limite UE 25 μg/m³ (anual) | Diretiva 2008/50/CE | 13,4% (Lisboa/Porto) |
| **O3** | Ozono troposférico; limite UE 180 μg/m³ (horário) | Diretiva 2008/50/CE | 13,4% (Lisboa/Porto) |
| **CO** | Monóxido de carbono; limite UE 10 mg/m³ (8h) | Diretiva 2008/50/CE | 84,7% (UCI principalmente) |
| **SO2** | Dióxido de enxofre; limite UE 350 μg/m³ (horário) | Diretiva 2008/50/CE | 13,4% (Lisboa/Porto) |

#### Variáveis Meteorológicas

| Variável | Justificação | Aplicação em Regras | Cobertura |
|----------|--------------|---------------------|-----------|
| **temperature_c** | Risco de incêndio, ondas de calor/frio | Limiares IPMA: >40°C (vermelho), <-5°C (frio extremo) | 96,9% |
| **humidity_percent** | Agrava risco de incêndio quando <30%; desconforto >80% | Combinação com temperatura | 96,9% |
| **wind_speed_kmh** | Propagação de incêndios, alerta vento forte >60 km/h | IPMA: amarelo 60-75, laranja 75-90, vermelho >90 | 13,4% |
| **precipitation_mm** | Alerta precipitação intensa >10 mm/h | IPMA: amarelo 10-30, laranja 30-60, vermelho >60 | 13,4% |

### ❌ Variáveis EXCLUÍDAS

| Variável | Razão de Exclusão |
|----------|-------------------|
| **NMHC** | 91,5% missing; hidrocarbonetos não-metânicos não têm limite UE específico |
| **NOx** | Redundante com NO2 (NOx ≈ NO + NO2); missing 28,3% |
| **C6H6** | Benzeno: limite anual (5 μg/m³), não horário - incompatível com alertas em tempo real |
| **pressure_hpa** | Não relevante para alertas ambientais diretos |
| **wind_direction_deg** | Informação secundária; velocidade é suficiente |

### 🔄 Variáveis Derivadas (a calcular)

| Variável | Fórmula | Justificação |
|----------|---------|--------------|
| **heat_index** | HI = f(T, RH) | Índice de calor para ondas de calor (NWS/NOAA) |
| **air_quality_index** | AQI = max(AQI_PM10, AQI_NO2, AQI_O3, ...) | Índice agregado (EEA) |

---

## 1.4 Decisão Final de Preprocessamento para Módulo 1

### Estratégia Adotada

**Princípio**: Maximizar a aplicabilidade das regras sem comprometer a validade científica.

#### 1. Tratamento de Missing Values

```python
# Estratégia por variável
estrategia_missing = {
    # POLUENTES: não imputar - regra não dispara se dado ausente
    'NO2': 'skip_rule',      # Regra não avalia se NO2 is NaN
    'PM10': 'skip_rule',
    'PM2.5': 'skip_rule',
    'O3': 'skip_rule',
    'CO': 'skip_rule',
    'SO2': 'skip_rule',
    
    # METEOROLOGIA: imputação conservadora
    'temperature_c': 'forward_fill',  # Assumir temperatura anterior (válido para 1h)
    'humidity_percent': 'forward_fill',
    'wind_speed_kmh': 'fill_zero',     # Missing → sem vento (conservador)
    'precipitation_mm': 'fill_zero',   # Missing → sem chuva (conservador)
}
```

**Justificação**:
- Poluentes: imputação introduziria falsos positivos/negativos em alertas de saúde
- Meteorologia: forward fill válido para 1h (variação lenta); zeros conservadores

#### 2. Filtragem de Registos

**NÃO aplicar filtragem global** - processar todos os 10.768 registos:
- Cada regra avalia **apenas as variáveis que tem disponíveis**
- Registo sem PM10 → regras de PM10 não disparam (neutral, não erro)
- Maximiza cobertura: regras NO2/CO cobrem 85% do dataset

#### 3. Normalização de Unidades

| Variável | Unidade Original | Conversão Necessária | Unidade Final |
|----------|------------------|----------------------|---------------|
| NO2 | μg/m³ | ✅ Nenhuma | μg/m³ |
| PM10 | μg/m³ | ✅ Nenhuma | μg/m³ |
| PM2.5 | μg/m³ | ✅ Nenhuma | μg/m³ |
| O3 | μg/m³ | ✅ Nenhuma | μg/m³ |
| CO | mg/m³ | ✅ Nenhuma | mg/m³ |
| SO2 | μg/m³ | ✅ Nenhuma | μg/m³ |
| temperature_c | °C | ✅ Nenhuma | °C |

**Verificação**: todas as unidades já estão em conformidade com Diretiva 2008/50/CE.

#### 4. Criação de Variáveis Derivadas

```python
# Heat Index (Steadman, 1979) - simplificado
def calculate_heat_index(T, RH):
    """Índice de calor em °C"""
    if T < 27:
        return T  # Não aplicável
    HI = -8.78469475556 + 1.61139411*T + 2.33854883889*RH \
         - 0.14611605*T*RH - 0.012308094*T**2 \
         - 0.0164248277778*RH**2 + 0.002211732*T**2*RH \
         + 0.00072546*T*RH**2 - 0.000003582*T**2*RH**2
    return HI

# Índice simplificado de risco de incêndio
def fire_risk_index(T, RH, wind):
    """0-100 (Canadian FWI simplificado)"""
    if pd.isna(T) or pd.isna(RH):
        return None
    wind = wind if not pd.isna(wind) else 0
    # Fórmula simplificada
    risk = (T - 10) * (100 - RH) / 100 + wind / 10
    return max(0, min(100, risk))
```

#### 5. Validação de Ranges

```python
# Sanity checks pré-inferência
validations = {
    'NO2': (0, 500),        # μg/m³ - valores fisicamente plausíveis
    'PM10': (0, 600),
    'PM2.5': (0, 300),
    'O3': (0, 500),
    'CO': (0, 50),          # mg/m³
    'SO2': (0, 500),
    'temperature_c': (-20, 50),
    'humidity_percent': (0, 100),
    'wind_speed_kmh': (0, 150),
    'precipitation_mm': (0, 200),
}
```

#### 6. Timestamp e Agregação Temporal

- **Dataset atual**: valores horários (1 registo/hora)
- **Regras**: maioritariamente limiares horários (Diretiva UE)
- **Exceções**: CO (limite 8h) → requer cálculo de média móvel 8h

```python
# Média móvel 8h para CO
df['CO_8h_avg'] = df.groupby('city')['CO'].transform(
    lambda x: x.rolling(window=8, min_periods=6).mean()
)
```

---

## 1.5 Sumário Executivo

### Decisões-Chave

1. ✅ **Processar todo o dataset** (10.768 registos) sem filtragem global
2. ✅ **Regras condicionais**: cada regra só avalia se dados disponíveis
3. ✅ **Não imputar poluentes**: missings → regra não dispara
4. ✅ **Imputação conservadora meteorologia**: forward fill (T, RH), zeros (vento, chuva)
5. ✅ **Criar média móvel 8h para CO**: conformidade com Diretiva 2008/50/CE

### Cobertura Esperada por Tipo de Regra

| Tipo de Regra | Variáveis Necessárias | Registos Aplicáveis | % Dataset |
|---------------|----------------------|---------------------|-----------|
| Qualidade do ar (NO2, CO) | NO2, CO | ≈9.100 | 84,5% |
| Qualidade do ar (PM, O3, SO2) | PM10, PM2.5, O3, SO2 | 1.442 | 13,4% |
| Risco meteorológico | T, RH | 10.433 | 96,9% |
| Risco composto (ar + clima) | T, RH, PM10, vento | 1.442 | 13,4% |

### Limitações Reconhecidas

1. **Heterogeneidade temporal**: 86,6% dos dados de 2004-2005 (UCI), 13,4% de 2025 (PT)
2. **Aplicabilidade geográfica**: limites UE podem não ser ideais para Itália (UCI_Dataset)
3. **Granularidade temporal**: dados horários, mas alguns limites UE são diários/anuais
4. **Missing sistemáticos**: meteorologia ausente em UCI_Dataset limita regras compostas

---

## Próximos Passos

1. Implementar preprocessamento em `rules_engine.py`
2. Definir 10-12 regras considerando cobertura de dados
3. Validar regras com subset de dados conhecido (casos de teste)
4. Documentar assunções e limitações no relatório final
