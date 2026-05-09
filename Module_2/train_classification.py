"""
train_classification.py
Modulo 2 - Treino dos modelos de classificacao para prever air_quality_good

Modelos:
  - Logistic Regression  (linear, com StandardScaler)
  - Random Forest        (nao-linear, ensemble)
  - KNN                  (baseado em distancia, com StandardScaler)

Le:    data/classification_data_clean.csv  (gerado pelo eda.ipynb)
Grava: 3 modelos .pkl + metrics.csv + roc_curves_classification.png

Correr (a partir da raiz do projeto IIA_Project):
   python Module_2/train_classification.py
"""

import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')  # nao abre janela; so grava ficheiro
import matplotlib.pyplot as plt


from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix,roc_curve, auc)

# ----------------------------------------------------------
# PATHS
# ----------------------------------------------------------
DATA_CSV    = r'data/classification_data_clean.csv'
METRICS_CSV = r'Module_2/metrics.csv'
ROC_PNG     = r'Module_2/roc_curves_classification.png'
LR_PKL      = r'Module_2/logisticregression_classification.pkl'
RF_PKL      = r'Module_2/randomforest_classification.pkl'
KNN_PKL     = r'Module_2/knn_classification.pkl'

TARGET = 'air_quality_good'

# ----------------------------------------------------------
# 1. Carregar dados
# ----------------------------------------------------------
df = pd.read_csv(DATA_CSV)
print(f"Dataset: {df.shape[0]} linhas x {df.shape[1]} colunas")
print(f"Distribuicao da target ({TARGET}):")
print(df[TARGET].value_counts())

X = df.drop(columns=[TARGET])
y = df[TARGET]

# ----------------------------------------------------------
# 2. Split treino/teste
# ----------------------------------------------------------
# test_size=0.2     -> 80% treino, 20% teste
# random_state=42   -> reprodutibilidade
# stratify=y        -> mantem ratio boa/ma (essencial com desbalanco 90/10) ! É Obrigattório aqui as classes estao desbalanceadas!!!!
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTreino: {len(X_train)} obs | Teste: {len(X_test)} obs")

# ----------------------------------------------------------
# 3. Definir os modelos + grids para GridSearchCV
# ----------------------------------------------------------
# ------Logistic Regression ----------
#
# Hyperparameters base:
#   C                 -> inverso da regularizacao L2. Menor = mais reg.
#   penalty='l2'      -> regularizacao L2 (Ridge): penaliza coef^2
#   solver='lbfgs'    -> optimizador adequado a datasets pequenos/medios
#   max_iter=1000     -> maximo de iteracoes ate convergir
#   class_weight='balanced' -> compensa o desbalanco 90/10
lr_pipe = make_pipeline(
    StandardScaler(),
    LogisticRegression(
        # penalty='l2' e o default; foi deprecated no sklearn 1.8.
        # Para regularizacao L2 usa-se C (inverso da forca da reg.)
        solver='lbfgs',
        max_iter=1000,
        class_weight='balanced',
        random_state=42,
    )
)
lr_grid = {
    # 'logisticregression__C' = nome do step + __ + nome do parametro
    'logisticregression__C': [0.01, 0.1, 1.0, 10.0],
}

# ++++++++++ Random Forest +++++++++++++++++
#
# Hyperparameters base:
#   n_estimators      -> nº de arvores (mais = melhor mas mais lento)
#   max_depth         -> profundidade max (None = cresce ate folha pura)
#   min_samples_split -> minimo de obs num no para o dividir
#   min_samples_leaf  -> minimo de obs por folha
#   max_features      -> features consideradas em cada split ('sqrt' tipico)
#   class_weight      -> 'balanced' para o desbalanco
#   n_jobs=-1         -> paraleliza por todos os cores
#   criterion         -> criterio de split (gini ou entropia)
# gini : mede a impureza do nó; menor é melhor (0 = nó puro)
# entropia: mede a incerteza do nó; menor é melhor (0 = nó puro)
rf_base = RandomForestClassifier(
    class_weight='balanced',
    n_jobs=-1,
    random_state=42,
)
rf_grid = {
    'criterion':        ['gini', 'entropy'],  # criterio de split (gini ou entropia)
    'n_estimators':     [100, 300, 500, 1000],
    'max_depth':        [None, 10, 20],
    'min_samples_leaf': [1, 5],
    'max_features':     ['sqrt', 'log2'],
}

# ---------- KNN ----------
# "Lazy learner" - nao treina; classifica pelo voto dos K vizinhos mais proximos.
#
# Hyperparameters base:
#   n_neighbors  -> K (numero de vizinhos)
#   weights      -> 'uniform' (todos pesam igual) ou 'distance' (mais proximos pesam mais)
#   metric       -> formula de distancia (minkowski c/ p=2 = euclidiana)
#   n_jobs=-1    -> paraleliza
knn_pipe = make_pipeline(
    StandardScaler(),  # KNN baseia-se em distancias -> scaling ESSENCIAL
    KNeighborsClassifier(
        metric='minkowski',
        p=2,
        n_jobs=-1,
    )
)
knn_grid = {
    'kneighborsclassifier__n_neighbors': [3, 5, 7, 10, 15],
    'kneighborsclassifier__weights':     ['uniform', 'distance'],
}

modelos = [
    ('LogisticRegression', lr_pipe, lr_grid),
    ('RandomForest',       rf_base, rf_grid),
    ('KNN',                knn_pipe, knn_grid),
]

# ----------------------------------------------------------
# 4. Para cada modelo: GridSearchCV + avaliacao + ROC + .pkl
# ----------------------------------------------------------
resultados = []
roc_data   = {}  # junta tudo no gráfico final

for nome, modelo, grid in modelos:
    print(f"\n{'='*60}")
    print(f"  {nome}")
    print('='*60)

    # GridSearchCV: cross-validation 5-fold para encontrar a melhor combinacao
    # de hyperparameters. scoring='f1_macro' trata as duas classes (boa/ma)
    # com igual peso — importante porque os dados estao desbalancados (~90/10).
    print("A correr GridSearchCV (cv=5, scoring='f1_macro')...")
    gs = GridSearchCV(
        estimator=modelo,
        param_grid=grid,
        cv=5,
        scoring='f1_macro',
        n_jobs=-1,
        verbose=0,
    )
    gs.fit(X_train, y_train)

    print(f"Melhores hyperparameters: {gs.best_params_}")
    print(f"Melhor F1 (cv-treino)   : {gs.best_score_:.4f}")

    # Modelo final (ja com os melhores params)
    final = gs.best_estimator_
    y_pred = final.predict(X_test)

    # Para a curva ROC precisamos das probabilidades
    # predict_proba devolve [P(False), P(True)] por linha; queremos P(True=boa)
    if hasattr(final, 'predict_proba'):
        y_proba = final.predict_proba(X_test)[:, 1]  # P(boa)
    else:
        y_proba = None

    # Metricas (pos_label=False -> classe 'ma' que importa)
    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, pos_label=False, zero_division=0)
    rec  = recall_score(y_test, y_pred, pos_label=False, zero_division=0)
    f1   = f1_score(y_test, y_pred, pos_label=False, zero_division=0)

    # ROC AUC (calculado contra a classe 'boa'=True)
    if y_proba is not None:
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        roc_auc_val = auc(fpr, tpr)
        roc_data[nome] = (fpr, tpr, roc_auc_val)
    else:
        roc_auc_val = None

    print(f"\nAccuracy        : {acc:.4f}")
    print(f"Precision (ma)  : {prec:.4f}")
    print(f"Recall    (ma)  : {rec:.4f}")
    print(f"F1        (ma)  : {f1:.4f}")
    if roc_auc_val is not None:
        print(f"ROC-AUC         : {roc_auc_val:.4f}")

    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=['ma', 'boa']))

    print("Matriz de confusao:")
    cm = confusion_matrix(y_test, y_pred, labels=[False, True])
    print(f"           Pred ma   Pred boa")
    print(f"Real ma    {cm[0,0]:>7d}   {cm[0,1]:>7d}")
    print(f"Real boa   {cm[1,0]:>7d}   {cm[1,1]:>7d}")

    pkl_path = f'Module_2/{nome.lower()}_classification.pkl'
    joblib.dump(final, pkl_path)
    print(f"\nModelo guardado em: {pkl_path}")

    resultados.append({
        'modelo':    nome,
        'tarefa':    'classificacao',
        'accuracy':  round(acc, 4),
        'precision': round(prec, 4),
        'recall':    round(rec, 4),
        'f1':        round(f1, 4),
        'roc_auc':   round(roc_auc_val, 4) if roc_auc_val is not None else '',
        'r2':        '',
        'mse':       '',
        'mae':       '',
    })

# ----------------------------------------------------------
# 5. Curvas ROC (todos os modelos no mesmo plot)
# ----------------------------------------------------------
plt.figure(figsize=(8, 7))
for nome, (fpr, tpr, roc_auc_val) in roc_data.items():
    plt.plot(fpr, tpr, lw=2, label=f'{nome} (AUC = {roc_auc_val:.3f})')

plt.plot([0, 1], [0, 1], color='gray', lw=1, linestyle='--',
         label='Classificador aleatorio')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('Taxa de Falsos Positivos (1 - Specificity)')
plt.ylabel('Taxa de Verdadeiros Positivos (Sensitivity)')
plt.title('Curvas ROC - Classificacao de air_quality_good')
plt.legend(loc='lower right')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(ROC_PNG, dpi=150, bbox_inches='tight')
plt.close()
print(f"\nCurvas ROC guardadas em: {ROC_PNG}")

# ----------------------------------------------------------
# 6. Escrever metrics.csv (preserva linhas de regressao)
# ----------------------------------------------------------
df_novos = pd.DataFrame(resultados)

try:
    df_existente = pd.read_csv(METRICS_CSV)
    df_existente = df_existente[df_existente['tarefa'] != 'classificacao']
    df_final = pd.concat([df_existente, df_novos], ignore_index=True)
except FileNotFoundError:
    df_final = df_novos

df_final.to_csv(METRICS_CSV, index=False)

print(f"\n{'='*60}")
print(f"  metrics.csv atualizado")
print('='*60)
print(df_final.to_string(index=False))
