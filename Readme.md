# IA para Cidades Sustentáveis — Projeto IIA 2025/2026

Projeto da unidade curricular de **Introdução à Inteligência Artificial** (ISCTE-IUL).
Aplicação de três abordagens complementares de IA — **simbólica**, **aprendizagem
automática** e **generativa** — ao problema da monitorização da qualidade do ar
em **Lisboa** e **Porto**.

## Autores

| Nome | Nº | Email |
|---|---|---|
| Ana-Maria Straistari | 113158 | asian3@iscte-iul.pt |
| David Marques | 113049 | dmsda2@iscte-iul.pt |
| Maura Soares | 123574 | mlass@iscte-iul.pt |
| Tomás Manarte | 122090 | tmcme@iscte-iul.pt |
| Sujan Parajuli | 121073 | spinu@iscte-iul.pt |

---

## Índice

1. [Quick start](#1-quick-start)
2. [Pipeline e ordem de execução](#2-pipeline-e-ordem-de-execução)
3. [Estrutura da entrega](#3-estrutura-da-entrega)
4. [Inputs e outputs por módulo](#4-inputs-e-outputs-por-módulo)
5. [Detalhe dos módulos](#5-detalhe-dos-módulos)
6. [Exemplos de output](#6-exemplos-de-output)
7. [Para o avaliador](#7-para-o-avaliador-correr-tudo-em-2-minutos)
8. [Reprodutibilidade](#8-reprodutibilidade)
9. [Troubleshooting](#9-troubleshooting)
10. [Notas finais](#10-notas-finais)

---

## 1. Quick start

```bash
# 1. Clonar o repositório
git clone <url-do-repo>
cd IIA_Project

# 2. Criar ambiente virtual e ativar
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. (Só para o Módulo 3) token do Hugging Face
# Criar ficheiro Module_3/.env com a linha:
#   HF_TOKEN=hf_xxxxxxxxxxxxx
# O token obtém-se em https://huggingface.co/settings/tokens
# (permissão Fine-Grained com "Make calls to Inference Providers" ativa)
```

Sem o token o notebook do Módulo 3 não consegue chamar o modelo, mas o `Module_3/report_demo.md` já contém um output gerado previamente que serve como exemplo.

---

## 2. Pipeline e ordem de execução

Os módulos têm dependências de dados entre si. **Esta é a ordem correta**:

```
[ data/processed_lisboa_porto_air_quality.csv ]   ← dataset original (versionado)
              │
              ▼
   ┌──────────────────────────────────────────────────┐
   │ PASSO 1 — Module_2/eda.ipynb                     │
   │  produz:                                         │
   │   data/clean_air_quality.csv                     │
   │   data/classification_data_clean.csv             │
   │   data/classification_data_clean_no_co.csv       │
   │   data/regression_data_clean.csv                 │
   └──────────────────────────────────────────────────┘
              │
   ┌──────────┴──────────┐
   ▼                     ▼
┌────────────────────┐  ┌────────────────────────────────────┐
│ PASSO 2a — Módulo 1│  │ PASSO 2b — Módulo 2                │
│ rules_engine.py    │  │ train_classification.py            │
│ bayes_alerts.py    │  │ train_regression.py                │
│ produz:            │  │ produz:                            │
│  resultados_       │  │  Module_2/resultados/metrics.csv   │
│  alertas.csv       │  │  + 5 .pkl (modelos serializados)   │
│  bayes_            │  │  + 2 .png (curvas ROC + resíduos)  │
│  resultados.png    │  │                                    │
└────────────────────┘  └────────────────────────────────────┘
              │                     │
              └──────────┬──────────┘
                         ▼
              ┌──────────────────────────┐
              │ PASSO 3 — Módulo 3       │
              │ gen_report.ipynb         │
              │ produz: report_demo.md   │
              └──────────────────────────┘
```

### Comandos completos (a partir da raiz do projeto)

```bash
# ============================================================
# PASSO 1 — Gerar os datasets limpos (notebook)
# ============================================================
jupyter notebook Module_2/eda.ipynb
# correr todas as células ("Run All"); gera 3 ficheiros em data/

# ============================================================
# PASSO 2a — Módulo 1: motor de regras + Rede Bayesiana
# ============================================================
python Module_1/rules_engine.py        # → Module_1/resultados_alertas.csv
python Module_1/bayes_alerts.py        # → Module_1/bayes_resultados.png
                                       # + accuracy + classification report no terminal

# ============================================================
# PASSO 2b — Módulo 2: treino dos modelos ML
# ============================================================
python Module_2/train_classification.py
python Module_2/train_regression.py
# ambos escrevem em Module_2/resultados/

# (Opcional) iteração experimental: testa o efeito de remover CO e/ou aplicar
# SMOTE em 4 combinações. Não toca em metrics.csv — grava em metrics_comparacao.csv.
python Module_2/train_classification_comparacao.py

# ============================================================
# PASSO 3 — Módulo 3: relatório gerado por LLM
# ============================================================
# Antes de correr, criar Module_3/.env com:  HF_TOKEN=hf_xxxxxxxx
jupyter notebook Module_3/gen_report.ipynb
# Run All — a célula final escreve Module_3/report_demo.md
```

> **Importante:** o PASSO 1 é obrigatório antes do PASSO 2 — sem `data/clean_air_quality.csv` os módulos 1 e 2 falham. O PASSO 3 lê os outputs dos módulos 1 e 2, pelo que tem de vir depois.

---

## 3. Estrutura da entrega

```
IIA_Project/
├── data/
│   ├── processed_lisboa_porto_air_quality.csv
│   ├── clean_air_quality.csv
│   ├── classification_data_clean.csv
│   ├── classification_data_clean_no_co.csv
│   └── regression_data_clean.csv
│
├── Module_1/
│   ├── rules_engine.py
│   ├── bayes_alerts.py
│   ├── regras.json
│   ├── regras.txt
│   ├── dev.ipynb
│   ├── resultados_alertas.csv
│   └── bayes_resultados.png
│
├── Module_2/
│   ├── eda.ipynb
│   ├── train_classification.py
│   ├── train_classification_comparacao.py
│   ├── train_regression.py
│   └── resultados/
│       ├── metrics.csv
│       ├── metrics_comparacao.csv
│       ├── roc_curves_classification.png
│       ├── roc_comparacao.png
│       └── residuals_regression.png
│
├── Module_3/
│   ├── gen_report.ipynb
│   ├── report_utils.py
│   ├── prompts.md
│   └── report_demo.md
│
├── Relatorio_Final_IA.docx
├── requirements.txt
└── Readme.md
```

---

## 4. Inputs e outputs por módulo

| Módulo / Script | Lê (input) | Escreve (output) |
|---|---|---|
| **EDA** — `Module_2/eda.ipynb` | `data/processed_lisboa_porto_air_quality.csv` | `data/clean_air_quality.csv`<br>`data/classification_data_clean.csv`<br>`data/classification_data_clean_no_co.csv`<br>`data/regression_data_clean.csv` |
| **M1 Regras** — `Module_1/rules_engine.py` | `data/clean_air_quality.csv`<br>`Module_1/regras.json` | `Module_1/resultados_alertas.csv` |
| **M1 Bayes** — `Module_1/bayes_alerts.py` | `data/clean_air_quality.csv` | `Module_1/bayes_resultados.png`<br>+ accuracy/classification report (stdout) |
| **M2 Classif.** — `Module_2/train_classification.py` | `data/classification_data_clean.csv` | `Module_2/resultados/metrics.csv`<br>`Module_2/resultados/roc_curves_classification.png`<br>`Module_2/resultados/{logisticregression,randomforest,knn}_classification.pkl` |
| **M2 Comparação** — `Module_2/train_classification_comparacao.py` | `data/classification_data_clean.csv`<br>`data/classification_data_clean_no_co.csv` | `Module_2/resultados/metrics_comparacao.csv`<br>`Module_2/resultados/roc_comparacao.png` |
| **M2 Regress.** — `Module_2/train_regression.py` | `data/regression_data_clean.csv` | `Module_2/resultados/metrics.csv` (atualiza)<br>`Module_2/resultados/residuals_regression.png`<br>`Module_2/resultados/{linearregression,randomforest}_regression.pkl` |
| **M3 Geração** — `Module_3/gen_report.ipynb` | `Module_1/resultados_alertas.csv`<br>`Module_1/regras.json`<br>`Module_2/resultados/metrics.csv`<br>`Module_3/.env` (HF_TOKEN) | `Module_3/report_demo.md` |

---

## 5. Detalhe dos módulos

### 5.1 Módulo 1 — IA Simbólica

Combina dois sub-sistemas que partilham a mesma fonte de dados.

**Motor de regras** (`rules_engine.py`):
- 12 regras codificadas em `regras.json`, com limites baseados na *Diretiva 2008/50/CE*, OMS 2021 e IPMA.
- Cada regra define: condição (`simple_threshold`, `range`, `compound_and`, `compound_or`), prioridade (1–10), nível de risco, ação recomendada e fonte regulamentar.
- Para cada observação, gera todos os alertas aplicáveis e seleciona o de maior prioridade.

Estrutura de uma regra em `regras.json`:

```json
{
  "id": "R04_PM25_ALTO",
  "description": "Particulas finas PM2.5 excedem limite anual UE",
  "priority": 10,
  "condition": {
    "type": "simple_threshold",
    "variable": "PM2.5",
    "operator": ">=",
    "threshold": 25,
    "unit": "ug/m3"
  },
  "consequence": {
    "risk_level": "ALTO",
    "category": "air_quality",
    "action": "Grupos sensiveis permanecam em ambientes internos. Usar mascara FFP2.",
    "source": "Diretiva 2008/50/CE; WHO 2021"
  }
}
```

**Rede Bayesiana** (`bayes_alerts.py`):
- DAG com 4 nós: `estacao → temperatura`, `estacao → pm25`, `(temperatura, pm25) → qualidade_ar`.
- CPDs estimadas por máxima verosimilhança com suavização de Laplace (α = 1).
- Inferência por enumeração, marginalizando variáveis ocultas.
- A *target* (`NO₂` + humidade) é deliberadamente mantida fora dos *inputs*, para evitar que a rede apenas reproduza as regras.

### 5.2 Módulo 2 — Aprendizagem Automática

Pipeline em três passos:

1. **EDA** (`eda.ipynb`)
   - Análise exploratória, limpeza, redefinição da target `air_quality_good` (= `False` se `NO₂ ≥ 30 µg/m³` **e** `humidade ≥ 80 %`).
   - Geração dos datasets para treino: `classification_data_clean.csv` (com CO), `classification_data_clean_no_co.csv` (sem CO, para a iteração comparativa) e `regression_data_clean.csv`.

2. **Classificação** (`train_classification.py`) — target: `air_quality_good`
   - Algoritmos: **Logistic Regression** (linear, `StandardScaler`, `class_weight='balanced'`), **Random Forest** (não-linear, *ensemble*, `class_weight='balanced'`), **KNN** (distância, `StandardScaler` + **SMOTE**).
   - `GridSearchCV` (cv=5, scoring=`f1_macro`) e `stratify=y` no split para o desbalanço ~90/10.
   - **Nota sobre o KNN**: o `KNeighborsClassifier` não suporta `class_weight`. Para compensar o desbalanço aplicou-se **SMOTE** (Chawla et al., 2002) como primeiro step do Pipeline via `imblearn` — o oversampling só ocorre no fold de treino da CV, evitando data leakage para a validação/teste.
   - Métricas registadas: accuracy, precision, recall, F1, ROC-AUC.

3. **Comparação experimental** (`train_classification_comparacao.py`) — *opcional, iteração metodológica*
   - Treina os 3 modelos em 4 combinações (com/sem CO × com/sem SMOTE) para isolar o efeito de cada mudança.
   - Não toca em `metrics.csv`; grava em `metrics_comparacao.csv` e `roc_comparacao.png`.
   - Confirmou que o CO é redundante (variação ≤ 0.02 em todas as métricas) e que o SMOTE só beneficia o KNN — daí a configuração final em `train_classification.py`.

4. **Regressão** (`train_regression.py`) — target: `NO2`
   - Algoritmos: **Linear Regression**, **Random Forest Regressor** (com `GridSearchCV`).
   - Métricas registadas: R², MSE, MAE.

### 5.3 Módulo 3 — IA Generativa

Pipeline de *grounded generation*: o LLM recebe **apenas factos numéricos pré-calculados** pelos Módulos 1 e 2, nunca o dataset bruto. Isto restringe o modelo à formatação textual e à adaptação de linguagem, mitigando o risco de alucinação.

O pipeline está implementado no notebook `gen_report.ipynb`, que importa helpers de `report_utils.py` (estrutura `ReportFacts`, função `load_facts`, templates de prompt e função `generate_hf`). As três variantes de prompt são chamadas dentro do notebook:

```python
saida_baseline    = generate_hf(facts, "baseline",      call_hf)
saida_estruturado = generate_hf(facts, "estruturado",   call_hf)
saida_critico     = generate_hf(facts, "critico_etico", call_hf)
```

| Variante | Audiência | Características |
|---|---|---|
| `baseline` | Genérica | Prompt minimalista, sem regras estruturais |
| `estruturado` | Técnica (Proteção Civil, analistas) | Cabeçalhos Markdown obrigatórios, fontes regulamentares, métricas |
| `critico_etico` | Decisores políticos + cidadão | Linguagem acessível, grupos de risco específicos, reflexão ética |

Análise comparativa completa em `Module_3/prompts.md`.

**Modelo:** `Qwen/Qwen2.5-72B-Instruct` via Hugging Face Inference API (configurável no setup do notebook, célula 2).
**Temperatura:** 0.2 por defeito em `generate_hf` (baixa, para texto institucional reprodutível).
**Autenticação:** o notebook lê `HF_TOKEN` de `Module_3/.env` (ficheiro não versionado — ver §1 Quick start).

---

## 6. Exemplos de output

### Módulo 1 — `resultados_alertas.csv`

```
cidade;datetime;n_alertas;risco;regras;acao
Lisboa;05/09/25 01:00;0;NORMAL;;Sem ação necessária.
Lisboa;05/09/25 07:00;1;ALTO;R04_PM25_ALTO;Grupos sensiveis permanecam em ambientes internos.
Porto;15/10/25 18:00;2;ALTO;R01_NO2_ALTO, R03_PM10_ALTO;Limitar trafego automovel.
```

### Módulo 2 — `metrics.csv`

```
modelo,tarefa,accuracy,precision,recall,f1,roc_auc,r2,mse,mae
LogisticRegression,classificacao,0.8304,0.3438,0.7586,0.4731,0.8533,,,
RandomForest,classificacao,0.917,0.5641,0.7586,0.6471,0.9366,,,
KNN,classificacao,0.8893,0.4717,0.8621,0.6098,0.934,,,
LinearRegression,regressao,,,,,,0.7182,44.8023,5.1014
RandomForest,regressao,,,,,,0.7231,44.0225,5.0737
```

> Nota: a linha do KNN reflecte o modelo treinado com SMOTE (versão final). O recall sobe de 0.45 (sem SMOTE) para 0.86, à custa de precision (0.68 → 0.47). O F1 melhora (0.54 → 0.61).

### Módulo 3 — `report.md` (excerto)

```markdown
## Resumo executivo
Entre setembro e outubro de 2025 foram analisadas 1.442 observações horárias
da qualidade do ar em Lisboa e Porto. Em cerca de 14 % dos casos o sistema
identificou condições acima do limite considerado seguro, sobretudo por
excesso de partículas finas (PM2.5)...

## Recomendações
1. **Quando PM10 ≥ 50 µg/m³**, restringir circulação automóvel em vias
   centrais e emitir aviso a asmáticos, crianças e idosos (Diretiva 2008/50/CE)...
```

---

## 7. Para o avaliador (correr tudo em 2 minutos)

Um único bloco de comandos para reproduzir a entrega completa, partindo de um clone limpo:

```bash
git clone <url-do-repo>
cd IIA_Project
python -m venv .venv && source .venv/bin/activate    # ou .venv\Scripts\Activate.ps1 no Windows
pip install -r requirements.txt

# 1. Gerar datasets limpos (executa o notebook sem abrir UI)
jupyter nbconvert --to notebook --execute Module_2/eda.ipynb --output eda_executed.ipynb

# 2. Módulo 1
python Module_1/rules_engine.py
python Module_1/bayes_alerts.py

# 3. Módulo 2
python Module_2/train_classification.py
python Module_2/train_regression.py

# 4. Módulo 3 (requer Module_3/.env com HF_TOKEN)
jupyter nbconvert --to notebook --execute Module_3/gen_report.ipynb --output gen_report_executed.ipynb
# alternativa: abrir o notebook no Jupyter e "Run All"
```

Após a execução, os principais artefactos estão em:

- `Module_1/resultados_alertas.csv` — alertas por observação
- `Module_1/bayes_resultados.png` — avaliação da Rede Bayesiana
- `Module_2/resultados/metrics.csv` — métricas dos 5 modelos
- `Module_2/resultados/roc_curves_classification.png` — Figura 2 do relatório
- `Module_2/resultados/residuals_regression.png` — Figura 3 do relatório
- `Module_3/report_demo.md` — relatório natural-language gerado pelo LLM (variante crítico-ético)
- `Relatorio_Final_IA.docx` — relatório final escrito (entrega académica)

---

## 8. Reprodutibilidade

- Todos os scripts usam `random_state=42` onde aplicável.
- O `train_classification.py` faz `stratify=y` no split, garantindo que a proporção da classe minoritária se mantém em treino e teste.
- O `metrics.csv` é incrementalmente atualizado: `train_classification.py` preserva as linhas de regressão e vice-versa.

**Versões testadas:**

| Pacote | Versão mínima |
|---|---|
| Python | 3.11 |
| pandas | 2.0 |
| numpy | 1.24 |
| scikit-learn | 1.4 |
| imbalanced-learn | 0.12 (SMOTE no KNN) |
| matplotlib | 3.7 |
| seaborn | 0.12 |
| huggingface_hub | 0.24 (só Módulo 3) |
| python-dotenv | 1.0 (só Módulo 3) |

---

## 9. Troubleshooting

| Problema | Causa provável | Solução |
|---|---|---|
| `FileNotFoundError: data/clean_air_quality.csv` | Não correste o PASSO 1 (eda.ipynb) | Executa o notebook do Módulo 2 antes dos restantes scripts |
| `FileNotFoundError: Module_2/resultados/metrics.csv` ao correr Módulo 3 | Não correste o PASSO 2b | Corre `train_classification.py` e `train_regression.py` |
| `KeyError: 'HF_TOKEN'` ou erro 401/403 ao correr Módulo 3 | Token Hugging Face em falta ou sem permissões | Cria `Module_3/.env` com `HF_TOKEN=hf_xxx` (token com permissão "Make calls to Inference Providers" ativa — ver §1) |
| Caracteres estranhos no `resultados_alertas.csv` | Codificação | O ficheiro é UTF-8; abre com encoding correto (Excel: "Importar do texto", encoding `65001`) |
| Notebook `eda.ipynb` falha em ler o CSV | Working directory errado | Abre o Jupyter a partir da **raiz do projeto** (`IIA_Project/`), não de `Module_2/` |
| Demora muito no `GridSearchCV` | Grid grande (Random Forest) | Reduz `n_estimators` em `train_classification.py` para acelerar |
| `ModuleNotFoundError: No module named 'imblearn'` | Falta o `imbalanced-learn` | `pip install imbalanced-learn` ou re-correr `pip install -r requirements.txt` |
| `FileNotFoundError: data/classification_data_clean_no_co.csv` ao correr `train_classification_comparacao.py` | EDA antiga, sem a célula da variante sem CO | Re-correr `Module_2/eda.ipynb` (Run All) |

---

## 10. Notas finais

- Os ficheiros em `Module_2/resultados/` são **gerados localmente** ao correr `train_classification.py` e `train_regression.py`. As 5 métricas reportadas no `Relatorio_Final_IA.docx` são reprodutíveis com `random_state=42`.
- O ficheiro `data/processed_lisboa_porto_air_quality.csv` consolida três fontes: Lisboa (721 obs), Porto (721 obs) e a partição `UCI_Dataset` (9.326 obs, cidade italiana, 2004–2005). O `eda.ipynb` descarta esta última e mantém apenas Lisboa + Porto (1.442 obs) — justificação detalhada no relatório.
- O relatório final escrito está em `Relatorio_Final_IA.docx`.
