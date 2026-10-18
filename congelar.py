r"""Congelamento da versao de entrega do ChurnGuard (Sprint 9).

Confere os dois repositorios, roda os testes locais, registra em
docs/PACOTE_FINAL.md quais revisoes de codigo, modelo e artigo compoem a
entrega e, por ultimo, cria a tag no dsi-grupo4 (o pisi3-grupo4 congela em 23/10).

Nao altera codigo. So escreve docs/PACOTE_FINAL.md, e pergunta antes do
commit e antes das tags. Se encontrar qualquer problema, para sem gravar nada.

USO (PowerShell, na raiz do dsi-grupo4)
    api\venv\Scripts\python.exe congelar.py --artigo "Artigo - Grupo 4_5.pdf"

    --artigo  nome do arquivo final do artigo, como foi entregue
    --pisi    clone do pisi3-grupo4 (padrao: ..\pisi3-grupo4, ao lado deste)
    --tag     nome da tag (padrao: v1.0-apresentacao)
    --conferir  so confere e mostra o resumo, sem gravar nem perguntar nada
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DSI = Path(__file__).resolve().parent
PYTHON_API = DSI / "api" / "venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")

problemas: list[str] = []


def titulo(texto: str) -> None:
    print(f"\n== {texto}")


def ok(texto: str) -> None:
    print(f"  ok  {texto}")


def falha(texto: str) -> None:
    print(f"  !!  {texto}")
    problemas.append(texto)


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return (r.stdout or "").strip()


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def perguntar(texto: str) -> bool:
    return input(f"{texto} (s/N) ").strip().lower() == "s"


# --------------------------------------------------------------- verificacoes

def conferir_repos(repos: dict[str, Path]) -> None:
    titulo("Repositorios")
    for nome, repo in repos.items():
        if not (repo / ".git").exists():
            falha(f"{nome} nao encontrado em {repo} (use --pisi)")
            continue
        git(repo, "fetch", "--quiet", "origin")
        local, remoto = git(repo, "rev-parse", "HEAD"), git(repo, "rev-parse", "@{u}")
        if not remoto:
            falha(f"{nome}: branch sem ligacao com o GitHub")
        elif local != remoto:
            falha(f"{nome} diferente do GitHub. Rode: git -C {repo} pull --rebase --autostash")
        else:
            ok(f"{nome} igual ao GitHub ({local[:7]})")

        sujos = git(repo, "status", "--porcelain", "--untracked-files=no")
        if sujos:
            print(f"  ..  {nome} tem alteracoes locais fora de commit; elas NAO entram na entrega:")
            for linha in sujos.splitlines():
                print(f"        {linha}")


def conferir_credenciais(repos: dict[str, Path]) -> None:
    titulo("Credenciais versionadas")
    for nome, repo in repos.items():
        if not (repo / ".git").exists():
            continue
        versionados = [a for a in git(repo, "ls-files").splitlines()
                       if "serviceAccount" in a or a.split("/")[-1] == ".env"]
        if versionados:
            falha(f"{nome} versiona: {', '.join(versionados)}")
        else:
            ok(f"{nome} sem .env nem serviceAccountKey versionados")

        # O texto procurado e montado em duas partes para este proprio arquivo
        # nao conter a frase e nao ser apontado como chave privada.
        marcador = "BEGIN " + "PRIVATE KEY"
        chaves = [a for a in git(repo, "grep", "-l", marcador).splitlines()
                  if a and not a.endswith(".env.example")]
        if chaves:
            falha(f"{nome} tem chave privada em: {', '.join(chaves)}")
        else:
            ok(f"{nome} sem chave privada no codigo")

        if git(repo, "log", "--all", "--oneline", "--",
               "api/serviceAccountKey.json", "serviceAccountKey.json"):
            falha(f"{nome} ja teve serviceAccountKey.json em algum commit")
        else:
            ok(f"{nome} sem serviceAccountKey.json no historico")


def conferir_modelo(pisi: Path) -> dict:
    titulo("Modelo")
    info = {"versao": "?", "sha": "?"}
    modelo = DSI / "ml" / "artefatos" / "modelo.joblib"
    meta = DSI / "ml" / "artefatos" / "metadados.json"

    if modelo.exists():
        info["sha"] = sha256(modelo)
        ok(f"modelo.joblib sha256 {info['sha'][:12]}...")
    else:
        falha("ml/artefatos/modelo.joblib nao encontrado")

    if meta.exists():
        info["versao"] = json.loads(meta.read_text(encoding="utf-8")).get("modelo_versao", "?")
        ok(f"versao declarada: {info['versao']}")
    else:
        falha("ml/artefatos/metadados.json nao encontrado")

    original = pisi / "models" / "modelo_final.joblib"
    if original.exists() and modelo.exists():
        if sha256(original) == info["sha"]:
            ok("o modelo da API e o mesmo arquivo de pisi3-grupo4/models/modelo_final.joblib")
        else:
            falha("o modelo da API e diferente de pisi3-grupo4/models/modelo_final.joblib")
    return info


def rodar_testes() -> dict:
    titulo("Testes locais")
    resultados = {}
    if not PYTHON_API.exists():
        falha(f"venv da API nao encontrado em {PYTHON_API}")
        return resultados
    for teste in ("testar_predicao.py", "testar_falhas.py"):
        print(f"  ..  rodando {teste}")
        r = subprocess.run([str(PYTHON_API), teste], cwd=DSI / "api", capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        linhas = [l.strip("= ").strip() for l in (r.stdout or "").splitlines()
                  if "verificacoes passaram" in l]
        resumo = linhas[-1] if linhas else "sem resumo na saida"
        resultados[teste] = resumo
        (ok if r.returncode == 0 else falha)(f"{teste}: {resumo}")
    return resultados


# -------------------------------------------------------------------- registro

def montar_registro(args, info: dict, resultados: dict, publicada: str, render: str,
                    pisi: Path) -> str:
    agora = datetime.now()
    dsi_c, dsi_m = git(DSI, "rev-parse", "HEAD"), git(DSI, "log", "-1", "--format=%s")
    pisi_c, pisi_m = git(pisi, "rev-parse", "HEAD"), git(pisi, "log", "-1", "--format=%s")
    return f"""# Pacote final da entrega

Versão congelada em {agora:%d/%m/%Y %H:%M} para a apresentação de 21/10/2026. A partir daqui só entram correções de falhas que impeçam a demonstração; qualquer correção repete os testes afetados e atualiza este arquivo.

## Revisões

| Peça | Revisão |
|---|---|
| App e API (dsi-grupo4) | `{dsi_c[:7]}` — {dsi_m} |
| Análises e modelo (pisi3-grupo4) | `{pisi_c[:7]}` — {pisi_m} |
| API publicada | commit `{render}` em https://dsi-grupo4.onrender.com |
| Modelo | `{info['versao']}`, `ml/artefatos/modelo.joblib` |
| SHA-256 do modelo | `{info['sha']}` |
| Artigo | {args.artigo} |

A tag `{args.tag}` marca a versão entregue no dsi-grupo4. O pisi3-grupo4 segue com o painel até o congelamento de 23/10; a revisão acima é a que forneceu o modelo.

## Verificações no congelamento

| Verificação | Resultado |
|---|---|
| `testar_predicao.py` | {resultados.get('testar_predicao.py', '?')} |
| `testar_falhas.py` | {resultados.get('testar_falhas.py', '?')} |
| `testar_api_publicada.py` | {publicada} |
| Credenciais versionadas | nenhuma: `.env`, `serviceAccountKey.json` e chave privada conferidos nos dois repositórios e no histórico |
| Modelo da API igual ao do pisi3-grupo4 | sim, mesmo SHA-256 |
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artigo", required=True)
    parser.add_argument("--pisi", default=str(DSI.parent / "pisi3-grupo4"))
    parser.add_argument("--tag", default="v1.0-apresentacao")
    parser.add_argument("--conferir", action="store_true")
    args = parser.parse_args()

    pisi = Path(args.pisi).expanduser().resolve()
    repos = {"dsi-grupo4": DSI, "pisi3-grupo4": pisi}

    conferir_repos(repos)
    conferir_credenciais(repos)
    info = conferir_modelo(pisi)
    resultados = rodar_testes()

    titulo("Resumo")
    if problemas:
        print(f"  {len(problemas)} problema(s):")
        for p in problemas:
            print(f"   - {p}")
        print("\n  Resolva antes de congelar. Nada foi gravado.")
        return 1
    ok("nenhum problema encontrado")
    if args.conferir:
        return 0

    print("\n  O teste da API publicada pede senha; rode em outro terminal:")
    print("  cd api; .\\venv\\Scripts\\python.exe testar_api_publicada.py "
          "--url https://dsi-grupo4.onrender.com --email demo.gestor1@example.com")
    publicada = input("  Resultado (ex.: 30 de 30, teste_api_publicada_2026-10-19_1030.md): ").strip()
    render = input("  Commit no topo do servico no Render (7 caracteres): ").strip()

    texto = montar_registro(args, info, resultados, publicada, render, pisi)
    destino = DSI / "docs" / "PACOTE_FINAL.md"
    destino.write_text(texto, encoding="utf-8")
    print("\n" + texto)
    ok(f"gravado {destino}")

    if not perguntar("\nFazer commit e push de docs/PACOTE_FINAL.md no dsi-grupo4?"):
        print("Parado antes do commit. Confira o arquivo e rode de novo.")
        return 0
    subprocess.run(["git", "-C", str(DSI), "add", "docs/PACOTE_FINAL.md"], check=True)
    subprocess.run(["git", "-C", str(DSI), "commit", "-m", f"Congela a versao de entrega ({args.tag})"], check=True)
    subprocess.run(["git", "-C", str(DSI), "push"], check=True)

    if not perguntar(f"Criar a tag {args.tag} no dsi-grupo4 e enviar ao GitHub?"):
        print("Tag nao criada.")
        return 0
    subprocess.run(["git", "-C", str(DSI), "tag", "-a", args.tag, "-m",
                    "Versao apresentada em DSI em 21/10/2026"], check=True)
    subprocess.run(["git", "-C", str(DSI), "push", "origin", args.tag], check=True)
    ok(f"tag {args.tag} criada e enviada no dsi-grupo4")
    return 0


if __name__ == "__main__":
    sys.exit(main())