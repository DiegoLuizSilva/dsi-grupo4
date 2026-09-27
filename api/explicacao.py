"""Calculo dos tres fatores exibidos na tela de resultado.

O aplicativo mostra tres fatores ordenados por contribuicao, cada um com
direcao do impacto e sugestao de retencao. Este modulo produz essa lista a
partir do modelo carregado, com duas estrategias:

    local   valores SHAP da propria instancia. Os fatores passam a ser daquele
            cliente, e e o que sustenta a Secao 6.1: sem explicacao por
            instancia, dois clientes de risco alto por motivos diferentes
            recebem a mesma lista, e a tela perde o sentido.
    global  importancia global do metadado ponderada pelo desvio do cliente em
            relacao ao valor de referencia. Aproximacao declarada.

ALINHAMENTO DAS COLUNAS
-----------------------
O ponto delicado deste modulo. O explicador opera sobre o estimador final, ou
seja, sobre os dados JA transformados pelo pipeline. Um `ColumnTransformer`
reordena as colunas: no pipeline do projeto, os nove atributos numericos sao
escalados primeiro e os tres binarios passam depois, de modo que a ordem vista
pelo estimador nao e a ordem declarada em `atributos`.

Casar o vetor SHAP com a ordem de entrada inverte o sinal de atributos que
mudaram de posicao. Foi medido: em um cliente com reclamacao registrada, a
contribuicao de `complains` aparecia como -0,046 (reduz) quando a correta e
+0,408 (aumenta) -- e a probabilidade salta de 0,01 para 0,605 quando a
reclamacao entra, o que confirma qual e a certa. A tela diria que a reclamacao
protege o cliente, com a probabilidade correta ao lado.

Por isso os nomes usados aqui vem de `motor.atributos_explicados`, derivado de
`get_feature_names_out()` das etapas de transformacao, e nunca de
`motor.atributos`. Quando nao ha transformacao, as duas listas coincidem.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("churnguard.explicacao")

QUANTIDADE_DE_FATORES = 3

# Abaixo deste valor a contribuicao e considerada irrelevante e o fator nao e
# exibido. Evita ocupar a tela com um atributo cujo peso arredonda para zero.
PISO_DE_CONTRIBUICAO = 1e-6


def calcular(motor: Any, bruto: dict, linha: dict) -> list[dict]:
    """Devolve ate tres fatores no formato que `routers/predict.py` espera.

    `bruto` sao os campos como o aplicativo enviou, `linha` os campos apos o
    tratamento declarado no metadado.
    """
    contribuicoes: list[tuple[str, float]] | None = None

    if motor.explicador is not None:
        try:
            contribuicoes = _por_shap(motor, linha)
        except Exception as erro:
            # A explicacao nunca derruba a predicao: a faixa de risco e a
            # informacao principal e continua correta sem os fatores.
            logger.warning("SHAP falhou (%s); usando a estrategia global.", erro)

    if contribuicoes is None:
        contribuicoes = _por_importancia_global(motor, bruto)

    return _formatar(contribuicoes)


# ------------------------------------------------------------ estrategia local

def _por_shap(motor: Any, linha: dict) -> list[tuple[str, float]]:
    """Contribuicao SHAP de cada atributo para a classe de cancelamento."""
    import numpy as np
    import pandas as pd

    X = pd.DataFrame([linha], columns=motor.atributos)

    # O explicador foi construido sobre o estimador final, entao a instancia
    # precisa passar pelas etapas de transformacao antes.
    if motor.transformar_para_explicar:
        X = motor.transformar(X)

    nomes = motor.atributos_explicados
    valores = motor.explicador.shap_values(X)
    vetor = np.asarray(_extrair_vetor(valores, motor.indice_churn, len(nomes))).ravel()

    if len(vetor) != len(nomes):
        raise ValueError(
            f"SHAP devolveu {len(vetor)} contribuicoes para {len(nomes)} "
            f"atributos ({nomes})."
        )

    return [(nome, float(v)) for nome, v in zip(nomes, vetor)]


def _extrair_vetor(valores: Any, indice_churn: int, n_atributos: int) -> Any:
    """Normaliza os varios formatos de saida do SHAP em um vetor unico.

    Em classificacao binaria o formato mudou entre versoes da biblioteca:
    versoes antigas devolvem uma lista com um array por classe; versoes
    recentes devolvem um unico array com a classe na ultima dimensao. Alguns
    modelos devolvem apenas a classe positiva. Tratar os tres casos evita
    escolher o sinal errado, que inverteria a direcao de todos os fatores.
    """
    import numpy as np

    if isinstance(valores, list):
        escolhido = valores[indice_churn] if len(valores) > indice_churn else valores[-1]
        return np.asarray(escolhido)[0]

    arranjo = np.asarray(valores)

    if arranjo.ndim == 3:  # (instancias, atributos, classes)
        return arranjo[0, :, indice_churn]

    if arranjo.ndim == 2:
        if arranjo.shape == (1, n_atributos):
            return arranjo[0]
        if arranjo.shape == (n_atributos, 2):  # (atributos, classes)
            return arranjo[:, indice_churn]
        return arranjo[0]

    return arranjo


# ----------------------------------------------------------- estrategia global

def _por_importancia_global(motor: Any, bruto: dict) -> list[tuple[str, float]]:
    """Importancia global ponderada pelo desvio do cliente.

    O sinal vem do desvio: um atributo cujo valor esta acima da referencia
    contribui em uma direcao, abaixo na outra. Para atributos em que o valor
    alto protege contra o cancelamento (uso, tempo de assinatura, valor do
    cliente), o sentido e invertido conforme SENTIDO.
    """
    explicacao = motor.metadados.get("explicacao") or {}
    importancias = explicacao.get("importancias") or {}
    referencias = explicacao.get("referencias") or {}

    if not importancias:
        importancias = _importancias_do_estimador(motor)

    contribuicoes: list[tuple[str, float]] = []

    # Percorre os atributos de ENTRADA, porque a estrategia global compara o
    # valor original do cliente com a referencia, antes de qualquer escala.
    for campo in motor.atributos:
        peso = float(importancias.get(campo, 0.0))
        if peso <= 0:
            continue

        valor = bruto.get(campo)
        if valor is None:
            continue

        desvio = _desvio(float(valor), referencias.get(campo))
        contribuicoes.append((campo, peso * desvio * SENTIDO.get(campo, 1.0)))

    return contribuicoes


def _desvio(valor: float, referencia: Any) -> float:
    """Desvio relativo, limitado para um atributo extremo nao dominar a lista."""
    if referencia is None:
        return 1.0 if valor > 0 else -1.0
    referencia = float(referencia)
    if referencia == 0:
        return 1.0 if valor > 0 else -1.0
    return max(-1.5, min(1.5, (valor - referencia) / referencia))


# Sentido do atributo quando seu valor esta ACIMA da referencia.
# Positivo empurra para o cancelamento, negativo afasta.
# Usado apenas na estrategia global; com SHAP o sinal vem do proprio modelo.
SENTIDO = {
    "complains": 1.0,
    "call_failure": 1.0,
    "status": 1.0,
    "charge_amount": 1.0,
    "tariff_plan": 1.0,
    "age": 1.0,
    "seconds_of_use": -1.0,
    "frequency_of_use": -1.0,
    "frequency_of_sms": -1.0,
    "distinct_called_numbers": -1.0,
    "subscription_length": -1.0,
    "customer_value": -1.0,
}


def _importancias_do_estimador(motor: Any) -> dict[str, float]:
    """Ultimo recurso: le feature_importances_ do estimador final.

    Usa `atributos_explicados`, porque `feature_importances_` tambem segue a
    ordem vista pelo estimador, nao a ordem de entrada.
    """
    estimador = motor.estimador_final()
    valores = getattr(estimador, "feature_importances_", None)

    if valores is None:
        logger.warning(
            "Sem importancias no metadado e sem feature_importances_ no estimador. "
            "Os fatores serao ordenados apenas pelo desvio."
        )
        return {campo: 1.0 for campo in motor.atributos}

    logger.warning(
        "Importancias lidas de feature_importances_ por ausencia no metadado. "
        "Preencher explicacao.importancias conforme ml/CONTRATO_MODELO.md."
    )
    return {
        campo: float(v)
        for campo, v in zip(motor.atributos_explicados, valores)
    }


# --------------------------------------------------------------- formatacao

def _formatar(contribuicoes: list[tuple[str, float]]) -> list[dict]:
    """Ordena por contribuicao absoluta e normaliza o peso entre 0 e 1.

    O peso e relativo ao maior fator exibido, nao a probabilidade. A tela usa
    isso para dimensionar a barra de cada fator; nao e percentual de risco, e
    nao deve ser apresentado como tal.
    """
    relevantes = [(campo, c) for campo, c in contribuicoes if abs(c) > PISO_DE_CONTRIBUICAO]
    relevantes.sort(key=lambda item: abs(item[1]), reverse=True)
    principais = relevantes[:QUANTIDADE_DE_FATORES]

    if not principais:
        return []

    maior = max(abs(c) for _, c in principais) or 1.0

    return [
        {
            "campo": campo,
            "impacto": "aumenta" if c > 0 else "reduz",
            "peso": round(abs(c) / maior, 4),
        }
        for campo, c in principais
    ]
