"""Endpoint de avaliacao de risco de cancelamento.

Na Sprint 2 este endpoint responde a partir do modulo `stub`. Na Sprint 5,
a unica alteracao necessaria e trocar a funcao chamada em `_motor` pela
que carrega o modelo treinado. O formato da resposta nao muda.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

import stub
from faixas import ROTULO_FAIXA, classificar, descrever
from schemas import PredictRequest, PredictResponse

router = APIRouter(tags=["predicao"])

# Ponto unico de troca do stub pelo modelo real na Sprint 5.
_motor = stub.prever


@router.post("/predict", response_model=PredictResponse,
             summary="Avalia o risco de cancelamento de um cliente")
def prever(dados: PredictRequest):
    bruto = _motor(dados)

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
