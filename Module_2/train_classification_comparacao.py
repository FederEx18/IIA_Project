"""
train_classification_comparacao.py
Modulo 2 - Comparacao experimental (iteracao sobre o train_classification.py)

Objectivo: perceber se vale a pena remover o CO e/ou aplicar SMOTE.
Treina os mesmos 3 modelos (LR, RF, KNN) em 4 combinacoes:

    1. baseline:   com CO, sem SMOTE
    2. no_co:      sem CO, sem SMOTE
    3. smote:      com CO, com SMOTE
    4. no_co_smote: sem CO, com SMOTE


Grava:  Module_2/resultados/metrics_comparacao.csv  (4 combos x 3 modelos = 12 linhas)
        Module_2/resultados/roc_comparacao.png       (curvas ROC das 4 combos)


Correr (a partir da raiz do projeto IIA_Project):
   python Module_2/train_classification_comparacao.py
"""

import pandas as pd
import matplotlib
from pathlib import Path
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline as SklearnPipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, roc_curve, auc)

# imblearn (so usado quando use_smote=True; SMOTE aplica-se so no fold de treino da CV, nao contamina o teste)
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE

# ----------------------------------------------------------
# PATHS
# ----------------------------------------------------------
ROOT           = Path(__file__).resolve().parent.parent
CSV_COM_CO     = ROOT / "data" / "classification_data_clean.csv"
CSV_SEM_CO     = ROOT / "data" / "classification_data_clean_no_co.csv"
METRICS_OUT    = ROOT / "Module_2" / "resultados" / "metrics_comparacao.csv"
ROC_OUT        = ROOT / "Module_2" / "resultados" / "roc_comparacao.png"
TARGET         = 'air_quality_good'

# ----------------------------------------------------------
# Reproducibilidade
#----------------------------------------------------------
RANDOM_STATE = 42

# ----------------------------------------------------------
# Combinacoes a testar
# ----------------------------------------------------------
COMBOS = [
    {'nome': 'baseline',    'csv': CSV_COM_CO, 'use_smote': False},
    {'nome': 'no_co',       'csv': CSV_SEM_CO, 'use_smote': False},
    {'nome': 'smote',       'csv': CSV_COM_CO, 'use_smote': True},
    {'nome': 'no_co_smote', 'csv': CSV_SEM_CO, 'use_smote': True},
]


def build_models(use_smote):
    """Devolve a lista (nome, pipeline, grid) para os 3 modelos."""
    PipeCls = ImbPipeline if use_smote else SklearnPipeline # se  use_smote = true, tem de ser pipeline do imblearn (que sabe aplicar o SMOTE só no fold de treino da CV)
    smote   = [('smote', SMOTE(random_state=RANDOM_STATE))] if use_smote else [] # se use_smote = true, adiciona a etapa de oversampling; senao, pipeline normal sem essa etapa
    cw      = None if use_smote else 'balanced' # se use_smote = true, nao precisa de class_weight (pois o SMOTE ja equilibra as classes); senao, usa class_weight='balanced' 
    #para lidar com o desbalanceamento original
    
    # ---------------------------Regresáo Logística-------------------------------------------

    lr_pipe = PipeCls(smote + [
        ('scaler', StandardScaler()),
        ('clf',    LogisticRegression(
            solver='lbfgs', # otimizador para a datasets pequenos/medios
            max_iter=1000, # nº de iteracoes 
            class_weight=cw, # se use_smote=True, cw=None (sem peso); se use_smote=False, cw='balanced' (compensa o desbalanco original)
            random_state=RANDOM_STATE)),
    ])
    lr_grid = {'clf__C': [0.01, 0.1, 1.0, 10.0]}

    # ---------------------------Random Forest-------------------------------------------

    rf_pipe = PipeCls(smote + [
        ('clf', RandomForestClassifier(
            class_weight=cw, # se use_smote=True, cw=None (sem peso); se use_smote=False, cw='balanced' (compensa o desbalanco original)
            n_jobs=-1, 
            random_state=RANDOM_STATE)),
    ])
    rf_grid = {
        'clf__n_estimators':     [100, 300, 500],
        'clf__max_depth':        [None, 10, 20],
        'clf__min_samples_leaf': [1, 5],
    }

    # ---------------------------KNN-------------------------------------------

    knn_pipe = PipeCls(smote + [
        ('scaler', StandardScaler()),
        ('clf',    KNeighborsClassifier(
            metric='minkowski', 
            p=2, n_jobs=-1)),
    ])
    knn_grid = {
        'clf__n_neighbors': [3, 5, 7, 10, 15],
        'clf__weights':     ['uniform', 'distance'],
    }

    return [
        ('LogisticRegression', lr_pipe,  lr_grid),
        ('RandomForest',       rf_pipe,  rf_grid),
        ('KNN',                knn_pipe, knn_grid),
    ]


# ----------------------------------------------------------
# Loop principal: 4 combos x 3 modelos
# ----------------------------------------------------------
resultados = []
rocs_por_combo = {}   # {combo_nome: {modelo_nome: (fpr, tpr, auc)}}

for combo in COMBOS:
    print(f"\n{'#'*60}")
    print(f"#  COMBO: {combo['nome']}   (csv={combo['csv'].split('/')[-1]}, smote={combo['use_smote']})")
    print('#'*60)

    df = pd.read_csv(combo['csv'])
    X = df.drop(columns=[TARGET])
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    rocs_por_combo[combo['nome']] = {}

    for nome, pipe, grid in build_models(combo['use_smote']):
        print(f"  -> {nome} ...", end=' ', flush=True)
        gs = GridSearchCV(pipe, grid, cv=5, scoring='f1_macro', n_jobs=-1, verbose=0)
        gs.fit(X_train, y_train)
        best = gs.best_estimator_
        y_pred = best.predict(X_test)
        y_proba = best.predict_proba(X_test)[:, 1] if hasattr(best, 'predict_proba') else None

        # Metricas (pos_label=False -> classe minoritaria 'ma qualidade')
        acc  = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, pos_label=False, zero_division=0)
        rec  = recall_score(y_test, y_pred, pos_label=False, zero_division=0)
        f1   = f1_score(y_test, y_pred, pos_label=False, zero_division=0)
        if y_proba is not None:
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            roc_auc_val = auc(fpr, tpr)
            rocs_por_combo[combo['nome']][nome] = (fpr, tpr, roc_auc_val)
        else:
            roc_auc_val = None

        resultados.append({
            'combo':     combo['nome'],
            'modelo':    nome,
            'accuracy':  round(acc, 4),
            'precision': round(prec, 4),
            'recall':    round(rec, 4),
            'f1':        round(f1, 4),
            'roc_auc':   round(roc_auc_val, 4) if roc_auc_val is not None else '',
        })
        print(f"F1={f1:.3f}, AUC={roc_auc_val:.3f}" if roc_auc_val else f"F1={f1:.3f}")


# ----------------------------------------------------------
# Tabela final de comparacao
# ----------------------------------------------------------
df_res = pd.DataFrame(resultados)
print(f"\n{'='*60}")
print('  RESULTADOS DAS 4 COMBOS')
print('='*60)
print(df_res.to_string(index=False))

# Vistas pivot: linhas=modelo, colunas=combo. Uma tabela por metrica.
# Mostramos todas para a leitura ser feita no relatorio — nao escolhemos
# vencedor automaticamente.
ORDEM_COMBOS = ['baseline', 'no_co', 'smote', 'no_co_smote']

for metrica in ['recall', 'precision', 'f1', 'roc_auc', 'accuracy']:
    print(f"\n{'='*60}")
    print(f'  {metrica.upper()} (pos_label=False -> classe "ma qualidade")')
    print('='*60)
    pivot = df_res.pivot(index='modelo', columns='combo', values=metrica)
    pivot = pivot[ORDEM_COMBOS]
    print(pivot.to_string())

df_res.to_csv(METRICS_OUT, index=False)
print(f"\nMetricas gravadas em: {METRICS_OUT}")


# ----------------------------------------------------------
# Curvas ROC — 1 painel por combo (grelha 2x2)
# ----------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(13, 11))
for ax, combo in zip(axes.flat, COMBOS):
    for modelo, (fpr, tpr, auc_val) in rocs_por_combo[combo['nome']].items():
        ax.plot(fpr, tpr, lw=2, label=f'{modelo} (AUC={auc_val:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.4)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])
    ax.set_xlabel('FPR'); ax.set_ylabel('TPR')
    ax.set_title(f'combo: {combo["nome"]}')
    ax.legend(loc='lower right', fontsize=9)
    ax.grid(alpha=0.3)
plt.suptitle('Comparação ROC — 4 combinações (com/sem CO × com/sem SMOTE)', fontsize=12)
plt.tight_layout()
plt.savefig(ROC_OUT, dpi=130, bbox_inches='tight')
plt.close()
print(f"Grafico ROC gravado em : {ROC_OUT}")
