"""Endpoints REST de CRUD de clientes usando Firestore.

POLITICA DE ACESSO: CARTEIRA COMPARTILHADA
------------------------------------------
Os clientes avaliados pelo ChurnGuard formam uma carteira unica da equipe de
retencao. Qualquer conta autenticada consulta e mantem qualquer cliente. Quem
nao esta autenticado nao acessa nada.

A decisao e do dominio: uma operadora distribui a mesma carteira entre varios
gestores, e um cliente precisa ser atendido por quem estiver disponivel. Uma
carteira privada por conta impediria que um gestor assumisse o atendimento de
outro, que e justamente o caso de uso.

O campo `proprietario` continua sendo gravado na criacao, mas agora significa
AUTORIA -- quem cadastrou aquele registro -- e nao posse. Ele nao restringe
leitura nem alteracao. Serve para rastrear a origem do dado e nao pode ser
definido pela requisicao.

Esta politica e a mesma declarada em `firestore.rules`, que governa o acesso
direto do aplicativo ao banco. Antes desta versao os dois caminhos divergiam: a
API filtrava por `proprietario` enquanto as regras liberavam a carteira inteira.
Como o aplicativo le os clientes direto do Firestore, pelo `dbService.ts`, o
filtro da API nunca chegava a ser exercitado -- valia a regra mais permissiva, e
o sistema afirmava uma privacidade que nao tinha.

Lembrete de dominio: a colecao `clientes` guarda os assinantes AVALIADOS pelo
ChurnGuard. Quem usa o aplicativo fica na colecao `pessoas`, essa sim privada
por conta, conforme as regras do Firestore.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

import db
from schemas import ClienteCreate, ClienteOut, ClienteUpdate
from seguranca import Conta, conta_atual

router = APIRouter(prefix="/clientes", tags=["clientes"])

COLECAO = "clientes"

# Campos que a requisicao nao pode definir nem sobrescrever. `proprietario` esta
# aqui para que o registro de autoria permaneca confiavel: ele e preenchido pelo
# servidor, a partir do token, e nunca pelo corpo da requisicao.
CAMPOS_CONTROLADOS = ("proprietario", "id", "criado_em", "atualizado_em")


def _colecao():
    try:
        return db.obter_db().collection(COLECAO)
    except db.ErroDePersistencia as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Banco de dados indisponivel: {erro}",
        ) from erro


def _sem_campos_controlados(dados: dict) -> dict:
    return {c: v for c, v in dados.items() if c not in CAMPOS_CONTROLADOS}


@router.get("", response_model=List[ClienteOut],
            summary="Lista a carteira de clientes da equipe")
def listar(conta: Conta = Depends(conta_atual)):
    clientes = []
    for doc in _colecao().stream():
        dados = doc.to_dict()
        dados["id"] = doc.id
        clientes.append(dados)

    return clientes


@router.get("/{cliente_id}", response_model=ClienteOut,
            summary="Busca um cliente da carteira")
def obter(cliente_id: str, conta: Conta = Depends(conta_atual)):
    doc = _colecao().document(cliente_id).get()
    if not doc.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")

    dados = doc.to_dict()
    dados["id"] = doc.id
    return dados


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED,
             summary="Cadastra um cliente na carteira")
def criar(dados: ClienteCreate, conta: Conta = Depends(conta_atual)):
    from google.cloud import firestore as gcf

    ref = _colecao().document()

    payload = _sem_campos_controlados(dados.model_dump())
    # Autoria, nao posse: registra quem cadastrou, sem restringir o acesso.
    payload["proprietario"] = conta.uid
    payload["criado_em"] = gcf.SERVER_TIMESTAMP
    payload["atualizado_em"] = gcf.SERVER_TIMESTAMP

    ref.set(payload)

    criado = ref.get().to_dict()
    criado["id"] = ref.id
    return criado


@router.put("/{cliente_id}", response_model=ClienteOut,
            summary="Atualiza um cliente da carteira")
def atualizar(cliente_id: str, dados: ClienteUpdate,
              conta: Conta = Depends(conta_atual)):
    from google.cloud import firestore as gcf

    ref = _colecao().document(cliente_id)
    doc = ref.get()

    if not doc.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")

    campos = _sem_campos_controlados(dados.model_dump(exclude_unset=True))
    if not campos:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Nenhum campo informado para atualizacao",
        )

    campos["atualizado_em"] = gcf.SERVER_TIMESTAMP
    # Quem alterou por ultimo, preservando `proprietario` como quem criou.
    campos["atualizado_por"] = conta.uid

    ref.update(campos)

    atualizado = ref.get().to_dict()
    atualizado["id"] = cliente_id
    return atualizado


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Remove um cliente da carteira")
def remover(cliente_id: str, conta: Conta = Depends(conta_atual)):
    ref = _colecao().document(cliente_id)
    doc = ref.get()

    if not doc.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")

    # O que acontece com o historico de avaliacoes deste cliente ainda e uma
    # decisao em aberto com a frente de frontend (registros orfaos nao
    # previstos). Enquanto a politica nao estiver implementada, a remocao do
    # cliente nao apaga as avaliacoes.
    ref.delete()
    return None