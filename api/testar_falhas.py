r"""Teste das situacoes de falha da API, com relatorio de evidencia.

Complementa o `testar_api_publicada.py`. As falhas abaixo nao podem ser
provocadas no ambiente publicado sem derruba-lo, entao sao simuladas aqui, na
maquina local, contra o mesmo codigo que roda na hospedagem.

CENARIOS
    F1  modelo indisponivel com stub bloqueado (configuracao publicada):
        /predict responde 503 com mensagem clara e /health mostra o motivo
    F2  modelo indisponivel com stub liberado (desenvolvimento): responde,
        mas se identifica como stub-0.1, nunca como o modelo treinado
    F3  modelo devolvido a pasta: volta a responder pelo modelo treinado
        sem reiniciar o servico
    F4  banco indisponivel: rotas de clientes respondem 503 e a predicao,
        que nao depende do banco, continua funcionando
    F5  erro inesperado dentro do modelo: 500 com mensagem generica, sem
        expor detalhes internos
    F6  valor fora do dominio detectado pelo modelo: 422

Nenhum dado real e lido ou gravado: o banco e substituido durante o teste.

USO (PowerShell, dentro de api/ com o venv ativo)
    python testar_falhas.py

Grava docs/evidencias/teste_falhas_AAAA-MM-DD_HHMM.md
"""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

# A autenticacao e desligada SO dentro deste processo, para isolar as falhas
# de modelo e de banco. A autorizacao e testada no testar_api_publicada.py.
os.environ["CHURNGUARD_EXIGIR_AUTENTICACAO"] = "0"
os.environ["CHURNGUARD_PERMITIR_STUB"] = "0"

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))

from fastapi.testclient import TestClient  # noqa: E402

import db  # noqa: E402
import main  # noqa: E402
import modelo  # noqa: E402

# Silencia o log de cada requisicao e o traceback proposital do F5, que
# poluiriam a saida sem acrescentar informacao.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("churnguard.predict").setLevel(logging.CRITICAL)

CASOS = RAIZ / "ml" / "artefatos" / "casos_de_referencia.json"
PASTA_EVIDENCIAS = RAIZ / "docs" / "evidencias"

linhas: list[dict] = []


def anotar(codigo: str, cenario: str, esperado: str, obtido: str, passou: bool) -> None:
    linhas.append({"codigo": codigo, "cenario": cenario, "esperado": esperado,
                   "obtido": obtido, "passou": passou})
    print(f"  [{'ok  ' if passou else 'FALHOU'}] {codigo} {cenario}")
    if not passou:
        print(f"           esperado: {esperado}")
        print(f"           obtido  : {obtido}")


def resumo(resposta) -> str:
    texto = resposta.text.replace("\n", " ")
    return f"HTTP {resposta.status_code} {texto[:140]}{'...' if len(texto) > 140 else ''}"


def entrada() -> dict:
    return json.loads(CASOS.read_text(encoding="utf-8"))[0]["entrada"]


class _BancoFora:
    def collection(self, nome):
        raise db.ErroDePersistencia("falha simulada: Firestore inalcancavel")


def main_teste() -> int:
    cliente = TestClient(main.app, raise_server_exceptions=False)
    pasta_original = modelo.PASTA_ARTEFATOS
    prever_original = modelo.prever

    # Garante o ponto de partida: modelo real carregado.
    modelo.carregar(forcar=True)

    # --------------------------------------------------------------- F1
    print("\nF1 Modelo indisponivel, stub bloqueado")
    try:
        modelo.PASTA_ARTEFATOS = Path("/pasta/que/nao/existe")
        modelo._motor = None

        r = cliente.post("/predict", json=entrada())
        anotar("F1.1", "POST /predict sem modelo", "HTTP 503",
               resumo(r), r.status_code == 503)
        anotar("F1.2", "mensagem explica a suspensao", "texto 'nao esta disponivel'",
               resumo(r), "nao esta disponivel" in r.text)

        saude = cliente.get("/health").json()["modelo"]
        anotar("F1.3", "/health informa o motivo", "carregado=false com motivo",
               f"carregado={saude.get('carregado')} motivo={saude.get('motivo', '')[:80]}",
               saude.get("carregado") is False and bool(saude.get("motivo")))

        # ----------------------------------------------------------- F2
        print("\nF2 Modelo indisponivel, stub liberado")
        os.environ["CHURNGUARD_PERMITIR_STUB"] = "1"
        r = cliente.post("/predict", json=entrada())
        versao = r.json().get("modelo_versao") if r.status_code == 200 else None
        anotar("F2.1", "resposta se identifica como stub", "HTTP 200 modelo_versao=stub-0.1",
               f"HTTP {r.status_code} modelo_versao={versao}",
               r.status_code == 200 and versao == "stub-0.1")
        os.environ["CHURNGUARD_PERMITIR_STUB"] = "0"
    finally:
        modelo.PASTA_ARTEFATOS = pasta_original

    # --------------------------------------------------------------- F3
    print("\nF3 Modelo devolvido, sem reiniciar")
    r = cliente.post("/predict", json=entrada())
    versao = r.json().get("modelo_versao") if r.status_code == 200 else None
    anotar("F3.1", "volta a responder pelo modelo treinado",
           "HTTP 200 modelo_versao=rf-smotenc-1.0",
           f"HTTP {r.status_code} modelo_versao={versao}",
           r.status_code == 200 and versao == "rf-smotenc-1.0")

    # --------------------------------------------------------------- F4
    print("\nF4 Banco indisponivel")
    obter_original = db.obter_db
    try:
        db.obter_db = lambda: _BancoFora()
        r = cliente.get("/clientes")
        anotar("F4.1", "GET /clientes sem banco", "HTTP 503", resumo(r), r.status_code == 503)
        r = cliente.post("/clientes", json={"nome": "teste"})
        anotar("F4.2", "POST /clientes sem banco", "HTTP 503", resumo(r), r.status_code == 503)
        r = cliente.post("/predict", json=entrada())
        anotar("F4.3", "predicao continua sem banco", "HTTP 200", f"HTTP {r.status_code}",
               r.status_code == 200)
    finally:
        db.obter_db = obter_original

    # --------------------------------------------------------------- F5
    print("\nF5 Erro inesperado no modelo")
    try:
        def explode(_dados):
            raise RuntimeError("detalhe-interno-que-nao-pode-vazar")
        modelo.prever = explode
        r = cliente.post("/predict", json=entrada())
        anotar("F5.1", "erro inesperado vira 500", "HTTP 500", resumo(r), r.status_code == 500)
        anotar("F5.2", "detalhe interno nao aparece na resposta",
               "sem 'detalhe-interno'", resumo(r), "detalhe-interno" not in r.text)

        # ----------------------------------------------------------- F6
        print("\nF6 Valor fora do dominio detectado pelo modelo")

        def fora(_dados):
            raise modelo.ErroDeDominio("valor fora do dominio do treino (simulado)")
        modelo.prever = fora
        r = cliente.post("/predict", json=entrada())
        anotar("F6.1", "erro de dominio vira 422", "HTTP 422", resumo(r), r.status_code == 422)
    finally:
        modelo.prever = prever_original

    # O servico termina no estado em que comecou.
    r = cliente.post("/predict", json=entrada())
    anotar("F7.1", "estado restaurado ao final", "HTTP 200 modelo treinado",
           f"HTTP {r.status_code} {r.json().get('modelo_versao') if r.status_code == 200 else ''}",
           r.status_code == 200 and r.json().get("modelo_versao") == "rf-smotenc-1.0")

    return gravar()


def gravar() -> int:
    agora = datetime.now()
    PASTA_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    arquivo = PASTA_EVIDENCIAS / f"teste_falhas_{agora:%Y-%m-%d_%H%M}.md"
    falhas = [l for l in linhas if not l["passou"]]

    texto = [
        "# Teste das situações de falha",
        "",
        f"- Data: {agora:%d/%m/%Y %H:%M}",
        f"- Máquina: {platform.system()} {platform.release()}, Python {platform.python_version()}",
        "- Script: `api/testar_falhas.py` (execução local, banco simulado, nenhum dado real tocado)",
        "",
        f"**Resultado: {len(linhas) - len(falhas)} de {len(linhas)} verificações passaram.**",
        "",
        "| Código | Cenário | Esperado | Obtido | Resultado |",
        "|---|---|---|---|---|",
    ]
    for l in linhas:
        texto.append(f"| {l['codigo']} | {l['cenario']} | {l['esperado']} | "
                     f"{l['obtido'].replace('|', '/')} | {'passou' if l['passou'] else '**FALHOU**'} |")
    texto.append("")
    arquivo.write_text("\n".join(texto), encoding="utf-8")

    print()
    print(f"{len(linhas) - len(falhas)} de {len(linhas)} verificacoes passaram.")
    print(f"Relatorio: {arquivo}")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main_teste())