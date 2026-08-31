"""Substituto temporario do modelo preditivo.

Este modulo existe para que o aplicativo possa ser construido em paralelo
ao treino do modelo. Ele devolve uma resposta com a MESMA estrutura que o
modelo real devolvera na Sprint 5, mas calculada por uma heuristica simples.

A heuristica e deterministica de proposito: a mesma entrada sempre produz
a mesma saida, o que permite escrever testes de tela e demonstrar o fluxo
sem depender de aleatoriedade.

NAO usar em producao nem relatar seus numeros no artigo.
"""

import math

from schemas import PredictRequest

MODELO_VERSAO = "stub-0.1"

# Cada entrada e (campo, peso, referencia).
# Peso positivo empurra para o cancelamento, negativo afasta.
# O valor de referencia e a mediana aproximada do dataset, usada para
# normalizar a contribuicao de cada atributo.
PESOS = [
    ("complains", 0.32, 0.0),
    ("call_failure", 0.14, 8.0),
    ("status", 0.18, 1.0),
    ("seconds_of_use", -0.16, 2990.0),
    ("frequency_of_use", -0.12, 54.0),
    ("subscription_length", -0.10, 35.0),
    ("customer_value", -0.09, 230.0),
    ("distinct_called_numbers", -0.08, 21.0),
    ("frequency_of_sms", -0.05, 21.0),
]

BASE = 0.34


def _contribuicao(valor: float, peso: float, referencia: float) -> float:
    """Contribuicao normalizada de um atributo em relacao a sua referencia."""
    if referencia == 0:
        desvio = 1.0 if valor > 0 else 0.0
    else:
        desvio = (valor - referencia) / referencia
        desvio = max(-1.5, min(1.5, desvio))
    return peso * desvio


def prever(dados: PredictRequest) -> dict:
    """Calcula probabilidade e fatores no mesmo formato do modelo real."""
    bruto = dados.model_dump()

    contribuicoes = []
    total = BASE

    for campo, peso, referencia in PESOS:
        valor = float(bruto[campo])
        c = _contribuicao(valor, peso, referencia)
        total += c
        contribuicoes.append((campo, c))

    # Logistica em vez de corte duro: um modelo real nunca devolve
    # exatamente 0 ou 1, e o corte duro deixava a saida com cara de mock.
    probabilidade = 1.0 / (1.0 + math.exp(-4.0 * (total - 0.5)))

    # Os tres atributos de maior contribuicao absoluta, como o SHAP fara.
    contribuicoes.sort(key=lambda x: abs(x[1]), reverse=True)
    principais = contribuicoes[:3]

    maior = max(abs(c) for _, c in principais) or 1.0

    fatores = []
    for campo, c in principais:
        fatores.append({
            "campo": campo,
            "impacto": "aumenta" if c > 0 else "reduz",
            "peso": round(abs(c) / maior, 4),
        })

    return {
        "probabilidade": round(probabilidade, 4),
        "fatores": fatores,
        "modelo_versao": MODELO_VERSAO,
    }
