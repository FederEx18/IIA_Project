## Resumo executivo

Este relatório analisa a qualidade do ar nas cidades de Lisboa e Porto durante o período de 10 de janeiro a 9 de dezembro de 2025. Foram recolhidas 1.442 observações, das quais 1243 foram classificadas como "NORMAL", 197 como "ALTO" e apenas 2 como "MODERADO". A cidade de Lisboa registou uma proporção mais elevada de alertas (17,3%) comparativamente ao Porto (10,3%). As principais regras acionadas foram a excedência do limite anual de partículas finas PM2.5 (R04_PM25_ALTO) e episódios de poluição multi-poluente com estagnação (R12_QUALIDADE_AR_PESSIMA). Os modelos de classificação e regressão utilizados indicaram que o RandomForest foi o melhor modelo, com métricas de precisão e recall adequadas, embora existam limitações significativas na cobertura geográfica e sazonal dos dados.

## Recomendações

### 1. **Ação para Partículas Finas PM2.5 Excedentes**
- **Gatilho Quantitativo**: Quando as concentrações de PM2.5 excederem 25 µg/m³ anualmente (UE) ou 15 µg/m³ em 24 horas (OMS 2021).
- **Fonte Regulamentar**: Diretiva 2008/50/CE; OMS 2021.
- **Grupo de Risco Específico**: Pessoas com asma, idosos, crianças e trabalhadores ao ar livre.
- **Ação**: Grupos sensíveis devem permanecer em ambientes internos. Recomenda-se o uso de máscaras FFP2 se necessário.

### 2. **Ação para Episódios de Poluição Multi-Poluente**
- **Gatilho Quantitativo**: Quando ocorrerem episódios de poluição multi-poluente com estagnação atmosférica.
- **Fonte Regulamentar**: Diretiva 2008/50/CE, artigo 24; conceito EEA AQI.
- **Grupo de Risco Específico**: Pessoas com condições respiratórias, idosos, crianças e trabalhadores ao ar livre.
- **Ação**: Qualidade do ar muito degradada, agravada por humidade alta. Grupos de risco devem evitar saídas.

## Limitações, Riscos e Considerações Éticas

### Desbalanço de Classes
O conjunto de dados apresenta um desbalanço significativo, com apenas 10% dos registos classificados como "ALTO" ou "MODERADO". Este desbalanço pode afetar a capacidade dos modelos de detetar corretamente situações críticas, aumentando o risco de falsos negativos.

### Cobertura Geográfica e Sazonal Limitada
Os dados foram recolhidos apenas nas cidades de Lisboa e Porto, o que limita a generalização dos resultados para outras regiões do país. Além disso, a cobertura sazonal é limitada a um período de 11 meses, o que pode não capturar variações sazonais importantes na qualidade do ar.

### Risco de Falsos Negativos em Saúde Pública
A existência de falsos negativos, onde situações de poluição são incorretamente classificadas como normais, representa um risco significativo para a saúde pública. Estes erros podem levar a uma subestimação dos riscos e a uma falta de medidas preventivas adequadas.

### Considerações Éticas
É crucial garantir que as informações sobre a qualidade do ar sejam comunicadas de forma clara e transparente, evitando jargão técnico excessivo. Deve-se também reconhecer as assimetrias de informação entre os decisores municipais e o público em geral, assegurando que todas as partes interessadas tenham acesso a informações relevantes e compreensíveis. Os modelos de machine learning devem ser vistos como ferramentas de apoio à decisão, nunca como decisores autónomos.