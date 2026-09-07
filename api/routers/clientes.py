"""Endpoints REST de CRUD de clientes usando Firestore."""

from typing import List
from fastapi import APIRouter, HTTPException, status
from db import obter_db
from schemas import ClienteCreate, ClienteOut, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["clientes"])

@router.get("", response_model=List[ClienteOut], summary="Lista todos os clientes")
def listar():
    db = obter_db()
    docs = db.collection("clientes").stream()
    clientes = []
    for doc in docs:
        dados = doc.to_dict()
        dados["id"] = doc.id  # Firestore usa string como ID
        clientes.append(dados)
    return clientes


@router.get("/{cliente_id}", response_model=ClienteOut, summary="Busca um cliente pelo id")
def obter(cliente_id: str):
    db = obter_db()
    doc = db.collection("clientes").document(cliente_id).get()
    if not doc.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")
    
    dados = doc.to_dict()
    dados["id"] = doc.id
    return dados


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED,
             summary="Cadastra um cliente")
def criar(dados: ClienteCreate):
    db = obter_db()
    # Adiciona no Firestore
    novo_ref = db.collection("clientes").document()
    payload = dados.model_dump()
    
    # Salva gerando os campos de controle padrao
    db.collection("clientes").document(novo_ref.id).set(payload)
    
    doc_criado = db.collection("clientes").document(novo_ref.id).get()
    resultado = doc_criado.to_dict()
    resultado["id"] = novo_ref.id
    return resultado


@router.put("/{cliente_id}", response_model=ClienteOut, summary="Atualiza um cliente")
def atualizar(cliente_id: str, dados: ClienteUpdate):
    db = obter_db()
    doc_ref = db.collection("clientes").document(cliente_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")

    campos = dados.model_dump(exclude_unset=True)
    if not campos:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nenhum campo informado para atualizacao")

    doc_ref.update(campos)
    
    doc_atualizado = doc_ref.get()
    resultado = doc_atualizado.to_dict()
    resultado["id"] = cliente_id
    return resultado


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT,
                summary="Remove um cliente")
def remover(cliente_id: str):
    db = obter_db()
    doc_ref = db.collection("clientes").document(cliente_id)
    if not doc_ref.get().exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")
    
    doc_ref.delete()
    return None