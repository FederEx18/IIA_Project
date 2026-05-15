"""
train_regression.py
Modulo 2 - Treino dos modelos de regressao para prever NO2

Modelos:
  - Linear Regression       (linear, com StandardScaler)
  - Random Forest Regressor (nao-linear, ensemble)

Le:    data/regression_data_clean.csv  (gerado pelo eda.ipynb)
Grava: 2 modelos .pkl + metrics.csv (preserva classificacao) + residuals_regression.png

Correr (a partir da raiz do projeto IIA_Project):
   python Module_2/train_regression.py
"""

import pandas as pd
import joblib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # nao abre janela; so grava ficheiro
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# ----------------------------------------------------------
# PATHS
# ----------------------------------------------------------
ROOT        = Path(__file__).resolve().parent.parent
DATA_CSV    = ROOT / "data" / "regression_data_clean.csv"
METRICS_CSV = ROOT / "Module_2" / "resultados" / "metrics.csv"
RES_PNG     = ROOT / "Module_2" / "resultados" / "residuals_regression.png"
LR_PKL      = ROOT / "Module_2" / "resultados" / "linearregression_regression.pkl"
RF_PKL      = ROOT / "Module_2" / "resultados" / "randomforest_regression.pkl"

TARGET = 'NO2'

# ----------------------------------------------------------
# 1. Carregar dados
# ----------------------------------------------------------
df = pd.read_csv(DATA_CSV,encoding='utf-8')
print(f"Dataset: {df.shape[0]} linhas x {df.shape[1]} colunas")
print(f"\nEstatisticas da target ({TARGET}):")
print(df[TARGET].describe())

X = df.drop(columns=[TARGET])
y = df[TARGET]

# ----------------------------------------------------------
# 2. Split treino/teste
# ----------------------------------------------------------
# test_size=0.2     -> 80% treino, 20% teste
# random_state=42   -> reprodutibilidade
# (sem stratify    -> regressao tem target continua, nao se "estratifica")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"\nTreino: {len(X_train)} obs | Teste: {len(X_test)} obs")

# ----------------------------------------------------------
# 3. Definir os modelos + grids
# ----------------------------------------------------------

# ---------- Linear Regression ----------
# Regressor linear: y = b0 + b1*x1 + b2*x2 + ... + bn*xn + erro
# Estima os coeficientes b por minimos quadrados (OLS).
#
# Hyperparameters base:
#   fit_intercept=True -> calcula b0 (intercepto). Default True.
#                         (Se a variavel ja estiver centrada em zero,
#                         podia-se desligar — nao e o nosso caso.)
#
# Nota: LinearRegression "puro" nao tem hyperparameters significativos
# para tunar (ao contrario de Ridge/Lasso que tem alpha). Por isso nao
# fazemos GridSearchCV aqui — usamos directamente.
# StandardScaler ajuda a interpretar os coeficientes (ficam comparaveis
# entre features) sem afectar o R2.
linreg_pipe = make_pipeline(
    StandardScaler(),
    LinearRegression(fit_intercept=True)
)

# ---------- Random Forest Regressor ----------
# Mesma logica do classificador mas para prever um numero (media dos votos).
#
# Hyperparameters base:
#   n_estimators      -> nº de arvores
#   max_depth         -> profundidade max
#   min_samples_leaf  -> minimo de obs por folha
#   max_features      -> features consideradas em cada split
#                        (1.0 = todas; 'sqrt' = poucas, mais aleatorio)
#   n_jobs=-1         -> paraleliza
#   random_state=42   -> reprodutibilidade
rf_base = RandomForestRegressor(
    n_jobs=-1,
    random_state=42,
)
rf_grid = {
    'n_estimators':     [100, 300, 500],
    'max_depth':        [None, 10, 20],
    'min_samples_leaf': [1, 5],
    'max_features':     [1.0, 'sqrt'],
}

# ----------------------------------------------------------
# 4. Treinar, avaliar e guardar cada modelo
# ----------------------------------------------------------
resultados = []
preds_data = {}  # para o plot de residuos no fim

# ===== Linear Regression =====
print(f"\n{'='*60}")
print("  LinearRegression")
print('='*60)

linreg_pipe.fit(X_train, y_train)
y_pred_lr = linreg_pipe.predict(X_test)

r2_lr  = r2_score(y_test, y_pred_lr)
mse_lr = mean_squared_error(y_test, y_pred_lr)
mae_lr = mean_absolute_error(y_test, y_pred_lr)

print(f"R2  : {r2_lr:.4f}   ({r2_lr*100:.2f}% da variancia explicada)")
print(f"MSE : {mse_lr:.4f}")
print(f"MAE : {mae_lr:.4f}   ({TARGET} ug/m3)")

joblib.dump(linreg_pipe, LR_PKL)
print("Modelo guardado em: linearregression_regression.pkl")

preds_data['LinearRegression'] = (y_test.values, y_pred_lr)
resultados.append({
    'modelo':    'LinearRegression',
    'tarefa':    'regressao',
    'accuracy':  '',
    'precision': '',
    'recall':    '',
    'f1':        '',
    'roc_auc':   '',
    'r2':        round(r2_lr, 4),
    'mse':       round(mse_lr, 4),
    'mae':       round(mae_lr, 4),
})

# ===== Random Forest Regressor =====
print(f"\n{'='*60}")
print("  RandomForestRegressor")
print('='*60)

print("A correr GridSearchCV (cv=5, scoring='r2')...")
gs = GridSearchCV(
    estimator=rf_base,
    param_grid=rf_grid,
    cv=5,
    scoring='r2',
    n_jobs=-1,
    verbose=0,
)
gs.fit(X_train, y_train)
print(f"Melhores hyperparameters: {gs.best_params_}")
print(f"Melhor R2 (cv-treino)   : {gs.best_score_:.4f}")

rf_final = gs.best_estimator_
y_pred_rf = rf_final.predict(X_test)

r2_rf  = r2_score(y_test, y_pred_rf)
mse_rf = mean_squared_error(y_test, y_pred_rf)
mae_rf = mean_absolute_error(y_test, y_pred_rf)

print(f"\nR2  : {r2_rf:.4f}   ({r2_rf*100:.2f}% da variancia explicada)")
print(f"MSE : {mse_rf:.4f}")
print(f"MAE : {mae_rf:.4f}   ({TARGET} ug/m3)")

joblib.dump(rf_final, RF_PKL)
print("Modelo guardado em: randomforest_regression.pkl")

preds_data['RandomForest'] = (y_test.values, y_pred_rf)
resultados.append({
    'modelo':    'RandomForest',
    'tarefa':    'regressao',
    'accuracy':  '',
    'precision': '',
    'recall':    '',
    'f1':        '',
    'roc_auc':   '',
    'r2':        round(r2_rf, 4),
    'mse':       round(mse_rf, 4),
    'mae':       round(mae_rf, 4),
})

# ----------------------------------------------------------
# 5. Plot de diagnostico: Real vs Previsto + Distribuicao dos Residuos
# ----------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for i, (nome, (y_true, y_p)) in enumerate(preds_data.items()):
    residuos = y_true - y_p

    # Esquerda: Real vs Previsto (idealmente em cima da diagonal y=x)
    axes[i, 0].scatter(y_true, y_p, alpha=0.5, color='steelblue')
    lims = [min(y_true.min(), y_p.min()),
            max(y_true.max(), y_p.max())]
    axes[i, 0].plot(lims, lims, 'r--', linewidth=2, label='y = x (perfeito)')
    axes[i, 0].set_xlabel(f'{TARGET} real (ug/m3)')
    axes[i, 0].set_ylabel(f'{TARGET} previsto (ug/m3)')
    axes[i, 0].set_title(f'{nome} - Real vs Previsto')
    axes[i, 0].legend()
    axes[i, 0].grid(alpha=0.3)

    # Direita: Distribuicao dos residuos (idealmente centrada em 0, simetrica)
    axes[i, 1].hist(residuos, bins=30, edgecolor='black', alpha=0.7,
                    color='steelblue')
    axes[i, 1].axvline(0, color='red', linestyle='--', linewidth=2,
                       label='Residuo = 0')
    axes[i, 1].set_xlabel('Residuo (real - previsto)')
    axes[i, 1].set_ylabel('Frequencia')
    axes[i, 1].set_title(f'{nome} - Distribuicao dos residuos')
    axes[i, 1].legend()
    axes[i, 1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig(RES_PNG, dpi=150, bbox_inches='tight')
plt.close()
print(f"\nGrafico de residuos guardado em: residuals_regression.png")

# ----------------------------------------------------------
# 6. Escrever metrics.csv (preserva linhas de classificacao)
# ----------------------------------------------------------
df_novos = pd.DataFrame(resultados)

try:
    df_existente = pd.read_csv(METRICS_CSV)
    df_existente = df_existente[df_existente['tarefa'] != 'regressao']
    df_final = pd.concat([df_existente, df_novos], ignore_index=True)
except FileNotFoundError:
    df_final = df_novos

df_final.to_csv(METRICS_CSV, index=False)

print(f"\n{'='*60}")
print(f"  metrics.csv atualizado")
print('='*60)
print(df_final.to_string(index=False))
