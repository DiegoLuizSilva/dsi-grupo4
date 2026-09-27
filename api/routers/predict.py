"""Endpoint de avaliacao de risco de cancelamento.

A partir da Sprint 5 este endpoint responde pelo modelo treinado, carregado
por `modelo.py`. O modulo `stub.py` permanece no repositorio como substituto
de desenvolvimento e continua sendo usado quando o pacote do modelo nao esta
presente na maquina, para que as frentes de aplicativo nao fiquem bloqueadas.

A troca nao e silenciosa: a resposta sempre carrega `modelo_versao`, e o stub
se identifica como `stub-0.1`. O endpoint /health informa qual motor esta
ativo. Nenhum numero produzido pelo stub entra no artigo.

Em ambiente publicado, `CHURNGUARD_PERMITIR_STUB=0` faz a API responder 503
em vez de cair para o stub, evitando uma demonstracao acidental sem modelo.
"""

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

import modelo
import stub
from faixas import ROTULO_FAIXA, classificar, descrever
from schemas import PredictRequest, PredictResponse
from seguranca import Conta, conta_atual

logger = logging.getLogger("churnguard.predict")

router = APIRouter(tags=["predicao"])


def _stub_permitido() -> bool:
    return os.getenv("CHURNGUARD_PERMITIR_STUB", "1") not in ("0", "false", "False")


def _motor_ativo():
    """Escolhe o motor a cada requisicao.

    A escolha por requisicao, e nao no import, permite colocar o artefato no
    lugar e passar a usar o modelo real sem reiniciar o processo. E o que a
    Sprint 6 cobra ao pedir a validacao da substituicao controlada do arquivo
    de modelo preservando o contrato.
    """
    try:
        modelo.carregar()
        return modelo.prever, False
    except modelo.ErroDeCarregamento as erro:
        if not _stub_permitido():
            logger.error("Modelo indisponivel e stub bloqueado: %s", erro)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "O modelo de predicao nao esta disponivel neste ambiente. "
                    "A avaliacao de risco esta temporariamente suspensa."
                ),
            ) from erro

        logger.warning("Respondendo pelo stub: %s", erro)
        return stub.prever, True


@router.post("/predict", response_model=PredictResponse,
             summary="Avalia o risco de cancelamento de um cliente")
def prever(dados: PredictRequest, conta: Conta = Depends(conta_atual)):
    # A rota exige autenticacao como as de dados. Carregar o modelo e calcular
    # a explicacao tem custo, e uma rota aberta em ambiente publicado fica
    # disponivel para qualquer requisicao que conheca o endereco.
    motor, usando_stub = _motor_ativo()

    try:
        bruto = motor(dados)
    except modelo.ErroDeDominio as erro:
        # Valor fora do dominio que o modelo conhece. E erro da requisicao,
        # nao do servidor: 422 mantem a coerencia com a validacao do Pydantic.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erro),
        ) from erro
    except modelo.ErroDeCarregamento as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Falha ao carregar o modelo: {erro}",
        ) from erro
    except Exception as erro:
        logger.exception("Falha inesperada na predicao.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel concluir a avaliacao.",
        ) from erro

    if usando_stub:
        logger.warning(
            "Avaliacao respondida pelo stub. Nao usar este resultado como evidencia."
        )

    faixa = classificar(bruto["probabilidade"])

    fatores = []
    for f in bruto["fatores"]:
        texto = descrever(f["campo"], f["impacto"])
        fatores.append({
            "campo": f["campo"],
            "rotulo": texto["rotulo"],
            "impacto": f["impacto"],
            "peso": f["peso"],
            "sugestao": texto["sugestao"],
        })

    return {
        "probabilidade": bruto["probabilidade"],
        "faixa": faixa,
        "rotulo_faixa": ROTULO_FAIXA[faixa],
        "fatores": fatores,
        "modelo_versao": bruto["modelo_versao"],
        "gerado_em": datetime.now(timezone.utc),
    }
