## Resumo Executivo

Este relatório analisa a qualidade do ar nas cidades de Lisboa e Porto durante o período de 10 de janeiro a 9 de dezembro de 2025. Foram recolhidas 1.442 observações, das quais 1243 foram classificadas como "NORMAL", 197 como "ALTO" e 2 como "MODERADO". Os principais alertas foram relacionados à concentração de partículas finas PM2.5, que excederam os limites anuais da União Europeia e da OMS, e a episódios de poluição multi-poluente com estagnação. Lisboa registou uma percentagem mais elevada de alertas (17,3%) comparativamente ao Porto (10,3%). Os modelos de classificação utilizados apresentaram diferentes métricas de desempenho, sendo o RandomForest o modelo com melhor performance geral.

## Recomendações

### 1. Ação para Partículas Finas PM2.5 Excedentes
- **Gatilho Quantitativo**: Concentração de PM2.5 superior a 25 µg/m³ (anual) ou 15 µg/m³ (24 horas).
- **Fonte Regulamentar**: Diretiva 2008/50/CE; OMS 2021.
- **Grupo de Risco Específico**: Pessoas com asma, idosos, crianças e trabalhadores ao ar livre.
- **Ação**: Os grupos sensíveis devem permanecer em ambientes internos. Recomenda-se o uso de máscaras FFP2 se necessário.

### 2. Ação para Episódios de Poluição Multi-Poluente com Estagnação
- **Gatilho Quantitativo**: Qualidade do ar muito degradada, agravada por humidade alta.
- **Fonte Regulamentar**: Diretiva 2008/50/CE, artigo 24; conceito EEA AQI.
- **Grupo de Risco Específico**: Pessoas com condições respiratórias, idosos, crianças e indivíduos com doenças cardiovasculares.
- **Ação**: Evitar saídas ao ar livre. Manter janelas fechadas e utilizar sistemas de filtragem de ar quando possível.

## Limitações, Riscos e Considerações Éticas

### Desbalanço de Classes
O conjunto de dados apresenta um desbalanço significativo entre as classes, com apenas 10% dos registos classificados como "má". Este desbalanço pode afetar a capacidade dos modelos de detetar corretamente situações críticas, aumentando o risco de falsos negativos.

### Cobertura Geográfica e Sazonal Limitada
As observações foram realizadas apenas nas cidades de Lisboa e Porto, o que limita a generalização dos resultados para outras regiões do país. Além disso, o período de análise abrange apenas um ano, podendo não capturar variações sazonais mais amplas.

### Risco de Falsos Negativos em Saúde Pública
Os modelos de classificação, apesar de apresentarem boas métricas de desempenho, ainda têm um risco de produzir falsos negativos, especialmente em situações onde a qualidade do ar é crítica. Falsos negativos podem levar a decisões inadequadas que comprometem a saúde pública.

### Incerteza dos Modelos
Os modelos são ferramentas de apoio à decisão e não devem ser considerados como decisores autónomos. É importante manter uma avaliação contínua e a integração de novos dados para melhorar a precisão e a fiabilidade das previsões.

### Assimetrias de Informação
Existem assimetrias de informação entre os decisores municipais e o público em geral. É crucial garantir que as informações sobre a qualidade do ar sejam comunicadas de forma clara e acessível, evitando jargão técnico excessivo, para que todos possam tomar decisões informadas.

### Viés
Os modelos podem estar sujeitos a viés se os dados de treino não forem representativos de todas as condições ambientais e demográficas. É importante monitorizar continuamente os modelos e ajustá-los conforme necessário para minimizar o viés.

Este relatório visa fornecer uma base sólida para a tomada de decisões informadas, reconhecendo as limitações e riscos associados aos dados e modelos utilizados.