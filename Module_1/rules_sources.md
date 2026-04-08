# Rules Sources (Module 1)

This file documents the official references used by the active rules in
[Module_1/regras.json](Module_1/regras.json), aligned with the current implementation in
[Module_1/rules_engine.py](Module_1/rules_engine.py).

## Core references

1. EU Directive 2008/50/EC (air-quality limits):
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32008L0050
2. WHO Global Air Quality Guidelines (2021):
https://www.who.int/publications/i/item/9789240034228
3. IPMA weather warnings:
https://www.ipma.pt/pt/enciclopedia/avisos.meteo/index.html
4. DGS public-health guidance:
https://www.dgs.pt/
5. TFUE Article 191 (precautionary principle):
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:12012E191
6. Canadian Fire Weather Index (reference for simplified wildfire logic):
https://cwfis.cfs.nrcan.gc.ca/background/summary/fwi
7. Beaufort wind scale context:
https://www.metoffice.gov.uk/weather/guides/coast-and-sea/beaufort-scale
8. WMO reference context:
https://cloudatlas.wmo.int/

## Rule mapping

1. R01_NO2_ALTO: NO2 >= 200 ug/m3 (EU hourly limit).
2. R02_NO2_MODERADO: 100 <= NO2 < 200 ug/m3 (precautionary operational band).
3. R03_PM10_ALTO: PM10 >= 50 ug/m3 (EU daily limit used conservatively in hourly data).
4. R04_PM25_ALTO: PM2.5 >= 25 ug/m3 (EU annual limit used conservatively in hourly data).
5. R05_O3_ALTO: O3 >= 180 ug/m3 (EU information threshold).
6. R06_CO_ALTO: CO_8h_avg >= 10 mg/m3 (EU 8h metric).
7. R07_SO2_ALTO: SO2 >= 350 ug/m3 (EU hourly limit).
8. R08_CALOR_EXTREMO: temperature >= 40 C (IPMA/DGS severe heat context).
9. R09_RISCO_INCENDIO: temperature >= 35 C and humidity <= 30% (simplified fire-weather rule inspired by FWI).
10. R10_VENTO_FORTE: wind >= 75 km/h (IPMA orange warning reference, gust-oriented in official usage).
11. R11_PRECIPITACAO_INTENSA: precipitation >= 10 mm/h (IPMA yellow threshold context).
12. R12_QUALIDADE_AR_PESSIMA: multi-pollutant episode condition with humidity >= 80%.

## Implementation alignment

1. Hourly input data: rules are evaluated row by row.
2. CO_8h_avg is implemented in code as rolling 8 records per city (minimum 6 valid values).
3. Missing values do not trigger a condition; the rule is skipped for that missing part.
4. Some extreme rules may trigger rarely in this dataset, which is expected.
