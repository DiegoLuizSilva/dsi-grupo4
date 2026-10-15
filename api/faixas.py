"""Pontos de corte das faixas de risco e traducao dos atributos.

Os cortes abaixo sao uma decisao do grupo, nao vem do dataset: o alvo
`Churn` do Iranian Churn Dataset e binario (0 ou 1), e as tres faixas
sao derivadas da probabilidade prevista. Qualquer alteracao aqui precisa
ser refletida no artigo.
"""

from __future__ import annotations

CORTE_BAIXO = 0.30
CORTE_ALTO = 0.65

ROTULO_FAIXA = {
    "baixo": "Risco baixo",
    "medio": "Risco medio",
    "alto": "Risco alto",
}


def classificar(probabilidade: float) -> str:
    """Converte a probabilidade prevista em uma das tres faixas."""
    if probabilidade < CORTE_BAIXO:
        return "baixo"
    if probabilidade <= CORTE_ALTO:
        return "medio"
    return "alto"


# Traducao dos atributos tecnicos para linguagem de tela.
# O campo `sugestao` atende o requisito HU08 do documento de requisitos.
#
# `aumenta_quando` diz de que lado da referencia (mediana da carteira, em
# ml/artefatos/metadados.json) o texto de `sugestao_aumenta` foi escrito. As
# sugestoes descrevem o valor do cliente ("uso baixo", "cliente recente"), mas o
# Random Forest nao e monotono: o mesmo atributo pode aumentar o risco com valor
# alto em um perfil e com valor baixo em outro. Quando o sinal do fator e o lado
# do valor nao combinam com o texto, `descrever` usa uma sugestao neutra em vez de
# afirmar algo falso sobre o cliente. Atributos binarios ou sem direcao no texto
# nao tem `aumenta_quando`.
ATRIBUTOS = {
    "call_failure": {
        "aumenta_quando": "acima",
        "rotulo": "Falhas de chamada",
        "sugestao_aumenta": "Abrir chamado tecnico para avaliar a cobertura na regiao do cliente",
        "sugestao_reduz": "Rede estavel para este cliente, sem acao tecnica necessaria",
    },
    "complains": {
        "rotulo": "Reclamacoes registradas",
        "sugestao_aumenta": "Retornar o contato em ate 48 horas e verificar se a reclamacao foi resolvida",
        "sugestao_reduz": "Cliente sem reclamacoes no periodo",
    },
    "subscription_length": {
        "aumenta_quando": "abaixo",
        "rotulo": "Tempo de assinatura",
        "sugestao_aumenta": "Cliente recente, oferecer acompanhamento nos primeiros meses",
        "sugestao_reduz": "Cliente de longa data, considerar beneficio por tempo de casa",
    },
    "charge_amount": {
        "rotulo": "Faixa de cobranca",
        "sugestao_aumenta": "Revisar o plano contratado e verificar se o valor esta compativel com o uso",
        "sugestao_reduz": "Faixa de cobranca compativel com o perfil",
    },
    "seconds_of_use": {
        "aumenta_quando": "abaixo",
        "rotulo": "Tempo total de uso",
        "sugestao_aumenta": "Uso baixo, oferecer pacote adequado ao consumo real",
        "sugestao_reduz": "Uso consistente, manter o plano atual",
    },
    "frequency_of_use": {
        "aumenta_quando": "abaixo",
        "rotulo": "Frequencia de chamadas",
        "sugestao_aumenta": "Queda no uso, contatar o cliente para entender a mudanca",
        "sugestao_reduz": "Frequencia de uso saudavel",
    },
    "frequency_of_sms": {
        "aumenta_quando": "abaixo",
        "rotulo": "Frequencia de mensagens",
        "sugestao_aumenta": "Baixo uso de mensagens, verificar se o pacote atende a necessidade",
        "sugestao_reduz": "Uso de mensagens dentro do esperado",
    },
    "distinct_called_numbers": {
        "aumenta_quando": "abaixo",
        "rotulo": "Contatos distintos acionados",
        "sugestao_aumenta": "Rede de contatos reduzida, indicio de migracao para outra operadora",
        "sugestao_reduz": "Rede de contatos ativa na operadora",
    },
    "status": {
        "rotulo": "Situacao da linha",
        "sugestao_aumenta": "Linha nao ativa, priorizar contato imediato",
        "sugestao_reduz": "Linha ativa",
    },
    "customer_value": {
        "aumenta_quando": "abaixo",
        "rotulo": "Valor do cliente",
        "sugestao_aumenta": "Valor abaixo da media da carteira, avaliar oferta de upgrade",
        "sugestao_reduz": "Cliente de valor relevante, priorizar retencao",
    },
    "tariff_plan": {
        "rotulo": "Tipo de plano",
        "sugestao_aumenta": "Avaliar migracao para plano com melhor custo-beneficio",
        "sugestao_reduz": "Plano adequado ao perfil",
    },
    "age": {
        "rotulo": "Idade",
        "sugestao_aumenta": "Adequar o canal de contato ao perfil etario",
        "sugestao_reduz": "Manter acompanhamento adequado ao perfil etario",
    },
    "age_group": {
        "rotulo": "Faixa etaria",
        "sugestao_aumenta": "Adequar a oferta ao segmento etario",
        "sugestao_reduz": "Segmento etario sem impacto relevante",
    },
}


def _lado(valor, referencia) -> str | None:
    """'acima' ou 'abaixo' da referencia; None se igual ou se faltar dado."""
    if valor is None or referencia is None:
        return None
    valor, referencia = float(valor), float(referencia)
    if valor > referencia:
        return "acima"
    if valor < referencia:
        return "abaixo"
    return None


def _sugestao_neutra(rotulo: str, impacto: str, lado: str) -> str:
    """Sugestao para quando o texto especifico contradiria o valor do cliente."""
    if impacto == "aumenta":
        return (
            f"{rotulo} {lado} da mediana da carteira; neste perfil, esse valor pesa "
            "a favor do cancelamento. Revisar o historico recente do cliente"
        )
    return f"{rotulo} {lado} da mediana da carteira, sem indicar risco neste perfil"


def descrever(campo: str, impacto: str, valor=None, referencia=None) -> dict:
    """Devolve rotulo e sugestao de um atributo, conforme a direcao do impacto.

    Com `valor` e `referencia`, confere se a sugestao especifica descreve o
    cliente de verdade. Ex.: "Rede de contatos reduzida" so aparece quando os
    contatos distintos estao abaixo da mediana.
    """
    meta = ATRIBUTOS.get(campo, {
        "rotulo": campo,
        "sugestao_aumenta": "Avaliar este atributo junto ao cliente",
        "sugestao_reduz": "Atributo dentro do esperado",
    })

    esperado = meta.get("aumenta_quando")
    lado = _lado(valor, referencia)
    if esperado and lado:
        coerente = (lado == esperado) if impacto == "aumenta" else (lado != esperado)
        if not coerente:
            return {"rotulo": meta["rotulo"],
                    "sugestao": _sugestao_neutra(meta["rotulo"], impacto, lado)}

    chave = "sugestao_aumenta" if impacto == "aumenta" else "sugestao_reduz"
    return {"rotulo": meta["rotulo"], "sugestao": meta[chave]}
