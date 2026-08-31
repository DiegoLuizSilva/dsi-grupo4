"""Pontos de corte das faixas de risco e traducao dos atributos.

Os cortes abaixo sao uma decisao do grupo, nao vem do dataset: o alvo
`Churn` do Iranian Churn Dataset e binario (0 ou 1), e as tres faixas
sao derivadas da probabilidade prevista. Qualquer alteracao aqui precisa
ser refletida no artigo.
"""

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
ATRIBUTOS = {
    "call_failure": {
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
        "rotulo": "Tempo total de uso",
        "sugestao_aumenta": "Uso baixo, oferecer pacote adequado ao consumo real",
        "sugestao_reduz": "Uso consistente, manter o plano atual",
    },
    "frequency_of_use": {
        "rotulo": "Frequencia de chamadas",
        "sugestao_aumenta": "Queda no uso, contatar o cliente para entender a mudanca",
        "sugestao_reduz": "Frequencia de uso saudavel",
    },
    "frequency_of_sms": {
        "rotulo": "Frequencia de mensagens",
        "sugestao_aumenta": "Baixo uso de mensagens, verificar se o pacote atende a necessidade",
        "sugestao_reduz": "Uso de mensagens dentro do esperado",
    },
    "distinct_called_numbers": {
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
        "sugestao_reduz": "Perfil etario sem impacto relevante",
    },
    "age_group": {
        "rotulo": "Faixa etaria",
        "sugestao_aumenta": "Adequar a oferta ao segmento etario",
        "sugestao_reduz": "Segmento etario sem impacto relevante",
    },
}


def descrever(campo: str, impacto: str) -> dict:
    """Devolve rotulo e sugestao de um atributo, conforme a direcao do impacto."""
    meta = ATRIBUTOS.get(campo, {
        "rotulo": campo,
        "sugestao_aumenta": "Avaliar este atributo junto ao cliente",
        "sugestao_reduz": "Atributo dentro do esperado",
    })
    chave = "sugestao_aumenta" if impacto == "aumenta" else "sugestao_reduz"
    return {"rotulo": meta["rotulo"], "sugestao": meta[chave]}
