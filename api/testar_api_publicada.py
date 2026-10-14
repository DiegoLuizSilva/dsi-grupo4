r"""Teste da API PUBLICADA, com relatorio de evidencia.

O `testar_predicao.py` prova o modelo e as rotas na maquina de quem roda. Este
script prova a mesma coisa no endereco publicado, que e o que o aplicativo e a
banca usam. Ele nao altera nada no banco: so faz leituras e predicoes.

Cada execucao grava um relatorio em `docs/evidencias/`, com data, endereco,
versao do modelo, tempo de cada resposta e o resultado de cada cenario. Esse
arquivo e a evidencia da Sprint 7 e deve ser commitado.

CENARIOS
    T01  /health responde, modelo real carregado, banco conectado,
         autenticacao exigida e stub desligado
    T02  rotas de dados e de predicao recusam requisicao sem token (401)
    T03  token invalido e cabecalho malformado sao recusados (401)
    T04  conta de demonstracao entra e le a carteira (200)
    T05  casos de referencia: mesma faixa e mesma probabilidade do modelo
         treinado, com tres fatores explicativos
    T06  entradas invalidas sao recusadas com 422, sem derrubar o servico
    T07  a mesma entrada devolve o mesmo resultado (determinismo)
    T08  o servico continua de pe depois das entradas invalidas

Modelo indisponivel e falha de banco NAO sao provocados aqui, porque isso
exigiria derrubar o ambiente publicado. Esses casos sao simulados
localmente pelo `testar_falhas.py`.

USO (PowerShell, dentro de api/ com o venv ativo)
    python testar_api_publicada.py --url https://SEU-SERVICO.onrender.com --email demo.gestor1@example.com

    A senha e pedida na hora e nao aparece na tela nem no historico.
    A chave do Firebase e lida de app/.env (EXPO_PUBLIC_FIREBASE_API_KEY).
    Para informar outra: --chave SUA_CHAVE

    --sem-login   roda so os cenarios que nao precisam de conta (T01 a T03)
"""

from __future__ import annotations

import argparse
import getpass
import json
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import httpx
except ImportError:  # pragma: no cover
    print("Falta o httpx. Rode: pip install -r requirements.txt")
    raise SystemExit(1)

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
CASOS = RAIZ / "ml" / "artefatos" / "casos_de_referencia.json"
ENV_DO_APP = RAIZ / "app" / ".env"
PASTA_EVIDENCIAS = RAIZ / "docs" / "evidencias"

TOLERANCIA = 0.001          # diferenca aceita na probabilidade
ESPERA_PRIMEIRA = 120.0     # o plano gratuito pode levar ~1 min para acordar
ESPERA_NORMAL = 30.0

LOGIN_FIREBASE = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={chave}"
)


# ------------------------------------------------------------------- registro

class Registro:
    def __init__(self) -> None:
        self.linhas: list[dict] = []

    def anotar(self, codigo: str, cenario: str, esperado: str, obtido: str,
               passou: bool, tempo_ms: float | None = None) -> None:
        self.linhas.append({
            "codigo": codigo, "cenario": cenario, "esperado": esperado,
            "obtido": obtido, "passou": passou, "tempo_ms": tempo_ms,
        })
        marca = "ok  " if passou else "FALHOU"
        tempo = f"  ({tempo_ms:.0f} ms)" if tempo_ms is not None else ""
        print(f"  [{marca}] {codigo} {cenario}{tempo}")
        if not passou:
            print(f"           esperado: {esperado}")
            print(f"           obtido  : {obtido}")

    @property
    def falhas(self) -> list[dict]:
        return [l for l in self.linhas if not l["passou"]]


def requisitar(cliente: httpx.Client, metodo: str, caminho: str,
               timeout: float = ESPERA_NORMAL, **kwargs):
    """Faz a chamada e devolve (resposta ou None, ms, erro ou None)."""
    inicio = time.perf_counter()
    try:
        resposta = cliente.request(metodo, caminho, timeout=timeout, **kwargs)
        return resposta, (time.perf_counter() - inicio) * 1000, None
    except httpx.HTTPError as erro:
        return None, (time.perf_counter() - inicio) * 1000, f"{type(erro).__name__}: {erro}"


def descrever(resposta, erro) -> str:
    if erro:
        return erro
    corpo = resposta.text.replace("\n", " ")
    if len(corpo) > 160:
        corpo = corpo[:160] + "..."
    return f"HTTP {resposta.status_code} {corpo}"


# ---------------------------------------------------------------- utilitarios

def ler_chave_do_app() -> str | None:
    if not ENV_DO_APP.exists():
        return None
    for linha in ENV_DO_APP.read_text(encoding="utf-8-sig").splitlines():
        linha = linha.strip()
        if linha.startswith("EXPO_PUBLIC_FIREBASE_API_KEY="):
            valor = linha.split("=", 1)[1].strip().strip('"').strip("'")
            if valor and valor != "cole_a_chave_aqui":
                return valor
    return None


def entrar(chave: str, email: str, senha: str) -> str:
    """Login pela API REST do Firebase; devolve o token de identidade."""
    resposta = httpx.post(
        LOGIN_FIREBASE.format(chave=chave),
        json={"email": email, "password": senha, "returnSecureToken": True},
        timeout=ESPERA_NORMAL,
    )
    if resposta.status_code != 200:
        try:
            motivo = resposta.json()["error"]["message"]
        except Exception:
            motivo = resposta.text[:200]
        raise RuntimeError(f"Login recusado pelo Firebase: {motivo}")
    return resposta.json()["idToken"]


def entrada_valida() -> dict:
    casos = json.loads(CASOS.read_text(encoding="utf-8"))
    return dict(casos[0]["entrada"])


# ------------------------------------------------------------------ cenarios

def t01_saude(cliente: httpx.Client, reg: Registro) -> dict:
    print("\nT01 Estado do servico")
    resposta, ms, erro = requisitar(cliente, "GET", "/health", timeout=ESPERA_PRIMEIRA)

    ok = resposta is not None and resposta.status_code == 200
    reg.anotar("T01.1", "/health responde (inclui o tempo para acordar)",
               "HTTP 200", "HTTP 200" if ok else descrever(resposta, erro),
               ok, ms)

    if resposta is None or resposta.status_code != 200:
        return {}

    saude = resposta.json()
    modelo = saude.get("modelo") or {}
    banco = saude.get("banco") or {}

    reg.anotar("T01.2", "modelo treinado carregado",
               "carregado=true", f"carregado={modelo.get('carregado')} "
               f"versao={modelo.get('modelo_versao')} motivo={modelo.get('motivo', '-')}",
               modelo.get("carregado") is True)
    reg.anotar("T01.3", "explicacao local (SHAP) ativa",
               "explicacao=local", f"explicacao={modelo.get('explicacao')}",
               modelo.get("explicacao") == "local")
    reg.anotar("T01.4", "banco conectado",
               "conectado=true", f"conectado={banco.get('conectado')} motivo={banco.get('motivo', '-')}",
               banco.get("conectado") is True)
    reg.anotar("T01.5", "autenticacao exigida no ambiente publicado",
               "autenticacao_exigida=true", f"autenticacao_exigida={saude.get('autenticacao_exigida')}",
               saude.get("autenticacao_exigida") is True)
    reg.anotar("T01.6", "stub de desenvolvimento desligado",
               "stub_permitido=false", f"stub_permitido={saude.get('stub_permitido')}",
               saude.get("stub_permitido") is False)
    return saude


def t02_sem_token(cliente: httpx.Client, reg: Registro) -> None:
    print("\nT02 Requisicoes sem token")
    for codigo, metodo, caminho, corpo in (
        ("T02.1", "GET", "/clientes", None),
        ("T02.2", "POST", "/predict", entrada_valida()),
        ("T02.3", "POST", "/clientes", {"nome": "nao deveria gravar"}),
    ):
        resposta, ms, erro = requisitar(cliente, metodo, caminho, json=corpo)
        reg.anotar(codigo, f"{metodo} {caminho} sem token",
                   "HTTP 401", descrever(resposta, erro),
                   resposta is not None and resposta.status_code == 401, ms)


def t03_token_invalido(cliente: httpx.Client, reg: Registro) -> None:
    print("\nT03 Token invalido ou malformado")
    for codigo, descricao, cabecalho in (
        ("T03.1", "token inventado", "Bearer token-inventado-123"),
        ("T03.2", "token com formato de JWT mas assinatura falsa",
         "Bearer eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ4In0.YXNzaW5hdHVyYQ"),
        ("T03.3", "cabecalho sem o prefixo Bearer", "token-sem-prefixo"),
    ):
        resposta, ms, erro = requisitar(
            cliente, "POST", "/predict", json=entrada_valida(),
            headers={"Authorization": cabecalho},
        )
        reg.anotar(codigo, descricao, "HTTP 401", descrever(resposta, erro),
                   resposta is not None and resposta.status_code == 401, ms)


def t04_leitura(cliente: httpx.Client, reg: Registro, cabecalho: dict) -> None:
    print("\nT04 Conta autenticada le a carteira")
    resposta, ms, erro = requisitar(cliente, "GET", "/clientes", headers=cabecalho)
    ok = resposta is not None and resposta.status_code == 200 and isinstance(resposta.json(), list)
    obtido = (f"HTTP 200, {len(resposta.json())} clientes" if ok else descrever(resposta, erro))
    reg.anotar("T04.1", "GET /clientes com token valido", "HTTP 200 com lista", obtido, ok, ms)


def t05_referencias(cliente: httpx.Client, reg: Registro, cabecalho: dict) -> None:
    print("\nT05 Casos de referencia contra o modelo publicado")
    casos = json.loads(CASOS.read_text(encoding="utf-8"))

    for i, caso in enumerate(casos, start=1):
        codigo = f"T05.{i}"
        resposta, ms, erro = requisitar(cliente, "POST", "/predict",
                                        json=caso["entrada"], headers=cabecalho)
        if resposta is None or resposta.status_code != 200:
            reg.anotar(codigo, caso["descricao"], "HTTP 200", descrever(resposta, erro), False, ms)
            continue

        corpo = resposta.json()
        prob = corpo.get("probabilidade", -1)
        fatores = corpo.get("fatores") or []
        diferenca = abs(prob - caso["probabilidade_esperada"])

        ok = (corpo.get("faixa") == caso["faixa_esperada"]
              and diferenca <= TOLERANCIA
              and len(fatores) == 3)

        reg.anotar(
            codigo, caso["descricao"],
            f"faixa={caso['faixa_esperada']} p={caso['probabilidade_esperada']:.4f} 3 fatores",
            f"faixa={corpo.get('faixa')} p={prob:.4f} {len(fatores)} fatores "
            f"({', '.join(f['campo'] for f in fatores)})",
            ok, ms,
        )


def t06_invalidas(cliente: httpx.Client, reg: Registro, cabecalho: dict) -> None:
    print("\nT06 Entradas invalidas")
    base = entrada_valida()

    def com(**mudancas):
        e = dict(base)
        e.update(mudancas)
        return e

    sem_campo = dict(base)
    sem_campo.pop("complains")

    variantes = [
        ("T06.1", "campo obrigatorio ausente (complains)", {"json": sem_campo}),
        ("T06.2", "faixa de cobranca acima de 10", {"json": com(charge_amount=11)}),
        ("T06.3", "reclamacao com valor 2", {"json": com(complains=2)}),
        ("T06.4", "idade negativa", {"json": com(age=-5)}),
        ("T06.5", "plano tarifario 3", {"json": com(tariff_plan=3)}),
        ("T06.6", "texto em campo numerico", {"json": com(seconds_of_use="muito")}),
        ("T06.7", "corpo vazio", {"json": {}}),
        ("T06.8", "JSON quebrado", {"content": b"{call_failure: 3",
                                    "headers_extra": {"Content-Type": "application/json"}}),
    ]

    for codigo, descricao, opcoes in variantes:
        headers = dict(cabecalho)
        headers.update(opcoes.pop("headers_extra", {}))
        resposta, ms, erro = requisitar(cliente, "POST", "/predict", headers=headers, **opcoes)
        reg.anotar(codigo, descricao, "HTTP 422", descrever(resposta, erro),
                   resposta is not None and resposta.status_code == 422, ms)


def t07_determinismo(cliente: httpx.Client, reg: Registro, cabecalho: dict) -> None:
    print("\nT07 Determinismo")
    entrada = entrada_valida()
    resultados = []
    for _ in range(3):
        resposta, _, _ = requisitar(cliente, "POST", "/predict", json=entrada, headers=cabecalho)
        if resposta is not None and resposta.status_code == 200:
            corpo = resposta.json()
            resultados.append((corpo["probabilidade"], corpo["faixa"],
                               tuple(f["campo"] for f in corpo["fatores"])))
    ok = len(resultados) == 3 and len(set(resultados)) == 1
    reg.anotar("T07.1", "tres chamadas iguais, mesmo resultado",
               "3 respostas identicas", f"{len(set(resultados))} resultado(s) distinto(s) em {len(resultados)}",
               ok)


def t08_continua_de_pe(cliente: httpx.Client, reg: Registro) -> None:
    print("\nT08 Servico continua de pe")
    resposta, ms, erro = requisitar(cliente, "GET", "/health")
    ok = resposta is not None and resposta.status_code == 200 and resposta.json()["modelo"]["carregado"]
    reg.anotar("T08.1", "/health depois das entradas invalidas", "HTTP 200, modelo carregado",
               descrever(resposta, erro) if not ok else "HTTP 200, modelo carregado", ok, ms)


# ------------------------------------------------------------------ relatorio

def gravar_relatorio(reg: Registro, url: str, saude: dict, email: str | None,
                     inicio: datetime) -> Path:
    PASTA_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    arquivo = PASTA_EVIDENCIAS / f"teste_api_publicada_{inicio:%Y-%m-%d_%H%M}.md"

    modelo = (saude or {}).get("modelo") or {}
    total = len(reg.linhas)
    passaram = total - len(reg.falhas)
    tempos = [l["tempo_ms"] for l in reg.linhas
              if l["tempo_ms"] is not None and not l["codigo"].startswith("T01.1")]
    tempos.sort()
    mediana = tempos[len(tempos) // 2] if tempos else None

    linhas = [
        "# Teste da API publicada",
        "",
        f"- Data: {inicio:%d/%m/%Y %H:%M}",
        f"- Endereço: `{url}`",
        f"- Modelo: `{modelo.get('modelo_versao', '?')}` ({modelo.get('algoritmo', '?')}), "
        f"explicação `{modelo.get('explicacao', '?')}`",
        f"- Conta usada: `{email or 'nenhuma (--sem-login)'}`",
        f"- Máquina que executou: {platform.system()} {platform.release()}, Python {platform.python_version()}",
        f"- Script: `api/testar_api_publicada.py`",
        "",
        f"**Resultado: {passaram} de {total} verificações passaram.**",
        "",
    ]
    if mediana is not None:
        primeira = next((l["tempo_ms"] for l in reg.linhas if l["codigo"] == "T01.1"), None)
        if primeira is not None:
            linhas.append(f"Primeira resposta (inclui o serviço acordar): {primeira/1000:.1f} s. "
                          f"Mediana das demais: {mediana:.0f} ms.")
            linhas.append("")

    linhas += [
        "| Código | Cenário | Esperado | Obtido | Tempo | Resultado |",
        "|---|---|---|---|---|---|",
    ]
    for l in reg.linhas:
        tempo = f"{l['tempo_ms']:.0f} ms" if l["tempo_ms"] is not None else "-"
        obtido = l["obtido"].replace("|", "/")
        linhas.append(f"| {l['codigo']} | {l['cenario']} | {l['esperado']} | {obtido} | "
                      f"{tempo} | {'passou' if l['passou'] else '**FALHOU**'} |")

    linhas += [
        "",
        "## Fora do escopo deste teste",
        "",
        "Modelo indisponível e banco indisponível não são provocados no ambiente publicado, "
        "porque isso exigiria derrubá-lo. Ambos são verificados localmente por "
        "`api/testar_falhas.py` e registrados em `docs/REGISTRO_DE_TESTES.md`.",
        "",
    ]

    if reg.falhas:
        linhas += [
            "## Falhas desta execução",
            "",
            "Registrar cada uma em `docs/REGISTRO_DE_TESTES.md` "
            "(falha, reprodução, correção, reteste) e rodar o script de novo.",
            "",
        ]
        for l in reg.falhas:
            linhas.append(f"- **{l['codigo']}** {l['cenario']}: esperado `{l['esperado']}`, "
                          f"obtido `{l['obtido']}`")
        linhas.append("")

    arquivo.write_text("\n".join(linhas), encoding="utf-8")
    return arquivo


# ----------------------------------------------------------------------- main

def main() -> int:
    parser = argparse.ArgumentParser(description="Testa a API publicada do ChurnGuard.")
    parser.add_argument("--url", required=True, help="endereco publicado, sem barra no fim")
    parser.add_argument("--email", help="e-mail de uma conta de demonstracao")
    parser.add_argument("--chave", help="apiKey do Firebase (padrao: lida de app/.env)")
    parser.add_argument("--sem-login", action="store_true", help="roda so T01 a T03")
    args = parser.parse_args()

    url = args.url.rstrip("/")
    if "SEU-" in url.upper():
        print("Troque SEU-SERVICO pelo endereco real do Render.")
        return 1

    if not CASOS.exists():
        print(f"Nao encontrei {CASOS}. Rode a partir do repositorio completo.")
        return 1

    token = None
    if not args.sem_login:
        if not args.email:
            print("Informe --email de uma conta de demonstracao, ou use --sem-login.")
            return 1
        chave = args.chave or ler_chave_do_app()
        if not chave:
            print("Nao achei EXPO_PUBLIC_FIREBASE_API_KEY em app/.env. Use --chave.")
            return 1
        senha = getpass.getpass(f"Senha de {args.email}: ")
        try:
            token = entrar(chave, args.email, senha)
        except Exception as erro:
            print(erro)
            return 1
        print("Login ok.")

    inicio = datetime.now()
    reg = Registro()
    print(f"Testando {url}")
    print("(a primeira chamada pode levar ate 1 minuto se o servico estiver dormindo)")

    with httpx.Client(base_url=url) as cliente:
        saude = t01_saude(cliente, reg)
        if not saude:
            print("\nO servico nao respondeu. Nada mais a testar.")
        else:
            t02_sem_token(cliente, reg)
            t03_token_invalido(cliente, reg)
            if token:
                cabecalho = {"Authorization": f"Bearer {token}"}
                t04_leitura(cliente, reg, cabecalho)
                t05_referencias(cliente, reg, cabecalho)
                t06_invalidas(cliente, reg, cabecalho)
                t07_determinismo(cliente, reg, cabecalho)
                t08_continua_de_pe(cliente, reg)

    arquivo = gravar_relatorio(reg, url, saude, args.email if token else None, inicio)

    total = len(reg.linhas)
    print()
    print(f"{total - len(reg.falhas)} de {total} verificacoes passaram.")
    print(f"Relatorio: {arquivo}")
    if reg.falhas:
        print("Ha falhas. Registre em docs/REGISTRO_DE_TESTES.md antes de corrigir.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())