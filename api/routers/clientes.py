"""Endpoints REST de CRUD de clientes usando Firestore.

Toda operacao e restrita a conta autenticada. O documento guarda o campo
`proprietario` com o `uid` de quem o criou, e a listagem filtra por ele. Sem
isso, publicar a API exporia os clientes de todas as contas a qualquer
requisicao que conhecesse o endereco do servico.

Lembrete de dominio: a colecao `clientes` guarda os assinantes AVALIADOS pelo
ChurnGuard. Quem usa o aplicativo fica na colecao `pessoas`. Sao coisas
diferentes e nao devem ser misturadas.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

import db
from schemas import ClienteCreate, ClienteOut, ClienteUpdate
from seguranca import Conta, conferir_dono, conta_atual

router = APIRouter(prefix="/clientes", tags=["clientes"])

COLECAO = "clientes"

# Campos que o cliente da API nao pode definir nem sobrescrever.
CAMPOS_CONTROLADOS = ("proprietario", "id")


def _colecao():
    try:
        return db.obter_db().collection(COLECAO)
    except db.ErroDePersistencia as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Banco de dados indisponivel: {erro}",
        ) from erro


def _sem_campos_controlados(dados: dict) -> dict:
    """Impede que a requisicao troque o dono do registro."""
    return {c: v for c, v in dados.items() if c not in CAMPOS_CONTROLADOS}


@router.get("", response_model=List[ClienteOut],
            summary="Lista os clientes da conta autenticada")
def listar(conta: Conta = Depends(conta_atual)):
    consulta = _colecao().where("proprietario", "==", conta.uid)

    clientes = []
    for doc in consulta.stream():
        dados = doc.to_dict()
        dados["id"] = doc.id
        clientes.append(dados)

    return clientes


@router.get("/{cliente_id}", response_model=ClienteOut,
            summary="Busca um cliente da conta autenticada")
def obter(cliente_id: str, conta: Conta = Depends(conta_atual)):
    doc = _colecao().document(cliente_id).get()
    if not doc.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")

    dados = doc.to_dict()
    conferir_dono(dados, conta, cliente_id)

    dados["id"] = doc.id
    return dados


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED,
             summary="Cadastra um cliente na conta autenticada")
def criar(dados: ClienteCreate, conta: Conta = Depends(conta_atual)):
    from google.cloud import firestore as gcf

    colecao = _colecao()
    ref = colecao.document()

    payload = _sem_campos_controlados(dados.model_dump())
    payload["proprietario"] = conta.uid
    payload["criado_em"] = gcf.SERVER_TIMESTAMP
    payload["atualizado_em"] = gcf.SERVER_TIMESTAMP

    ref.set(payload)

    criado = ref.get().to_dict()
    criado["id"] = ref.id
    return criado


@router.put("/{cliente_id}", response_model=ClienteOut,
            summary="Atualiza um cliente da conta autenticada")
def atualizar(cliente_id: str, dados: ClienteUpdate,
              conta: Conta = Depends(conta_atual)):
    from google.cloud import firestore as gcf

    ref = _colecao().document(cliente_id)
    doc = ref.get()

    if not doc.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")

    conferir_dono(doc.to_dict(), conta, cliente_id)

    campos = _sem_campos_controlados(dados.model_dump(exclude_unset=True))
    if not campos:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Nenhum campo informado para atualizacao",
        )

    campos["atualizado_em"] = gcf.SERVER_TIMESTAMP
    ref.update(campos)

    atualizado = ref.get().to_dict()
    atualizado["id"] = cliente_id
    return atualizado


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Remove um cliente da conta autenticada")
def remover(cliente_id: str, conta: Conta = Depends(conta_atual)):
    ref = _colecao().document(cliente_id)
    doc = ref.get()

    if not doc.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")

    conferir_dono(doc.to_dict(), conta, cliente_id)

    # O que acontece com o historico de avaliacoes deste cliente e uma decisao
    # combinada com a frente de frontend na Sprint 6 (registros orfaos nao
    # previstos). Enquanto a politica nao estiver implementada, a remocao do
    # cliente nao apaga as avaliacoes.
    ref.delete()
    return None
