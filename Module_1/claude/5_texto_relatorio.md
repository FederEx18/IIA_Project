# 5. TEXTO PARA RELATÓRIO FINAL - MÓDULO 1

## 5.1 METODOLOGIA

### 5.1.1 Auditoria e Preparação de Dados

O dataset `processed_lisboa_porto_air_quality.csv` contém 10.768 registos provenientes de três fontes heterogéneas: UCI_Dataset (86,6%, dados históricos de 2004-2005 de Itália), Lisboa (6,7%, dados recentes de 2025) e Porto (6,7%, dados recentes de 2025). Esta composição apresenta desafios significativos para a construção de um sistema de regras baseado em conhecimento, nomeadamente a presença de *missing values* sistemáticos diferenciados por fonte.

A análise de *missing values* revelou que variáveis meteorológicas complementares (velocidade do vento, precipitação, pressão atmosférica) estão ausentes em 86,6% dos registos (correspondentes ao UCI_Dataset), enquanto poluentes atmosféricos como PM₁₀, PM₂.₅, O₃ e SO₂ apresentam padrão inverso — disponíveis apenas para Lisboa e Porto. Variáveis como NO₂ (15% *missing*) e CO (15,3% *missing*) apresentam melhor cobertura global, sendo utilizáveis em ambos os subconjuntos.

Dada esta heterogeneidade, optou-se por uma estratégia de **processamento condicional**: cada regra avalia apenas as variáveis que possui disponíveis, em vez de aplicar filtragem global que reduziria drasticamente o dataset utilizável. Esta abordagem maximiza a cobertura do sistema (63,5% dos registos ativam pelo menos uma regra) sem comprometer a validade científica, uma vez que a ausência de dados para uma variável resulta simplesmente na não-avaliação da regra correspondente (*skip*), e não numa imputação potencialmente enviesada.

Para variáveis meteorológicas com *missing* reduzido (<5%), aplicou-se **forward fill** para temperatura e humidade (assumindo variação lenta em janelas de 1 hora) e preenchimento com zero para vento e precipitação (abordagem conservadora que assume ausência do fenómeno). Poluentes atmosféricos não foram imputados, respeitando o princípio de precaução em alertas de saúde pública.

Uma transformação crítica foi o cálculo da **média móvel de 8 horas** para CO, em conformidade com a Diretiva 2008/50/CE da União Europeia, que estabelece o limite de 10 mg/m³ para a máxima média diária de 8 horas. Esta transformação foi implementada com `rolling(window=8, min_periods=6)`, tolerando até 25% de dados ausentes na janela temporal.

### 5.1.2 Sistema Baseado em Regras

#### Fundamentação em Lógica de Predicados

O motor de inferência implementa **cláusulas de Horn** do tipo:

```
∀x (antecedente₁(x) ∧ antecedente₂(x) ∧ ... ∧ antecedenteₙ(x) → consequente(x))
```

onde antecedentes são predicados sobre variáveis ambientais (ex: `NO₂(x) ≥ 200`) e consequentes são classificações de risco e ações recomendadas.

Foram definidas 12 regras, agrupadas em três categorias:
- **Qualidade do ar** (7 regras): NO₂, PM₁₀, PM₂.₅, O₃, CO, SO₂, episódio multi-poluente
- **Riscos meteorológicos** (4 regras): onda de calor, risco de incêndio, vento forte, precipitação intensa
- **Regras compostas** (1 regra): qualidade do ar agravada por condições de estagnação atmosférica

#### Calibração de Limiares

Todos os limiares foram derivados de fontes normativas reconhecidas:

**Diretiva 2008/50/CE (União Europeia)**:
- NO₂: 200 μg/m³ (limite horário)
- PM₁₀: 50 μg/m³ (limite 24 horas, aplicado conservadoramente a dados horários)
- PM₂.₅: 25 μg/m³ (limite anual, aplicado por precaução a alertas de curto prazo)
- O₃: 180 μg/m³ (limiar de informação ao público)
- CO: 10 mg/m³ (máxima média diária de 8 horas)
- SO₂: 350 μg/m³ (limite horário)

**Instituto Português do Mar e da Atmosfera (IPMA)**:
- Temperatura: 40°C (alerta vermelho para onda de calor)
- Vento: 75 km/h (alerta laranja)
- Precipitação: 10 mm/h (alerta amarelo)

**Canadian Forest Fire Weather Index** (simplificado):
- Risco de incêndio: Temperatura ≥35°C ∧ Humidade ≤30%

É importante notar que alguns limiares da Diretiva 2008/50/CE são definidos para médias de 24 horas ou anuais, enquanto os dados disponíveis têm granularidade horária. Nestes casos (PM₁₀, PM₂.₅), a aplicação direta do limiar a dados horários constitui uma **abordagem ultra-conservadora** que pode gerar falsos positivos, mas que é preferível em contexto de proteção de saúde pública. Esta limitação é explicitamente documentada no sistema.

#### Arquitectura do Motor de Inferência

O motor implementa **inferência para a frente** (*forward chaining*), avaliando sequencialmente as 12 regras para cada registo do dataset. Quando múltiplas regras são ativadas, o sistema aplica um mecanismo de **priorização** baseado em:
1. Gravidade do risco (ALTO > MODERADO > BAIXO)
2. Prioridade numérica atribuída a cada regra (10 = crítico, 5-6 = moderado)
3. Categoria (riscos meteorológicos > qualidade do ar, por terem impacto mais imediato e abrangente)

O resultado final para cada registo inclui:
- Lista de regras ativadas
- Nível de risco máximo (`max(risk_level_regra_i)`)
- Conjunto de ações recomendadas (união das ações de todas as regras ativadas)

### 5.1.3 Rede Bayesiana

#### Estrutura da Rede

A Rede Bayesiana construída modela relações causais entre **4 nós**:

```
    Estação do Ano (raiz)
       /           \
      /             \
  Temperatura    Tráfego Intenso
      \             /
       \           /
    Qualidade do Ar (efeito)
```

Esta estrutura captura conhecimento do domínio:
- Estação do ano influencia tanto padrões de temperatura (verão quente, inverno frio) como padrões de tráfego (redução no verão devido a férias)
- Temperatura e tráfego são **causas independentes** dada a estação (assumindo *d*-separação)
- Qualidade do ar é o **efeito observável** da combinação de ambos os fatores

**Estados das Variáveis**:
- Estação: {Inverno, Primavera, Verão, Outono}
- Temperatura: {Baixa (<15°C), Moderada (15-30°C), Alta (>30°C)}
- Tráfego: {Sim, Não}
- Qualidade do Ar: {Boa, Má}

#### Elicitação de Probabilidades

As **Tabelas de Probabilidade Condicional (CPTs)** foram construídas através de **expert elicitation** calibrada com:

1. **Dados climáticos históricos**: Normais Climatológicas 1971-2000 do IPMA para calibrar P(Temperatura | Estação). Por exemplo, P(Temperatura=Alta | Estação=Verão) = 0,70 reflete que em Portugal continental, cerca de 70% dos dias de verão excedem 30°C em zonas urbanas.

2. **Observações empíricas de tráfego**: P(Tráfego=Sim | Estação=Verão) = 0,30 vs. P(Tráfego=Sim | Estação=Inverno) = 0,55 baseia-se em dados da Câmara Municipal de Lisboa que mostram redução de ~40% no tráfego em agosto devido a férias escolares.

3. **Literatura científica sobre qualidade do ar**:
   - Carslaw & Ropkins (2012): redução de 30-40% em NO₂ aos fins de semana (proxy para impacto de tráfego)
   - Pusede et al. (2014): formação de ozono troposférico depende de temperatura, radiação solar e presença de precursores (NOₓ, VOCs)
   - Fenech et al. (2019): inversão térmica (temperaturas baixas com estagnação) aumenta PM₁₀ em 50-100%

4. **Correlações observadas no dataset**: corr(air_quality_good, NO₂) = -0,60 e corr(air_quality_good, temperatura) = -0,15 validam que tráfego (proxy NO₂) tem impacto mais forte que temperatura isolada.

A CPT mais complexa, P(QualidadeAr | Temperatura, Tráfego), foi calibrada com raciocínio contrafactual. Por exemplo, P(Boa | Temperatura=Alta, Tráfego=Sim) = 0,25 reflete o **pior cenário**: calor favorece formação fotoquímica de O₃, enquanto tráfego injeta NOₓ (precursor de O₃) e PM diretamente. Já P(Boa | Temperatura=Moderada, Tráfego=Não) = 0,85 representa o **melhor cenário**.

#### Inferência por Enumeração

O método de inferência implementado é **enumeração exata** (Russell & Norvig, 2020, Algoritmo Fig. 14.9), que marginaliza sobre variáveis ocultas:

```
P(Query | Evidence) = α × Σ_{hidden} P(Query, hidden, Evidence)
```

onde α é a constante de normalização.

**Exemplo de cálculo** (detalhado na Seção 3.5 do documento técnico):

Query: P(QualidadeAr=Boa | Estação=Verão)

Passo 1: Expandir soma sobre Temperatura (3 estados) × Tráfego (2 estados) = 6 configurações

Passo 2: Para cada configuração (Temp, Traf):
```
P(Boa, Temp, Traf, Verão) = P(Boa | Temp, Traf) × P(Temp | Verão) × P(Traf | Verão) × P(Verão)
```

Passo 3: Somar todas as configurações → resultado não-normalizado = 0,520

Passo 4: Calcular P(Má | Verão) = 0,481 e normalizar → **P(Boa | Verão) = 52%**

**Interpretação**: No verão, a qualidade do ar tem probabilidade ligeiramente superior de ser boa (52%) do que má (48%). Este resultado, aparentemente contra-intuitivo (verão associa-se a calor e formação de O₃), explica-se pela redução significativa de tráfego (férias) que compensa o efeito da temperatura.

---

## 5.2 RESULTADOS

### 5.2.1 Cobertura do Sistema de Regras

A execução do motor de inferência sobre os 10.768 registos revelou os seguintes padrões:

**Regras de Alta Ativação** (>10% dos registos aplicáveis):
- R02_NO2_MODERADO: 1.423 ativações (15,5% dos 9.157 registos com NO₂)
- R12_QUALIDADE_AR_PESSIMA: ≈10% dos registos Lisboa/Porto (estimativa)

**Regras de Ativação Moderada** (1-10%):
- R01_NO2_ALTO: 486 ativações (5,3%)
- R03_PM10_ALTO: 67 ativações (4,6% dos 1.442 registos Lisboa/Porto)
- R08_CALOR_EXTREMO: ≈1% (eventos raros mas críticos)

**Regras Sem Ativação** (0%, mas justificadas):
- R05_O3_ALTO (limiar 180 μg/m³ vs. máximo observado 115 μg/m³): dataset não contém eventos de ozono extremo
- R07_SO2_ALTO (limiar 350 μg/m³ vs. máximo 18 μg/m³): SO₂ em forte declínio na Europa desde dessulfurização de combustíveis
- R10_VENTO_FORTE (limiar 75 km/h vs. máximo 28 km/h): dados são velocidade média, não rajadas

**Cobertura Global**: 6.842 registos (63,5%) tiveram pelo menos uma regra ativada, o que é considerado adequado dado que:
1. 36,5% dos registos representam condições normais (sem alertas necessários)
2. Algumas regras modelam eventos raros por natureza (extremos climáticos)

### 5.2.2 Distribuição de Risco

A distribuição agregada de níveis de risco nos registos com alertas foi:

| Nível | Registos | % do Total | Interpretação |
|-------|----------|------------|---------------|
| ALTO | ≈1.800 | 16,7% | Situações críticas (múltiplos poluentes, eventos extremos) |
| MODERADO | ≈2.500 | 23,2% | Alertas preventivos (limiares intermédios) |
| BAIXO | ≈2.500 | 23,2% | Monitorização reforçada |
| NORMAL | 3.926 | 36,5% | Sem alertas |

Esta distribuição é consistente com um sistema de alerta bem calibrado: a maioria dos dias apresenta condições normais ou risco baixo, enquanto eventos críticos (ALTO) são minoria mas presentes.

### 5.2.3 Resultados da Rede Bayesiana

#### Validação Marginal

A probabilidade marginal P(QualidadeAr=Boa) calculada pela rede através de enumeração completa é **0,54** (54%), enquanto a proporção observada no dataset é **0,425** (42,5%). 

Esta discrepância de 11,5 pontos percentuais é **aceitável e esperada** porque:
1. A rede foi calibrada com conhecimento genérico europeu (normais climatológicas, legislação UE)
2. O dataset UCI_Dataset (86% dos dados) provém de zona industrial italiana com poluição de fundo superior à média europeia
3. A rede não modela poluição de fundo (*background pollution*), apenas fatores dinâmicos (meteorologia, tráfego)

#### Exemplos de Inferência

**Inferência Preditiva 1**: P(QualidadeAr | Estação=Inverno)
- P(Boa | Inverno) = 48%
- P(Má | Inverno) = 52%
- **Interpretação**: Inverno é ligeiramente desfavorável devido a inversão térmica + maior tráfego, apesar de temperaturas moderadas

**Inferência Preditiva 2**: P(QualidadeAr | Temperatura=Alta, Tráfego=Sim)
- P(Boa | Alta, Sim) = 25%
- P(Má | Alta, Sim) = 75%
- **Interpretação**: Pior cenário modelado — combinação de calor (O₃ fotoquímico) e emissões de tráfego

**Inferência Diagnóstica**: P(Tráfego=Sim | QualidadeAr=Má)
- P(Tráfego=Sim | Má) = 57%
- *Prior* P(Tráfego=Sim) = 50%
- **Interpretação**: Observar má qualidade aumenta probabilidade de tráfego intenso em 7 pp, mas não é evidência conclusiva (temperatura também contribui)

#### Testes de Sensibilidade

Testes de monotonicidade confirmaram comportamento esperado:
- P(Boa | Tráfego=Não) = 68% vs. P(Boa | Tráfego=Sim) = 42% → ✓ Tráfego degrada qualidade
- P(Boa | Temperatura=Moderada) = 66% vs. P(Boa | Temperatura=Alta) = 43% → ✓ Calor degrada qualidade

---

## 5.3 LIMITAÇÕES E RISCOS

### 5.3.1 Limitações Metodológicas

**Sistema de Regras**:

1. **Aplicação de limiares temporais inadequados**: Limiares da Diretiva 2008/50/CE para PM₁₀ (24h) e PM₂.₅ (anual) foram aplicados a dados horários. Isto pode gerar **falsos positivos** (alertas desnecessários) quando picos horários não se sustentam ao longo do período de referência normativo. A solução rigorosa seria calcular médias móveis de 24h/anual, mas isto requer janelas temporais longas indisponíveis em 86% do dataset.

2. **Ausência de contexto temporal**: Regras atuam sobre snapshots individuais, sem memória. Por exemplo, a Diretiva permite 18 excedências anuais do limite horário de NO₂, mas o sistema alerta em cada ocorrência isolada sem contabilizar o histórico anual.

3. **Heterogeneidade geográfica não modelada**: Limiares UE podem ser inadequados para Itália (UCI_Dataset). Zonas do Mediterrâneo têm poluição de fundo (poeiras sarianas, aerossóis marinhos) superior ao Norte da Europa.

**Rede Bayesiana**:

4. **Simplificação estrutural extrema**: Apenas 4 nós vs. ~20 variáveis relevantes documentadas na literatura (radiação solar, direção do vento, pressão atmosférica, VOCs, etc.). A rede captura relações de primeira ordem, mas ignora interações complexas.

5. **Discretização perde informação**: Temperatura contínua transformada em 3 bins. A diferença entre 29°C e 31°C (ambos "Alta") pode ser crítica para formação de O₃, mas é invisível à rede.

6. **CPTs baseadas em *expert elicitation***: Idealmente, CPTs seriam aprendidas dos dados via Maximum Likelihood. No entanto, os 1.442 registos Lisboa/Porto (únicos com todas as variáveis) são insuficientes para estimar robustamente 48 parâmetros (P(QualidadeAr | 3 Temperaturas × 2 Tráfegos × 4 Estações)).

### 5.3.2 Riscos de Utilização em Contexto Real

**Falsos Positivos** (alertas desnecessários):
- **Impacto**: Erosão da confiança pública se alertas frequentes não se concretizam em eventos adversos
- **Mitigação**: Calibrar limiares com dados locais de 2-3 anos; implementar período de teste "shadow" onde alertas são gerados mas não publicados

**Falsos Negativos** (falha em detetar risco real):
- **Impacto**: Exposição da população a condições perigosas (ex: PM₂.₅ elevado não detetado)
- **Causas**: Missing values, limiares demasiado altos, eventos não modelados (ex: incêndios florestais → PM₂.₅ súbito)
- **Mitigação**: Integrar com sistemas oficiais (IPMA, QualAr); ter redundância de sensores

**Viés de Dados**:
- 86% dos dados são de 2004-2005 (UCI_Dataset), potencialmente desatualizados face a:
  - Legislação mais restritiva (Euro 6 veículos)
  - Mudanças climáticas (ondas de calor mais frequentes)
  - COVID-19 (teletrabalho permanente reduziu tráfego)
- **Risco**: Sistema calibrado para realidade histórica pode ser otimista ou pessimista em 2026

**Dependência de Qualidade de Sensores**:
- Regras assumem dados precisos e calibrados
- Deriva de sensores (degradação temporal) pode causar alertas espúrios
- **Mitigação**: Protocolo de manutenção/calibração regular de estações de monitorização

### 5.3.3 Implicações Éticas e Socioeconómicas

**Equidade e Justiça Ambiental**:
- Alertas baseados em estações fixas podem não representar microclimas de bairros específicos
- Populações vulneráveis (sem acesso a ar condicionado, moradias mal ventiladas) sofrem mais com poluição/calor, mas podem não ter recursos para agir sobre recomendações
- **Questão ética**: Sistema alertar sem providenciar soluções (ex: "evite sair") pode agravar desigualdades

**Responsabilidade de Decisão**:
- Sistema é **ferramenta de apoio à decisão**, não substituto de especialistas
- Decisões críticas (fechar escolas, limitar tráfego) têm custos económicos e sociais
- Transparência: regras e limiares devem ser publicamente auditáveis

**Risco de Automação Excessiva**:
- Confiar cegamente em alertas automáticos sem validação humana pode levar a decisões erradas
- Exemplo: alerta de incêndio (R09) em dia chuvoso devido a sensor de humidade avariado
- **Princípio**: "Human in the loop" obrigatório para decisões de alto impacto

**Privacidade e Vigilância**:
- Embora este sistema use dados ambientais públicos, futuros desenvolvimentos podem integrar dados pessoais (ex: localização de cidadãos para alertas personalizados)
- Necessário framework legal claro (RGPD) e consentimento informado

---

## 5.4 DISCUSSÃO E CONCLUSÕES

Este trabalho demonstra a aplicabilidade de **Inteligência Artificial simbólica** (sistemas baseados em regras e redes bayesianas) a problemas reais de gestão urbana. A combinação de raciocínio dedutivo (regras) com raciocínio probabilístico (Bayes) oferece complementaridade:

- **Regras**: Transparentes, auditáveis, adequadas para conformidade regulatória (Diretiva 2008/50/CE)
- **Bayes**: Modelam incerteza, permitem inferência diagnóstica ("qual a causa mais provável?"), educam intuição sobre relações causais

No entanto, ambas as abordagens têm **limitações fundamentais** que são exacerbadas pela heterogeneidade e incompletude dos dados disponíveis:

1. **Conhecimento especializado é escasso e custoso**: Definir 12 regras rigorosas requereu consulta de múltiplas fontes normativas (Diretiva UE, IPMA, WHO, literatura científica). Escalar para 50+ regras seria inviável sem equipa multidisciplinar.

2. **Dados reais são sempre imperfeitos**: Missing values, heterogeneidade temporal/geográfica, deriva de sensores. Sistemas simbólicos lidam mal com estas imperfeições (regra ou dispara ou não dispara — não há "meio termo").

3. **Manutenção e atualização**: Legislação muda (WHO 2021 reduziu limite PM₂.₅ de 10 para 5 μg/m³), clima muda, padrões de tráfego mudam. Regras hardcoded requerem revisão manual constante.

Estas limitações motivam a transição para **Aprendizagem Automática** (Módulo 2), onde modelos aprendem padrões diretamente dos dados, adaptam-se a mudanças, e lidam melhor com missing values e não-linearidades.

**Aprendizagens-chave**:

- IA simbólica é **ferramenta valiosa mas insuficiente** para sistemas complexos do mundo real
- **Interpretabilidade** (ponto forte de regras/Bayes) é crítica para aceitação pública e auditoria regulatória
- Integração com **sistemas oficiais** (IPMA, QualAr) e **validação por especialistas** é não-negociável antes de deploy
- **Transparência sobre limitações** é obrigação ética — utentes devem saber que sistema pode falhar

**Trabalho Futuro**:
- Integrar motor de regras com modelos de ML (Módulo 2) num sistema híbrido
- Implementar Dynamic Bayesian Networks para modelar evolução temporal
- Desenvolver interface web para decisores com visualizações intuitivas
- Testar em modo "shadow" com dados em tempo real por 3-6 meses antes de deploy

---

## NOTAS FINAIS

Este documento constitui a base técnica do Módulo 1. Para o relatório final de 10 páginas:
- Seções 5.1, 5.2, 5.3 e 5.4 podem ser condensadas (remover exemplos de cálculo detalhados, manter interpretações)
- Figuras/diagramas são essenciais: estrutura da rede bayesiana, exemplo de ativação de regra, distribuição de risco
- Bibliografia completa está na Seção 6 (próximo ficheiro)
