# Módulo 3 — Engenharia de Prompts

Este documento descreve as **três variantes de prompt** testadas em
`gen_report.ipynb`, os outputs respetivos sobre o mesmo conjunto de factos
(`Module_1/resultados_alertas.csv` + `Module_1/regras.json` +
`Module_2/resultados/metrics.csv`), e uma análise comparativa.

Todas as variantes recebem o **mesmo bloco de factos numéricos** (ver
`ReportFacts` em `gen_report.ipynb`). Diferem apenas nas instruções dadas
ao modelo. O objetivo é avaliar como variações na engenharia do prompt
afetam estrutura, clareza, fidelidade aos dados e adequação ao público.

Modelo usado: `Qwen/Qwen2.5-72B-Instruct` via Hugging Face Inference API. Temperatura 0.2 (baixa, para texto institucional reprodutível), max_tokens 1500.

---

## Variante 1 — Baseline

**Prompt:**

> És um assistente que escreve relatórios curtos.
> A partir destes dados sobre qualidade do ar, escreve:
> - Um resumo executivo (≤ 200 palavras)
> - 2 a 3 recomendações de ação
> - Uma secção sobre limitações e riscos
>
> Dados: `{facts}`

**Output (excerto):**

```
Foi feita uma análise da qualidade do ar em Lisboa e Porto entre setembro
e outubro de 2025, totalizando 1.442 observações. A maioria das medições
correspondeu a níveis NORMAL (1.243), com 199 alertas de nível ALTO. As
principais regras disparadas foram excedências de PM2.5 (R04, 111 vezes)
e episódios de qualidade do ar péssima (R12, 80 vezes). Os modelos de
aprendizagem automática atingiram F1 de 0,647 (Random Forest) e R² de
0,723 na previsão de NO₂.

Recomendações:
1. Reduzir tráfego em períodos de PM2.5 elevado.
2. Reforçar comunicação à população em zonas com >15 % de alertas.
3. Adoptar modelos com melhor recall.

Limitações: dados limitados, classes desbalanceadas, sem cobertura sazonal
completa.
```

**Notas:**
- Texto correto mas seco; não cita fontes regulamentares.
- Recomendações genéricas (ex: "Reduzir tráfego" sem indicar gatilho ou
  grupo de risco).
- Limitações ficam ao nível de bullet points sem contexto.

---

## Variante 2 — Estruturado

**Prompt:**

> És um analista técnico a redigir um relatório para a Proteção Civil.
> Usa exclusivamente os factos abaixo; não inventes números nem cidades.
> O relatório tem três secções com cabeçalho em Markdown
> ('## Resumo executivo', '## Recomendações', '## Limitações e riscos').
>
> Regras:
> 1. Resumo executivo: máximo 200 palavras, prosa contínua, sem listas.
> 2. Recomendações: 2 a 3 ações concretas, cada uma indicando o gatilho
>    quantitativo (ex: 'PM10 > 50 µg/m³') e a fonte regulamentar.
> 3. Limitações e riscos: enumerar pelo menos três limitações dos dados
>    ou modelos, citando as métricas (recall, F1, R²) quando relevante.
> 4. Se não tiveres informação para uma alegação, escreve 'dados
>    insuficientes'.
>
> Factos: `{facts}`

**Output (excerto):**

```
## Resumo executivo
Análise de 1.442 observações horárias recolhidas em Lisboa e Porto entre
setembro e outubro de 2025. O motor de regras (12 regras baseadas na
Diretiva 2008/50/CE e nas guidelines da OMS 2021) identificou 199
situações com risco superior ao nível normal (~14 %), distribuídas de
forma desigual: Lisboa concentra 17,3 % das observações com alerta, contra
10,2 % no Porto. As regras mais ativadas correspondem a excedências de
PM2.5 (R04, 111 ocorrências) e a episódios de qualidade do ar péssima
(R12, 80 ocorrências). Os modelos do Módulo 2 atingiram, em classificação
binária da qualidade do ar, F1 = 0,647 e ROC-AUC = 0,937 (Random Forest);
em regressão de NO₂, R² = 0,723 e MAE = 5,07 µg/m³. As métricas
privilegiam a deteção da classe minoritária ('má'), com recall ≥ 0,76 nos
modelos selecionados, em coerência com o risco assimétrico de falsos
negativos em saúde pública.

## Recomendações
1. **Limitar tráfego automóvel quando PM10 ≥ 50 µg/m³** (Diretiva
   2008/50/CE, limite 24h aplicado conservadoramente a dados horários).
   Grupos sensíveis devem evitar exercício ao ar livre.
2. **Ativar plano de calor para temperatura ≥ 35 °C com humidade < 30 %**
   (IPMA, DGS Plano Contingência Temperaturas Extremas), com alerta
   antecipado a serviços de saúde e proibição de queimadas.
3. **Reforçar comunicação em Lisboa**, onde a frequência de alertas
   (17,3 %) supera a do Porto em mais de 7 p.p.

## Limitações e riscos
- Cobertura sazonal limitada (set-out 2025); inverno e verão não estão
  representados, pelo que os modelos extrapolarão fora deste regime.
- Desbalanço de classes (~10 % de registos 'má'): a accuracy de 0,924 do
  KNN é enganadora porque o seu recall na classe 'má' é apenas 0,448.
- O R² de 0,723 dos modelos de regressão indica que ~28 % da variância
  do NO₂ não é explicada pelas variáveis disponíveis — variáveis-chave
  como volume de tráfego não estão incluídas.
```

**Notas:**
- Estrutura clara, métricas citadas no sítio certo.
- Recomendações concretas com gatilho quantitativo e fonte regulamentar.
- Boa para audiência técnica (Proteção Civil, analistas).
- Linguagem ainda assume conhecimento técnico (e.g. "ROC-AUC", "p.p.").

---

## Variante 3 — Crítico-Ético

**Prompt:**

> És um analista de políticas públicas a redigir um relatório destinado
> simultaneamente a decisores municipais e a comunicação ao cidadão. O
> texto deve ser claro, sem jargão técnico excessivo, e ético: identifica
> explicitamente assimetrias de informação, risco de viés e incerteza dos
> modelos.
>
> Estrutura obrigatória (cabeçalhos em Markdown):
> ## Resumo executivo (≤ 200 palavras)
> ## Recomendações (2 a 3 ações)
> ## Limitações, riscos e considerações éticas
>
> Regras:
> 1. Usa apenas os factos fornecidos. Se algo não estiver nos factos, diz
>    'não disponível nos dados deste relatório'.
> 2. Cada recomendação deve nomear (i) o gatilho quantitativo, (ii) a
>    fonte regulamentar (Diretiva 2008/50/CE, OMS 2021, IPMA), (iii) o
>    grupo de risco específico (asmáticos, idosos, crianças, trabalhadores
>    ao ar livre).
> 3. Na secção crítica, discute pelo menos: o desbalanço de classes (~10 %
>    de registos 'má'), a cobertura geográfica e sazonal limitada, e o
>    risco de falsos negativos em saúde pública.
> 4. Não atribuas intenção, opinião ou previsão fora do que os dados
>    suportam. Trata os modelos como ferramentas de apoio, nunca como
>    decisores autónomos.
>
> Factos: `{facts}`

**Output (excerto):**

```
## Resumo executivo
Entre setembro e outubro de 2025, foram analisadas 1.442 observações
horárias da qualidade do ar em Lisboa e Porto. Em cerca de 14 % dos
casos, o sistema identificou condições acima do limite considerado
seguro, sobretudo por excesso de partículas finas (PM2.5) e episódios
combinados de elevada poluição com humidade alta. Lisboa apresentou mais
alertas (17,3 %) do que o Porto (10,2 %), o que pode refletir tráfego
mais denso ou diferenças nas estações de medição. Os modelos preditivos
testados atingiram desempenho moderado-alto (acerto global elevado mas
com falhas notáveis na deteção de eventos raros), pelo que devem ser
usados como apoio à decisão e nunca como substitutos do julgamento
humano. Recomenda-se que cada alerta gerado pelo sistema seja validado
por uma equipa técnica antes de qualquer comunicação ao público.

## Recomendações
1. **Quando PM10 ≥ 50 µg/m³**, restringir circulação automóvel em vias
   centrais e emitir aviso a **asmáticos, crianças e idosos** para
   evitarem exercício ao ar livre (Diretiva 2008/50/CE, anexo XI).
2. **Em situação de calor extremo (≥ 35 °C com humidade < 30 %)**,
   ativar o plano de contingência da DGS para **trabalhadores ao ar
   livre, idosos isolados e crianças em creches** (IPMA / DGS Plano
   Calor).
3. **Reforçar comunicação em Lisboa**, onde os alertas são 70 % mais
   frequentes do que no Porto. Esta comunicação deve ser feita em
   linguagem simples e em múltiplos canais para chegar a populações com
   menor literacia digital.

## Limitações, riscos e considerações éticas
- **Desbalanço de classes:** apenas ~10 % das observações são 'má'
  qualidade do ar. Modelos podem parecer 'corretos' (accuracy alta) e
  ainda assim falhar metade dos alertas. A nossa preferência foi por
  modelos com maior recall na classe 'má', porque falhar um alerta tem
  custo de saúde pública superior a emitir um falso alerta.
- **Cobertura limitada:** dois meses, duas cidades, ambas costeiras.
  Aplicar este sistema a cidades de interior, no inverno ou no verão,
  exige revalidação. Não disponível nos dados deste relatório a
  performance fora deste regime.
- **Risco de viés social:** alertas têm impacto desigual — quem tem mais
  recursos pode ficar em casa, comprar purificadores, evitar transporte
  público. O sistema não compensa estas desigualdades; a câmara
  municipal deverá articular a comunicação com políticas de saúde
  pública para grupos vulneráveis.
- **Responsabilidade humana:** este sistema é apoio à decisão. Nenhum
  alerta deve ser comunicado ao público sem revisão por equipa técnica
  da Proteção Civil ou autoridade de saúde.
```

**Notas:**
- Linguagem acessível mas tecnicamente correta.
- Cada recomendação inclui gatilho, fonte e grupo de risco específico.
- A secção crítica adiciona uma dimensão ética (viés social, incerteza,
  responsabilidade humana) que está ausente nas variantes anteriores.
- Adequada para comunicação a decisores políticos e ao público.

---

## Análise comparativa

| Critério | Baseline | Estruturado | Crítico-ético |
|---|---|---|---|
| Cumpre estrutura pedida (resumo+rec+limitações) | Parcial (sem cabeçalhos) | Sim | Sim |
| Cita fontes regulamentares | Não | Sim | Sim |
| Identifica grupo de risco específico | Não | Não | Sim |
| Adequado a público não-técnico | Médio | Baixo | Alto |
| Reflexão ética explícita | Não | Limitada | Sim |
| Risco de hallucination | Médio | Baixo | Baixo |
| Densidade de informação útil | Baixa | Alta | Alta |
| Adequação a decisor político | Baixa | Média | Alta |

**Observações:**

- Os três outputs são **factualmente equivalentes**: usam os mesmos
  números (1.442 observações, F1 = 0,647, R² = 0,723, etc.). A diferença
  está na estrutura, na linguagem e na profundidade da discussão crítica.
- A variante **baseline** mostra o efeito de não dar instruções
  suficientes: o modelo produz texto razoável mas genérico, sem cumprir
  formalmente a estrutura pedida (não usa cabeçalhos Markdown).
- A variante **estruturada** é a mais útil para audiências técnicas: é
  densa, precisa e cita métricas. Mas o jargão (ROC-AUC, p.p., recall)
  pode excluir leitores não-técnicos.
- A variante **crítico-ético** é a recomendada para a maioria dos
  contextos da Proteção Civil porque: (i) inclui sempre o grupo de risco
  no qual a recomendação se aplica, (ii) explicita a incerteza dos
  modelos, (iii) reflete sobre o impacto desigual dos alertas. Foi
  escolhida como variante predefinida em `gen_report.py`.

## Risco de alucinação e mitigações

Em todas as variantes, o LLM recebe **apenas os factos numéricos
pré-calculados pelos Módulos 1 e 2**, nunca o dataset bruto. Esta
arquitetura ("grounded generation") restringe o modelo à formatação
textual e à adaptação de linguagem; toda decisão factual continua a vir
dos módulos anteriores.

Mesmo assim, observámos os seguintes padrões de risco que merecem
atenção:

1. **Sobre-interpretação qualitativa.** O modelo, quando lhe é dada uma
   métrica como R² = 0,72, tende a classificá-la como "aceitável" ou
   "robusta". Esta categorização é um juízo de valor implícito do prompt
   ("desempenho moderado-alto" no exemplo). Recomenda-se que avaliações
   qualitativas sejam revistas por humanos.
2. **Inferência sobre causa.** Na variante crítico-ética, o output sugere
   que a maior frequência de alertas em Lisboa "pode refletir tráfego
   mais denso ou diferenças nas estações de medição" — esta hipótese é
   plausível mas não está nos dados. Está corretamente assinalada com
   "pode", mas é uma forma branda de extrapolação.
3. **Generalização para grupos.** Quando o prompt pede "grupo de risco",
   o modelo lista grupos plausíveis (asmáticos, idosos, crianças). Estes
   são os grupos canónicos da literatura de saúde pública, mas o
   relatório não tem dados específicos sobre nenhum deles. A
   recomendação deve ser lida como aplicação de conhecimento clínico
   geral, não como inferência sobre a população observada.

A revisão humana de cada output gerado é, portanto, parte intrínseca do
processo — o sistema é apoio à redação, não substituto.
