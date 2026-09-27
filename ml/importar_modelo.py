r"""Importa o modelo do repositorio pisi3-grupo4 para o formato que a API le.

O trabalho de classificacao vive em outro repositorio, com uma organizacao
propria: o pipeline em `models/modelo_final.joblib` e a descricao em
`reports/tabelas/model_metadata.json`. A API espera o pacote descrito em
`ml/CONTRATO_MODELO.md`. Este script faz a ponte, sem alterar nada do outro
repositorio.

O que ele produz em `ml/artefatos/`:

    modelo.joblib               copia do pipeline
    metadados.json              traduzido para o contrato da API
    casos_de_referencia.json    gerado a partir da base, com a probabilidade
                                obtida chamando o pipeline diretamente

Os casos de referencia sao o que prova que a API reproduz o modelo. Eles sao
gerados aqui, e nao a mao, porque a probabilidade precisa vir do pipeline e nao
de uma expectativa escrita por alguem.

USO
    cd ml
    python importar_modelo.py --pisi ..\..\pisi3-grupo4

    --pisi   caminho do clone do pisi3-grupo4
    --versao identificador do modelo (padrao: rf-smotenc-1.0)
"""

from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import shutil
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "artefatos"

# Decisoes tomadas em src/common.py do pisi3-grupo4, na funcao load_data.
# Replicadas aqui como DECLARACAO, para que a API as execute sem que nenhuma
# delas fique escrita no codigo da API.
IGNORADOS = ["age_group"]
MAPEAMENTOS = {
    "tariff_plan": {"1": 0, "2": 1},
    "status": {"1": 0, "2": 1},
}

CORTE_BAIXO = 0.30
CORTE_ALTO = 0.65


def versao_de(pacote: str) -> str:
    try:
        return md.version(pacote)
    except md.PackageNotFoundError:
        return "ausente"


def faixa(p: float) -> str:
    if p < CORTE_BAIXO:
        return "baixo"
    if p <= CORTE_ALTO:
        return "medio"
    return "alto"


def preparar(entrada: dict) -> dict:
    """Aplica o tratamento declarado: descarta e remapeia."""
    saida = {c: v for c, v in entrada.items() if c not in IGNORADOS}
    for campo, mapa in MAPEAMENTOS.items():
        saida[campo] = mapa[str(saida[campo])]
    return saida


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pisi", required=True, help="caminho do clone do pisi3-grupo4")
    parser.add_argument("--versao", default="rf-smotenc-1.0")
    args = parser.parse_args()

    # Progresso explicito: numa maquina fria, `import pandas` e o
    # `joblib.load` (que puxa scikit-learn e imbalanced-learn) levam varios
    # minutos na primeira execucao, com o antivirus inspecionando cada arquivo.
    # Sem estas linhas o script fica mudo o tempo todo e parece travado.
    def etapa(texto: str) -> None:
        print(texto, end="", flush=True)

    etapa("Carregando bibliotecas... ")
    import joblib
    import pandas as pd
    print("ok")

    pisi = Path(args.pisi).expanduser().resolve()

    origem_modelo = pisi / "models" / "modelo_final.joblib"
    origem_meta = pisi / "reports" / "tabelas" / "model_metadata.json"
    origem_csv = pisi / "data" / "raw" / "iranian_churn.csv"

    for caminho in (origem_modelo, origem_meta, origem_csv):
        if not caminho.exists():
            print(f"nao encontrei: {caminho}")
            print("Confira o --pisi. Ele aponta para a RAIZ do clone do pisi3-grupo4.")
            return 1

    meta_origem = json.loads(origem_meta.read_text(encoding="utf-8"))
    atributos = list(meta_origem["features"])

    etapa("Carregando o modelo (6 MB, pode demorar na primeira vez)... ")
    pipeline = joblib.load(origem_modelo)
    print("ok")

    if not hasattr(pipeline, "predict_proba"):
        print("O pipeline nao expoe predict_proba; as faixas dependem dele.")
        return 1

    esperado = getattr(pipeline, "n_features_in_", None)
    if esperado is not None and esperado != len(atributos):
        print(f"O modelo espera {esperado} atributos, o metadado lista {len(atributos)}.")
        return 1

    # ------------------------------------------------- ordem pos-transformacao

    # A ordem que o estimador ve pode diferir da ordem de entrada. O vetor SHAP
    # segue a ordem do estimador; declarar isso aqui evita que os fatores saiam
    # com o sinal invertido na tela.
    ordem_transformada = atributos
    passos = getattr(pipeline, "steps", None)

    if passos:
        etapas = [e for _, e in passos[:-1] if hasattr(e, "transform")]
        if etapas and hasattr(etapas[-1], "get_feature_names_out"):
            ordem_transformada = [str(n) for n in etapas[-1].get_feature_names_out()]

    reordenou = ordem_transformada != atributos

    # ------------------------------------------------------------- referencias

    etapa("Lendo a base... ")
    df = pd.read_csv(origem_csv)
    df.columns = df.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    print(f"ok ({len(df)} registros)")

    referencias: dict[str, float] = {}
    for campo in atributos:
        mediana = df[campo].median()
        referencias[campo] = int(mediana) if float(mediana).is_integer() else round(float(mediana), 4)

    # ------------------------------------------------------------- metadados

    etapa("Copiando o pacote... ")
    SAIDA.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem_modelo, SAIDA / "modelo.joblib")
    print("ok")

    metadados = {
        "modelo_versao": args.versao,
        "algoritmo": meta_origem.get("vencedor", "RandomForestClassifier"),
        "treinado_em": date.today().isoformat(),

        "atributos": atributos,
        "atributos_ignorados": IGNORADOS,
        "mapeamentos": MAPEAMENTOS,

        "classes": [int(c) for c in pipeline.classes_],
        "classe_churn": 1,

        "explicacao": {
            "tipo": "tree",
            "arquivo": None,
            "atributos_transformados": ordem_transformada,
            "importancias": None,
            "referencias": referencias,
        },

        "bibliotecas": {
            "scikit-learn": versao_de("scikit-learn"),
            "numpy": versao_de("numpy"),
            "joblib": versao_de("joblib"),
            "shap": versao_de("shap"),
            "imbalanced-learn": versao_de("imbalanced-learn"),
        },

        "sementes": {
            "seed_holdout": meta_origem.get("seed_holdout"),
            "seed_cv": meta_origem.get("seed_cv"),
        },

        "origem": {
            "repositorio": "pisi3-grupo4",
            "arquivo": "models/modelo_final.joblib",
            "criterio": meta_origem.get("criterio"),
            "cv_f1": meta_origem.get("cv_f1"),
            "n_treino": meta_origem.get("n_treino"),
            "n_teste": meta_origem.get("n_teste"),
            "sha256_da_base": meta_origem.get("sha256"),
            "versoes_do_treino": meta_origem.get("versoes"),
        },

        "observacoes": (
            "Importado de pisi3-grupo4 por ml/importar_modelo.py. O pipeline "
            "reordena as colunas, por isso explicacao.atributos_transformados "
            "declara a ordem vista pelo estimador."
        ),
    }

    (SAIDA / "metadados.json").write_text(
        json.dumps(metadados, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # ------------------------------------------------------------ casos

    etapa("Gerando os casos de referencia... ")
    casos = montar_casos(df, pipeline, atributos)
    print(f"ok ({len(casos)})")

    (SAIDA / "casos_de_referencia.json").write_text(
        json.dumps(casos, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # ------------------------------------------------------------ resumo

    print(f"Pacote gravado em {SAIDA}")
    print(f"  versao          : {args.versao}")
    print(f"  algoritmo       : {metadados['algoritmo']}")
    print(f"  atributos       : {len(atributos)}")
    print(f"  casos           : {len(casos)}")

    if reordenou:
        print()
        print("  O pipeline REORDENA as colunas. Ordem vista pelo estimador:")
        print(f"    {', '.join(ordem_transformada)}")
        print("  Declarada em explicacao.atributos_transformados.")

    treino = meta_origem.get("versoes") or {}
    divergentes = [
        (p, v, versao_de(p))
        for p, v in treino.items()
        if versao_de(p) != "ausente" and str(v).split(".")[0] != versao_de(p).split(".")[0]
    ]
    if divergentes:
        print()
        print("  AVISO: divergencia de versao maior entre treino e esta maquina:")
        for pacote, no_treino, aqui in divergentes:
            print(f"    {pacote}: treino {no_treino}, aqui {aqui}")
        print("  Conferir os casos de referencia antes de confiar no resultado.")

    print()
    print("Proximo passo:")
    print("  cd ..\\api && python testar_predicao.py")
    return 0


def montar_casos(df, pipeline, atributos: list[str]) -> list[dict]:
    """Casos cobrindo as tres faixas e os extremos do dominio."""
    import pandas as pd

    inteiros = {c for c, t in df.dtypes.items() if pd.api.types.is_integer_dtype(t)}
    indice_churn = list(pipeline.classes_).index(1)

    def entrada_de(linha) -> dict:
        saida = {}
        for campo in df.columns:
            if campo == "churn":
                continue
            valor = linha[campo]
            if hasattr(valor, "item"):
                valor = valor.item()
            saida[campo] = int(valor) if campo in inteiros else round(float(valor), 4)
        return saida

    def prever(entrada: dict) -> float:
        X = pd.DataFrame([preparar(entrada)])[atributos]
        return round(float(pipeline.predict_proba(X)[0][indice_churn]), 4)

    escolhidos: list[tuple[str, dict]] = []

    # Extremo do dominio de cobranca: os sete registros que ja causaram
    # divergencia entre o aplicativo e a API.
    dez = df[df.charge_amount == 10]
    if not dez.empty:
        escolhidos.append(("Cobranca na faixa 10, extremo do dominio", entrada_de(dez.iloc[0])))

    # Um caso de cada combinacao de plano e situacao da linha, para que o
    # mapeamento de tariff_plan e status seja exercitado nas quatro formas. Se a
    # API deixar de aplicar o mapeamento, algum destes muda de faixa.
    for plano in (1, 2):
        for situacao in (1, 2):
            recorte = df[(df.tariff_plan == plano) & (df.status == situacao)]
            if not recorte.empty:
                escolhidos.append((
                    f"Plano {plano}, situacao da linha {situacao}",
                    entrada_de(recorte.iloc[0]),
                ))

    # Cobrir as tres faixas: procura na base um registro para cada uma.
    encontradas: set[str] = set()
    for _, linha in df.iterrows():
        if len(encontradas) == 3:
            break
        entrada = entrada_de(linha)
        f = faixa(prever(entrada))
        if f not in encontradas:
            encontradas.add(f)
            escolhidos.append((f"Registro de risco {f}", entrada))

    casos = []
    vistos: set[str] = set()

    for descricao, entrada in escolhidos:
        assinatura = json.dumps(entrada, sort_keys=True)
        if assinatura in vistos:
            continue
        vistos.add(assinatura)

        probabilidade = prever(entrada)
        casos.append({
            "descricao": descricao,
            "entrada": entrada,
            "probabilidade_esperada": probabilidade,
            "faixa_esperada": faixa(probabilidade),
        })

    return casos


if __name__ == "__main__":
    raise SystemExit(main())