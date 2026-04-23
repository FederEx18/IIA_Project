"""
bayes_alerts.py
Módulo 1 — Rede Bayesiana
Projeto: IA para Cidades Sustentáveis

Rede Bayesiana (conforme codigo da professora Aula 5)
para estimar a probabilidade de má qualidade do ar em Lisboa e Porto.

"""

import pandas as pd
import matplotlib.pyplot as plt
from itertools import product
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

# ----------------------------------------------------------
# PATHS
# ----------------------------------------------
INPUT_CSV = "processed_lisboa_porto_air_quality.csv"


# ----------------------------------------------------------
# CARREGAR E CRIAR COLUNA ESTACAO ANO
# ----------------------------------------------------------

def carregar_dados(caminho=INPUT_CSV):
    df = pd.read_csv(caminho, sep=";")
    if "PM2.5" in df.columns:
        df.rename(columns={"PM2.5": "PM2_5"}, inplace=True)

    # Criar coluna de estação do ano a partir do mês
    def mes_para_estacao(mes):
        if mes in [6, 7, 8]:   return "verao"
        if mes in [12, 1, 2]:  return "inverno"
        if mes in [3, 4, 5]:   return "primavera"
        return "outono"

    df["estacao"] = df["month"].apply(mes_para_estacao)

    print(f"Dados carregados: {len(df)} registos")
    print(f"Estações: {df['estacao'].value_counts().to_dict()}")
    return df


# ----------------------------------------------------------
# DISCRETIZAÇÃO DAS VARIÁVEIS CONTÍNUAS
# ----------------------------------------------------------

def discretizar(df):
    """
    Converte as var continuas em categorias discretas.(Obrigatorio na rede bayesiana)
    Limites baseados na Diretiva 2008/50/CE e IPMA.
    """
    d = pd.DataFrame()

    # Estação do ano ( categorica discreta)
    d["estacao"] = df["estacao"]

    # NO2: baixo < 100 | moderado 100-200 | alto >= 200  (micro g/m3, Diretiva UE)
    d["no2"] = pd.cut(df["NO2"],
                      bins=[0, 100, 200, 500],
                      labels=["baixo", "moderado", "alto"])

    # Temperatura: fria < 15 | amena 15-30 | quente >= 30  (°C, IPMA)
    d["temperatura"] = pd.cut(df["temperature_c"],
                               bins=[-10, 15, 30, 60],
                               labels=["fria", "amena", "quente"])

    # Qualidade do ar: label existente no dataset
    d["qualidade_ar"] = df["air_quality_good"].map({True: "boa", False: "ma"})

    d = d.dropna()

    print(f"\nApós discretização: {len(d)} registos")
    for col in ["no2", "temperatura", "qualidade_ar", "estacao"]:
        print(f"  {col}: {dict(d[col].value_counts())}")

    return d


# ---------------------------------------------------
# REDE BAYESIANA 
# ----------------------------------------------------------

class BayesianNetwork:
    """
    Rede Bayesiana
    (Baseado no código da prof aula 5)
    Estrutura do DAG:
        estacao  ->temperatura
        estacao  -> no2
        temperatura + no2 -> qualidade_ar

    Cada no tem uma Tabela de Probabilidade Condicional estimada por contagem dos dados (Maximum Likelihood + Laplace).
    """

    def __init__(self):
        # Parents de cada nó na rede
        self.parents = {
            "estacao"     : [],                          # nó raiz — sem pais
            "temperatura" : ["estacao"],                 # depende da estação
            "no2"         : ["estacao"],                 # depende da estação
            "qualidade_ar": ["temperatura", "no2"],      # depende dos dois
        }
        self.cpds       = {}
        self.categories = {}

    def fit(self, df, alpha=1.0):
        """
        Estima as CPDs por Maximum Likelihood com suavização de Laplace (alpha).
        A suavização evita probabilidades zero quando há poucos dados.
        """
        # Guarda categorias possiveis de cada no
        for node in self.parents:
            if hasattr(df[node], "cat"):
                self.categories[node] = [str(c) for c in df[node].cat.categories]
            else:
                self.categories[node] = [str(c) for c in sorted(df[node].unique())]

        # Estima tabela de probabilidade de cada no
        for node, pais in self.parents.items():
            vals_node = self.categories[node]
            self.cpds[node] = {}

            if not pais:
                # No raiz — P(node)
                counts = df[node].value_counts()
                total  = counts.sum() + alpha * len(vals_node)
                self.cpds[node][()] = {
                    v: (counts.get(v, 0) + alpha) / total for v in vals_node
                }
            else:
                # No com parents — P(node | parents)
                vals_pais = [self.categories[p] for p in pais]
                for combo_pais in product(*vals_pais):
                    # Filtra linhas onde os parents tem estes valores
                    mask = pd.Series([True] * len(df), index=df.index)
                    for p, v in zip(pais, combo_pais):
                        mask &= (df[p].astype(str) == str(v))
                    subset = df[mask][node]
                    counts = subset.value_counts()
                    total  = counts.sum() + alpha * len(vals_node)
                    self.cpds[node][combo_pais] = {
                        v: (counts.get(v, 0) + alpha) / total for v in vals_node
                    }

        print("Probabilidades estimadas com sucesso")
        return self

    def p_cond(self, node, value, evidence):
        """Retorna P(node=value | pais)."""
        pais = self.parents[node]
        if not pais:
            return self.cpds[node][()].get(str(value), 0)
        key = tuple(str(evidence.get(p, "")) for p in pais)
        return self.cpds[node].get(key, {}).get(str(value), 1e-9)

    def query(self, evidencia):
        """Inferencia por enumeração:
        P(qualidade_ar | evidência) — soma sobre var não observadas.

        P(Q | e) = alpha × SOMA[P(Q, e, variáveis_ocultas)] 
        """
        probs = {}

        for valor_q in self.categories["qualidade_ar"]:
            soma = 0.0

            # Variaveis ocultas = não observadas e não é qualidade_ar
            ocultas  = [n for n in self.parents if n != "qualidade_ar" and n not in evidencia]
            dominios = [self.categories[n] for n in ocultas]

            for combo in product(*dominios):
                # Atribuição completa
                atrib = {"qualidade_ar": valor_q}
                atrib.update(evidencia)
                atrib.update(dict(zip(ocultas, combo)))

                # P(atribuição) = produto de todas as tabelas de prob. condicionais
                p = 1.0
                for node in self.parents:
                    p *= self.p_cond(node, atrib[node], atrib)

                soma += p

            probs[valor_q] = soma

        # Normalizar
        total = sum(probs.values())
        if total > 0:
            probs = {k: v / total for k, v in probs.items()}

        return probs


# ----------------------------------------------------------
# EXEMPLOS DE INFERÊNCIA (Perguntamos à rede)
# ----------------------------------------------------------

def mostrar_inferencias(bn):
    """
    Testa a rede com cenários concretos.
    """
    cenarios = [
        ("Sem evidência (prior)",              {}),
        ("Verão",                              {"estacao": "verao"}),
        ("Inverno",                            {"estacao": "inverno"}),
        ("NO2 baixo",                          {"no2": "baixo"}),
        ("NO2 moderado",                       {"no2": "moderado"}),
        ("NO2 alto",                           {"no2": "alto"}),
        ("Verão + NO2 baixo",                  {"estacao": "verao",    "no2": "baixo"}),
        ("Inverno + NO2 alto",                 {"estacao": "inverno",  "no2": "alto"}),
        ("Temperatura quente + NO2 alto",      {"temperatura": "quente", "no2": "alto"}),
        ("Temperatura fria + NO2 moderado",    {"temperatura": "fria",   "no2": "moderado"}),
    ]

    print()
    print("=" * 65)
    print("INFERÊNCIA — P(qualidade_ar | evidência)")
    print("=" * 65)
    print(f"{'Cenário':<38} {'P(boa)':>8} {'P(má)':>8} {'Previsão':>10}")
    print("-" * 65)

    for nome, ev in cenarios:
        probs    = bn.query(ev)
        p_boa    = probs.get("boa", 0)
        p_ma     = probs.get("ma", 0)
        previsao = "boa" if p_boa > p_ma else "má"
        print(f"{nome:<38} {p_boa:>8.3f} {p_ma:>8.3f} {previsao:>10}")

    print("=" * 65)


# ----------------------------------------------------------
#  AVALIAÇÃO 
# ----------------------------------------------------------

def avaliar_dataset(bn, df_disc):
    """
    Corre a rede para cada linha do dataset e avalia.
    """
    resultados = []
    for _, row in df_disc.iterrows():
        ev = {
            "estacao"    : str(row["estacao"]),
            "temperatura": str(row["temperatura"]),
            "no2"        : str(row["no2"]),
        }
        probs  = bn.query(ev)
        melhor = max(probs, key=probs.get)
        resultados.append({
            "real"    : str(row["qualidade_ar"]),
            "previsto": melhor,
            "p_boa"   : probs.get("boa", 0),
            "p_ma"    : probs.get("ma", 0),
        })

    df_res = pd.DataFrame(resultados)
    acc    = (df_res["real"] == df_res["previsto"]).mean()

    print(f"\nAccuracy da Rede Bayesiana: {acc:.1%}")
    print(f"Total de registos avaliados: {len(df_res)}\n")
    print(classification_report(df_res["real"], df_res["previsto"]))

    return df_res


# ----------------------------------------------------------
# GRAFICOS, MATRIZES E DIAGRAMAS DE CONFUSÃO
# ----------------------------------------------------------

def mostrar_graficos(df_res):
    """
    Gráficos de avaliação — seguindo o estilo do notebook da professora.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Matriz de confusão
    labels = ["boa", "ma"]

    cm = confusion_matrix(df_res["real"], df_res["previsto"], labels=labels)
    ConfusionMatrixDisplay(cm, display_labels=labels).plot(ax=axes[0], cmap="Blues")
    axes[0].set_title("Matriz de Confusão — Rede Bayesiana", fontweight="bold")

    # Distribuição das probabilidades (confiança do modelo)
    confianca = df_res[["p_boa", "p_ma"]].max(axis=1)
    axes[1].hist(confianca, bins=30, color="lightblue", alpha=0.8, edgecolor="white")
    media = confianca.mean()
    axes[1].axvline(media, color="red", linestyle="--", label=f"Média: {media:.2f}")
    axes[1].set_title("Confiança da Rede Bayesiana (P máxima)", fontweight="bold")
    axes[1].set_xlabel("P(estado mais provável)")
    axes[1].set_ylabel("Nº de registos")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig("bayes_resultados.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Gráfico guardado em 'bayes_resultados.png'")


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def executar_rede_bayesiana():
    # 1. Carregar dados
    df = carregar_dados()

    # 2. Discretizar variáveis
    df_disc = discretizar(df)

    # 3. Criar e treinar a rede
    bn = BayesianNetwork()
    bn.fit(df_disc)

    # 4. Exemplos de inferência (perguntar à rede))
    mostrar_inferencias(bn)

    # 5. Avaliar no dataset 
    df_res = avaliar_dataset(bn, df_disc)

    # 6. Grsfs
    mostrar_graficos(df_res)

if __name__ == "__main__":

    executar_rede_bayesiana()

    