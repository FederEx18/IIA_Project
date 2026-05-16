## Resumo Executivo

Este relatório analisa a qualidade do ar nas cidades de Lisboa e Porto durante o período de 10 de janeiro a 9 de dezembro de 2025. Foram recolhidas 1.442 observações, das quais 1243 foram classificadas como "NORMAL", 197 como "ALTO" e apenas 2 como "MODERADO". As principais regras acionadas foram relacionadas à concentração de partículas finas PM2.5, que excederam os limites anuais da União Europeia (UE) e da Organização Mundial da Saúde (OMS). A cidade de Lisboa registou uma proporção mais elevada de alertas (17.3%) comparativamente ao Porto (10.3%). Os modelos de classificação utilizados, nomeadamente o RandomForest, apresentaram uma precisão e eficácia razoáveis, mas com limitações significativas que devem ser consideradas.

## Recomendações

### 1. Monitorização e Ação em Caso de Excesso de PM2.5
- **Gatilho Quantitativo**: Concentração de PM2.5 superior a 25 µg/m³ (anual) conforme a Diretiva 2008/50/CE e 15 µg/m³ (24 horas) conforme a OMS 2021.
- **Ação**: Grupos sensíveis (pessoas com asma, idosos, crianças e trabalhadores ao ar livre) devem permanecer em ambientes internos. Recomenda-se o uso de máscaras FFP2 se necessário.

### 2. Prevenção de Episódios de Poluição Multi-Poluente
- **Gatilho Quantitativo**: Episódios de poluição com estagnação atmosférica, conforme a Diretiva 2008/50/CE, Artigo 24.
- **Ação**: Em caso de qualidade do ar muito degradada, especialmente com alta humidade, os grupos de risco (pessoas com asma, idosos, crianças e trabalhadores ao ar livre) devem evitar saídas ao ar livre.

## Limitações, Riscos e Considerações Éticas

### Desbalanceamento de Classes
O conjunto de dados apresenta um desbalanceamento significativo, com apenas 10% dos registos classificados como "ALTO" ou "MODERADO". Este desbalanceamento pode afetar a performance dos modelos, especialmente em termos de precisão e recall para as classes minoritárias.

### Cobertura Geográfica e Sazonal Limitada
As observações foram realizadas apenas nas cidades de Lisboa e Porto, o que limita a generalização dos resultados para outras regiões de Portugal. Além disso, a cobertura sazonal é limitada a um único ano, podendo não refletir padrões de longo prazo ou variações sazonais mais amplas.

### Risco de Falsos Negativos em Saúde Pública
Os modelos de classificação, apesar de apresentarem métricas razoáveis, têm um risco de produzir falsos negativos, ou seja, situações em que a qualidade do ar é classificada como "NORMAL" quando, na realidade, é "ALTO" ou "MODERADO". Isso pode levar a uma subestimação dos riscos à saúde pública, especialmente para grupos sensíveis.

### Considerações Éticas
É crucial que os modelos de classificação sejam utilizados como ferramentas de apoio à decisão e não como decisores autónomos. As recomendações devem ser sempre validadas por profissionais de saúde e ambientais antes de serem implementadas. Além disso, é importante garantir a transparência e a acessibilidade das informações aos cidadãos, evitando jargões técnicos e promovendo a compreensão dos riscos associados à qualidade do ar.

## Conclusão
Este relatório fornece uma análise detalhada da qualidade do ar em Lisboa e Porto, destacando as principais preocupações e recomendações para mitigar os riscos à saúde pública. No entanto, é essencial considerar as limitações e riscos associados aos dados e modelos utilizados, garantindo uma abordagem ética e transparente na comunicação e implementação das medidas recomendadas.