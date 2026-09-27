"""API do ChurnGuard.

Para rodar em desenvolvimento:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Documentacao interativa em http://localhost:8000/docs

Configuracao por variaveis de ambiente, descrita em `.env.example`:

    FIREBASE_CREDENCIAL_JSON          credencial da conta de servico (hospedagem)
    FIREBASE_CREDENCIAL_ARQUIVO       caminho da credencial (desenvolvimento)
    CHURNGUARD_ARTEFATOS              pasta do pacote do modelo
    CHURNGUARD_PERMITIR_STUB          0 no ambiente publicado
    CHURNGUARD_EXIGIR_AUTENTICACAO    1 no ambiente publicado
    CHURNGUARD_ORIGENS                origens permitidas no CORS
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import db
from routers import clientes, predict

logging.basicConfig(
    level=os.getenv("CHURNGUARD_LOG", "INFO").upper(),
    format="%(asctime)s  %(levelname)-8s %(name)s  %(message)s",
)

logger = logging.getLogger("churnguard")


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # A inicializacao nao interrompe a subida do servico: se o banco ou o
    # modelo estiverem indisponiveis, a API sobe e informa o estado no
    # /health, em vez de falhar sem deixar rastro.
    db.iniciar()

    try:
        import modelo
        modelo.carregar()
    except Exception as erro:
        logger.warning("Modelo nao carregado na inicializacao: %s", erro)

    yield


app = FastAPI(
    title="ChurnGuard API",
    description="Servico de CRUD de clientes e avaliacao de risco de cancelamento.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)


def _origens_permitidas() -> list[str]:
    """Origens aceitas pelo CORS.

    O aplicativo Expo em dispositivo nao envia cabecalho Origin, entao o CORS
    nao o afeta. A restricao existe para o navegador: com `*` qualquer pagina
    web poderia chamar a API usando o token da pessoa. Definir
    CHURNGUARD_ORIGENS na hospedagem, separando por virgula.
    """
    bruto = os.getenv("CHURNGUARD_ORIGENS", "").strip()
    if bruto:
        return [origem.strip() for origem in bruto.split(",") if origem.strip()]

    # Padrao de desenvolvimento: o que o Expo usa na maquina local.
    return [
        "http://localhost:8081",
        "http://localhost:19006",
        "http://127.0.0.1:8081",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_origens_permitidas(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(clientes.router)
app.include_router(predict.router)


@app.get("/health", tags=["infra"], summary="Verifica se a API esta de pe")
def health():
    """Estado do servico, do banco e do motor de predicao.

    O bloco `modelo` existe para que nunca seja preciso adivinhar se a API
    esta respondendo pelo modelo treinado ou pelo stub de desenvolvimento.
    Conferir este endpoint antes de qualquer demonstracao ou de coletar
    qualquer resultado para o artigo.
    """
    import modelo
    import seguranca

    return {
        "status": "ok",
        "versao": app.version,
        "modelo": modelo.situacao(),
        "banco": db.situacao(),
        "autenticacao_exigida": os.getenv("CHURNGUARD_EXIGIR_AUTENTICACAO", "1")
        not in ("0", "false", "False"),
        "stub_permitido": os.getenv("CHURNGUARD_PERMITIR_STUB", "1")
        not in ("0", "false", "False"),
    }
