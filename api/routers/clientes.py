"""Endpoints REST de CRUD de clientes."""

import sqlite3
from typing import List

from fastapi import APIRouter, HTTPException, status

from db import conectar
from schemas import ClienteCreate, ClienteOut, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_model=List[ClienteOut], summary="Lista todos os clientes")
def listar():
    with conectar() as c:
        linhas = c.execute(
            "SELECT * FROM clientes ORDER BY identificador"
        ).fetchall()
    return [dict(l) for l in linhas]


@router.get("/{cliente_id}", response_model=ClienteOut, summary="Busca um cliente pelo id")
def obter(cliente_id: int):
    with conectar() as c:
        linha = c.execute(
            "SELECT * FROM clientes WHERE id = ?", (cliente_id,)
        ).fetchone()
    if linha is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")
    return dict(linha)


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED,
             summary="Cadastra um cliente")
def criar(dados: ClienteCreate):
    try:
        with conectar() as c:
            cursor = c.execute(
                "INSERT INTO clientes (identificador, tariff_plan, observacao) VALUES (?, ?, ?)",
                (dados.identificador, dados.tariff_plan, dados.observacao),
            )
            novo_id = cursor.lastrowid
            linha = c.execute("SELECT * FROM clientes WHERE id = ?", (novo_id,)).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Ja existe um cliente com o identificador {dados.identificador}",
        )
    return dict(linha)


@router.put("/{cliente_id}", response_model=ClienteOut, summary="Atualiza um cliente")
def atualizar(cliente_id: int, dados: ClienteUpdate):
    campos = dados.model_dump(exclude_unset=True)
    if not campos:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nenhum campo informado para atualizacao")

    with conectar() as c:
        existe = c.execute("SELECT 1 FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        if existe is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")

        atribuicoes = ", ".join(f"{k} = ?" for k in campos)
        valores = list(campos.values()) + [cliente_id]
        c.execute(
            f"UPDATE clientes SET {atribuicoes}, atualizado_em = datetime('now') WHERE id = ?",
            valores,
        )
        linha = c.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    return dict(linha)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Remove um cliente")
def remover(cliente_id: int):
    with conectar() as c:
        cursor = c.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")
    return None
