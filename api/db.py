"""Persistencia da API em SQLite.

Guarda os clientes cadastrados pelo lado do servidor. O aplicativo mantem
a sua propria base local em expo-sqlite para funcionar sem conexao; esta
base atende os endpoints REST de CRUD.
"""

import os
import sqlite3
from contextlib import contextmanager

CAMINHO_BANCO = os.getenv("CHURNGUARD_DB", os.path.join(os.path.dirname(__file__), "churnguard.db"))

ESQUEMA = """
CREATE TABLE IF NOT EXISTS clientes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    identificador  TEXT    NOT NULL UNIQUE,
    tariff_plan    INTEGER NOT NULL,
    observacao     TEXT,
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now')),
    atualizado_em  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


@contextmanager
def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexao
        conexao.commit()
    finally:
        conexao.close()


def iniciar():
    """Cria as tabelas se ainda nao existirem."""
    with conectar() as c:
        c.executescript(ESQUEMA)
