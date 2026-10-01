"""Autenticacao e autorizacao das rotas da API.

O aplicativo autentica a pessoa no Firebase Authentication e recebe um token
de identidade. Este modulo verifica esse token no servidor, com a chave publica
do Firebase, e devolve o `uid` da conta autenticada.

O que a autenticacao garante aqui e a fronteira entre dentro e fora: sem token
valido, nenhuma rota de dados ou de predicao responde. A carteira de clientes em
si e COMPARTILHADA entre as contas autenticadas -- decisao de dominio registrada
em `routers/clientes.py` e em `firestore.rules`. O `uid` e usado para registrar
autoria, nao para restringir acesso.

Por que a verificacao acontece no servidor: o aplicativo saber quem esta logado
nao protege nada, porque a API pode ser chamada sem passar pelo aplicativo. Uma
vez publicada, qualquer requisicao direta ao endereco do servico alcanca as
mesmas rotas. A unica barreira que vale e a do servidor.

Durante o desenvolvimento local, `CHURNGUARD_EXIGIR_AUTENTICACAO=0` libera as
rotas e usa uma conta ficticia, para que o CRUD continue testavel sem token.
Em ambiente publicado a variavel precisa ficar em `1`, que e o padrao.
"""

from __future__ import annotations

import logging
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger("churnguard.seguranca")

# `auto_error=False` para que a ausencia do cabecalho chegue aqui e produza
# uma mensagem propria, em vez do texto padrao da biblioteca.
_esquema = HTTPBearer(auto_error=False, description="Token de identidade do Firebase")

CONTA_DE_DESENVOLVIMENTO = "desenvolvimento-local"


def _exige_autenticacao() -> bool:
    return os.getenv("CHURNGUARD_EXIGIR_AUTENTICACAO", "1") not in ("0", "false", "False")


class Conta:
    """Identidade da conta autenticada."""

    def __init__(self, uid: str, email: str | None = None, simulada: bool = False):
        self.uid = uid
        self.email = email
        self.simulada = simulada

    def __repr__(self) -> str:  # pragma: no cover
        return f"Conta(uid={self.uid!r}, simulada={self.simulada})"


def conta_atual(
    credencial: HTTPAuthorizationCredentials | None = Depends(_esquema),
) -> Conta:
    """Dependencia que resolve a conta autenticada da requisicao.

    Usar nas rotas de dados:

        @router.get("")
        def listar(conta: Conta = Depends(conta_atual)):
            ...
    """
    if not _exige_autenticacao():
        logger.warning(
            "Autenticacao desativada; respondendo como %s. "
            "Nao usar esta configuracao em ambiente publicado.",
            CONTA_DE_DESENVOLVIMENTO,
        )
        return Conta(CONTA_DE_DESENVOLVIMENTO, simulada=True)

    if credencial is None or not credencial.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Envie o token de identidade no cabecalho Authorization: Bearer <token>.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        from firebase_admin import auth as firebase_auth
    except ImportError as erro:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servico de autenticacao indisponivel no servidor.",
        ) from erro

    # A verificacao do token depende do app do Firebase Admin inicializado.
    import db

    db.iniciar()

    try:
        conteudo = firebase_auth.verify_id_token(credencial.credentials)
    except firebase_auth.ExpiredIdTokenError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessao expirada. Entre novamente no aplicativo.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from erro
    except firebase_auth.RevokedIdTokenError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessao encerrada. Entre novamente no aplicativo.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from erro
    except Exception as erro:
        # Token malformado, assinatura invalida ou projeto diferente. A
        # mensagem para o cliente e generica de proposito; o detalhe fica no log.
        logger.warning("Token recusado: %s", erro)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacao invalido.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from erro

    uid = conteudo.get("uid") or conteudo.get("sub")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identificacao de conta.",
        )

    return Conta(uid=uid, email=conteudo.get("email"))


def registrar_autoria(documento: dict, conta: Conta, cliente_id: str) -> None:
    """Registra no log quem acessou um documento criado por outra conta.

    A carteira de clientes e COMPARTILHADA entre as contas autenticadas: a
    decisao esta documentada em `routers/clientes.py` e e a mesma declarada em
    `firestore.rules`. Portanto esta funcao nao bloqueia nada -- ela apenas
    deixa rastro, o que ajuda a investigar uma alteracao inesperada.

    Ate a versao anterior existia aqui um `conferir_dono` que devolvia 404
    quando a conta nao era a dona do registro. Ele foi retirado porque
    contradizia as regras do Firestore e, na pratica, nunca era exercitado: o
    aplicativo le os clientes direto do banco, pelo `dbService.ts`, sem passar
    por esta API. Manter os dois comportamentos divergentes fazia o sistema
    afirmar uma privacidade que nao possuia.
    """
    proprietario = documento.get("proprietario")

    if proprietario is not None and proprietario != conta.uid:
        logger.info(
            "Conta %s acessou o cliente %s, cadastrado por %s (carteira compartilhada).",
            conta.uid, cliente_id, proprietario,
        )