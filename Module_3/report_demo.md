## Resumo executivo

Este relatório analisa a qualidade do ar nas cidades de Lisboa e Porto durante o período de 10 de janeiro a 9 de dezembro de 2025. Foram registradas 1442 observações, das quais 1243 foram classificadas como "NORMAL", 197 como "ALTO" e apenas 2 como "MODERADO". Os principais alertas foram relacionados à concentração de partículas finas PM2.5, que excederam os limites anuais da União Europeia (UE) e da Organização Mundial da Saúde (OMS). A cidade de Lisboa apresentou uma proporção maior de alertas (17.3%) em comparação com o Porto (10.3%). Os modelos de classificação e regressão utilizados para prever a qualidade do ar mostraram desempenho variável, com o RandomForest sendo o melhor modelo em ambos os casos.

## Recomendações

### 1. Ação para Partículas Finas PM2.5 Excedendo Limite Anual UE
- **Gatilho Quantitativo**: Concentração de PM2.5 superior a 25 µg/m³ (anual) conforme Diretiva 2008/50/CE e 15 µg/m³ (24h) conforme OMS 2021.
- **Fonte Regulamentar**: Diretiva 2008/50/CE, OMS 2021.
- **Grupo de Risco Específico**: Pessoas com asma, idosos, crianças e trabalhadores ao ar livre.
- **Ação**: Grupos sensíveis devem permanecer em ambientes internos. Recomenda-se o uso de máscaras FFP2 se necessário.

### 2. Ação para Episódios de Poluição Multi-Poluente com Estagnação
- **Gatilho Quantitativo**: Qualidade do ar muito degradada, agravada por condições de alta umidade.
- **Fonte Regulamentar**: Diretiva 2008/50/CE, art. 24 (episódios de poluição); conceito EEA AQI.
- **Grupo de Risco Específico**: Pessoas com asma, idosos, crianças e trabalhadores ao ar livre.
- **Ação**: Grupos de risco devem evitar saídas ao ar livre.

## Limitações, Riscos e Considerações Éticas

### Desbalanceamento de Classes
O conjunto de dados apresenta um desbalanceamento significativo, com apenas 10% dos registros classificados como "ALTO" ou "MODERADO". Este desbalanceamento pode afetar a capacidade dos modelos de aprendizado de máquina de detectar corretamente situações críticas, aumentando o risco de falsos negativos.

### Cobertura Geográfica e Sazonal Limitada
As observações foram coletadas apenas nas cidades de Lisboa e Porto, o que limita a generalização dos resultados para outras regiões do país. Além disso, o período de análise abrange apenas um ano, o que pode não capturar variações sazonais mais amplas na qualidade do ar.

### Risco de Falsos Negativos em Saúde Pública
Os modelos de classificação, embora tenham apresentado bom desempenho em termos de acurácia e ROC-AUC, mostraram recall e precisão moderados. Isso significa que há um risco de falsos negativos, onde situações de qualidade do ar ruim podem ser erroneamente classificadas como normais. Esses erros podem ter implicações graves para a saúde pública, especialmente para grupos de risco.

### Transparência e Ética
É importante reconhecer que os modelos são ferramentas de apoio à decisão e não devem ser usados como decisores autônomos. As decisões finais devem ser tomadas por especialistas humanos, levando em conta a totalidade das informações disponíveis, incluindo fatores contextuais e locais que podem não estar refletidos nos dados.

### Incerteza dos Modelos
Os modelos de machine learning, mesmo os melhores, têm incertezas inerentes. É crucial comunicar essas incertezas aos decisores e ao público, para evitar uma falsa sensação de segurança. As recomendações devem ser acompanhadas de declarações claras sobre a confiabilidade e os limites dos modelos utilizados.