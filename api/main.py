"""API do ChurnGuard.

Para rodar:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Documentacao interativa em http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import db
from routers import clientes, predict


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    db.iniciar()
    yield


app = FastAPI(
    title="ChurnGuard API",
    description="Servico de CRUD de clientes e avaliacao de risco de cancelamento.",
    version="0.1.0",
    lifespan=ciclo_de_vida,
)

# Liberado durante o desenvolvimento para o Expo alcancar a API.
# Restringir antes de hospedar, na Sprint 6.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clientes.router)
app.include_router(predict.router)


@app.get("/health", tags=["infra"], summary="Verifica se a API esta de pe")
def health():
    return {"status": "ok", "versao": app.version}
