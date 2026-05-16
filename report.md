## Resumo executivo

Foram analisadas 1442 observações horárias de qualidade do ar nas cidades de Lisboa, Porto, no período 2025-09-05 a 2025-10-05. O motor de regras identificou 199 situações com risco acima do nível normal (13.8 % do total).
 A regra mais ativada foi R04_PM25_ALTO (111 ocorrências), associada a Particulas finas PM2.5 excedem limite anual UE.
 Para a tarefa de classificação binária da qualidade do ar, o modelo RandomForest obteve F1 = 0.647 e ROC-AUC = 0.937, com recall = 0.759 na classe minoritária.
 Para a previsão de NO₂, o modelo RandomForest atingiu R² = 0.723 e MAE = 5.07 µg/m³.


## Recomendações

1. **R04_PM25_ALTO** — Grupos sensiveis permanecam em ambientes internos. Usar mascara FFP2 se necessario. (fonte: Diretiva 2008/50/CE (25 ug/m3, anual); WHO 2021 (15 ug/m3, 24h)).
2. **R12_QUALIDADE_AR_PESSIMA** — Qualidade do ar muito degradada agravada por humidade alta. Grupos de risco evitem saídas. (fonte: Diretiva 2008/50/CE art. 24 (episodios poluicao); conceito EEA AQI).
3. **R04_PM25_ALTO, R12_QUALIDADE_AR_PESSIMA** — sem ação registada (fonte: n/d).

## Limitações e riscos

- O dataset cobre apenas duas cidades portuguesas e dois meses; generalização sazonal e geográfica é limitada.
- A target air_quality_good é redefinida para gerar variabilidade (NO₂ ≥ 30 µg/m³ ∧ humidade ≥ 80 %), pelo que não é diretamente comparável com sistemas externos.
- O sistema é apoio à decisão, não decisor autónomo: cada alerta deve ser validado pela Proteção Civil antes de comunicação ao público.