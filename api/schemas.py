"""Contratos de entrada e saida da API do ChurnGuard.

Os nomes dos campos aqui sao a fonte da verdade para o aplicativo.
Eles correspondem as colunas do Iranian Churn Dataset, normalizadas
para snake_case (o CSV original usa espacos duplos em algumas colunas).
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ----------------------------------------------------------------- CLIENTES

class ClienteBase(BaseModel):
    identificador: str = Field(..., min_length=1, max_length=60,
                               description="Codigo do cliente na operadora")
    tariff_plan: int = Field(..., ge=1, le=2,
                             description="1 = pre-pago, 2 = pos-pago")
    observacao: Optional[str] = Field(None, max_length=300)


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    tariff_plan: Optional[int] = Field(None, ge=1, le=2)
    observacao: Optional[str] = Field(None, max_length=300)


class ClienteOut(ClienteBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime


# ----------------------------------------------------------------- PREDICAO

class PredictRequest(BaseModel):
    call_failure: int = Field(..., ge=0, description="Falhas de chamada no periodo")
    complains: int = Field(..., ge=0, le=1, description="0 = sem reclamacao, 1 = com reclamacao")
    subscription_length: int = Field(..., ge=0, description="Meses de assinatura")
    charge_amount: int = Field(..., ge=0, le=9, description="Faixa de cobranca, 0 = menor, 9 = maior")
    seconds_of_use: int = Field(..., ge=0, description="Segundos totais de chamada")
    frequency_of_use: int = Field(..., ge=0, description="Quantidade de chamadas")
    frequency_of_sms: int = Field(..., ge=0, description="Quantidade de mensagens")
    distinct_called_numbers: int = Field(..., ge=0, description="Numeros distintos acionados")
    age_group: int = Field(..., ge=1, le=5, description="Faixa etaria, 1 a 5")
    tariff_plan: int = Field(..., ge=1, le=2, description="1 = pre-pago, 2 = pos-pago")
    status: int = Field(..., ge=1, le=2, description="1 = ativo, 2 = nao ativo")
    age: int = Field(..., ge=0, le=120)
    customer_value: float = Field(..., ge=0, description="Valor calculado do cliente")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "call_failure": 8, "complains": 0, "subscription_length": 38,
                "charge_amount": 0, "seconds_of_use": 4370, "frequency_of_use": 71,
                "frequency_of_sms": 5, "distinct_called_numbers": 17, "age_group": 3,
                "tariff_plan": 1, "status": 1, "age": 30, "customer_value": 197.64
            }]
        }
    }


class Fator(BaseModel):
    campo: str = Field(..., description="Nome tecnico do atributo")
    rotulo: str = Field(..., description="Nome legivel, exibido na tela")
    impacto: Literal["aumenta", "reduz"] = Field(..., description="Direcao da contribuicao")
    peso: float = Field(..., description="Contribuicao absoluta, de 0 a 1")
    sugestao: str = Field(..., description="Acao de retencao sugerida")


class PredictResponse(BaseModel):
    probabilidade: float = Field(..., ge=0, le=1)
    faixa: Literal["baixo", "medio", "alto"]
    rotulo_faixa: str = Field(..., description="Texto exibido na tela")
    fatores: List[Fator]
    modelo_versao: str
    gerado_em: datetime
