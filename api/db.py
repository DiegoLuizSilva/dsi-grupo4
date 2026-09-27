"""Persistencia da API em Firestore (Firebase Admin).

A credencial e resolvida em tres tentativas, na ordem:

1. `FIREBASE_CREDENCIAL_JSON` — o conteudo do JSON da conta de servico, inteiro,
   em uma variavel de ambiente. E o formato aceito pelos servicos de
   hospedagem, que nao permitem enviar arquivo junto com o codigo.
2. `FIREBASE_CREDENCIAL_ARQUIVO` — caminho de um arquivo de credencial. Em
   desenvolvimento, o padrao continua sendo `api/serviceAccountKey.json`.
3. Credencial padrao do ambiente (`GOOGLE_APPLICATION_CREDENTIALS` ou a
   identidade da propria infraestrutura, quando existir).

A inicializacao e preguicosa, feita na primeira consulta e nao no import.
Antes, um `serviceAccountKey.json` ausente impedia o modulo de ser importado,
e com isso a API inteira deixava de subir: nem `/health` respondia e nem a
documentacao abria. Adiar a inicializacao permite que o servico suba, informe
o problema no `/health` e falhe apenas nas rotas que de fato usam o banco.

Nenhuma credencial e versionada. Ver `.env.example`.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

logger = logging.getLogger("churnguard.db")

CAMINHO_PADRAO = Path(__file__).resolve().parent / "serviceAccountKey.json"

_cliente = None
_falha: str | None = None
_trava = threading.Lock()


class ErroDePersistencia(RuntimeError):
    """Nao foi possivel inicializar o acesso ao Firestore."""


def _credencial():
    """Resolve a credencial conforme a ordem documentada acima."""
    from firebase_admin import credentials

    bruto = os.getenv("FIREBASE_CREDENCIAL_JSON")
    if bruto:
        try:
            return credentials.Certificate(json.loads(bruto)), "FIREBASE_CREDENCIAL_JSON"
        except (json.JSONDecodeError, ValueError) as erro:
            raise ErroDePersistencia(
                "FIREBASE_CREDENCIAL_JSON esta definida mas nao contem um JSON "
                f"de conta de servico valido: {erro}"
            ) from erro

    caminho = Path(os.getenv("FIREBASE_CREDENCIAL_ARQUIVO", CAMINHO_PADRAO))
    if caminho.exists():
        return credentials.Certificate(str(caminho)), str(caminho)

    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return credentials.ApplicationDefault(), "GOOGLE_APPLICATION_CREDENTIALS"

    raise ErroDePersistencia(
        "Nenhuma credencial do Firebase encontrada. Definir "
        "FIREBASE_CREDENCIAL_JSON (hospedagem) ou colocar o arquivo em "
        f"{caminho} (desenvolvimento). Ver api/.env.example."
    )


def iniciar() -> None:
    """Inicializa o Firebase Admin. Chamada no ciclo de vida da aplicacao.

    Nao levanta excecao: registra a falha para que o servico continue de pe e
    o problema apareca no `/health`. As rotas que precisam do banco falham
    individualmente, com mensagem propria.
    """
    global _cliente, _falha

    with _trava:
        if _cliente is not None:
            return

        try:
            import firebase_admin
            from firebase_admin import firestore

            if not firebase_admin._apps:
                credencial, origem = _credencial()
                firebase_admin.initialize_app(credencial)
                logger.info("Firebase inicializado a partir de %s.", origem)

            _cliente = firestore.client()
            _falha = None
        except Exception as erro:
            _falha = str(erro)
            logger.error("Firestore indisponivel: %s", erro)


def obter_db():
    """Cliente do Firestore. Levanta ErroDePersistencia se indisponivel."""
    if _cliente is None:
        iniciar()
    if _cliente is None:
        raise ErroDePersistencia(_falha or "Firestore nao inicializado.")
    return _cliente


def situacao() -> dict:
    """Resumo para o endpoint /health."""
    if _cliente is not None:
        return {"conectado": True}
    return {"conectado": False, "motivo": _falha or "ainda nao inicializado"}
