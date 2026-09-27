"""Gera um artefato de ensaio no formato do contrato, para testar a API.

ATENCAO
-------
O pacote produzido aqui NAO e o modelo do projeto. Serve para um unico
proposito: exercitar o carregamento, a inferencia e a explicacao da API antes
de o modelo real existir, para que a integracao da Sprint 5 nao precise esperar
a frente de classificacao terminar.

Nao tem protocolo de validacao por grupos, nao tem balanceamento, nao tem
ajuste de hiperparametros e nao foi comparado com outros algoritmos. Seus
numeros nao entram no artigo em nenhuma hipotese. A versao declarada e
`ensaio-0.x` justamente para que apareca na resposta da API e no historico
caso alguem esqueca de trocar o artefato.

Quando o pacote de Diego chegar, apagar `ml/artefatos/` e colocar o dele no
lugar. Nada no codigo da API precisa mudar.

Uso:
    cd ml
    python gerar_artefato_de_ensaio.py
"""

from __future__ import annotations

import importlib.metadata as md
import json
from datetime import date
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "data" / "raw" / "iranian_churn.csv"
SAIDA = AQUI / "artefatos"

SEMENTE = 42
VERSAO = "ensaio-0.1"

# As mesmas decisoes de 02_pre_processamento.ipynb, replicadas aqui para que o
# artefato de ensaio tenha o mesmo formato de entrada do artefato real.
IGNORADOS = ["age_group"]
MAPEAMENTOS = {
    "tariff_plan": {"1": 0, "2": 1},
    "status": {"1": 0, "2": 1},
}


def carregar_base() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    )
    return df


def preparar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    X = df.drop(columns="churn").drop(columns=IGNORADOS).copy()
    y = df["churn"].copy()

    for campo, mapa in MAPEAMENTOS.items():
        X[campo] = X[campo].map({int(k): v for k, v in mapa.items()})

    return X, y


def versao_de(pacote: str) -> str:
    try:
        return md.version(pacote)
    except md.PackageNotFoundError:
        return "ausente"


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)

    df = carregar_base()
    X, y = preparar(df)
    atributos = X.columns.tolist()

    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X, y, test_size=0.2, random_state=SEMENTE, stratify=y
    )

    modelo = RandomForestClassifier(
        n_estimators=200, random_state=SEMENTE, n_jobs=-1
    )
    modelo.fit(X_treino, y_treino)

    joblib.dump(modelo, SAIDA / "modelo.joblib")

    # Referencias: mediana do TREINO, no dominio original dos atributos.
    referencias: dict[str, float] = {}
    for campo in atributos:
        if campo in MAPEAMENTOS:
            # Volta para o dominio original (1/2), que e o que a API recebe.
            inverso = {v: int(k) for k, v in MAPEAMENTOS[campo].items()}
            referencias[campo] = int(X_treino[campo].map(inverso).median())
        else:
            referencias[campo] = float(round(X_treino[campo].median(), 4))

    importancias = {
        campo: float(round(peso, 6))
        for campo, peso in zip(atributos, modelo.feature_importances_)
    }

    explicador = None
    tipo_de_explicacao = "global"
    try:
        import shap

        explicador = shap.TreeExplainer(modelo)
        joblib.dump(explicador, SAIDA / "explainer.joblib")
        tipo_de_explicacao = "tree"
    except Exception as erro:  # pragma: no cover
        print(f"aviso: explicador SHAP nao gerado ({erro}); ficando na estrategia global.")

    metadados = {
        "modelo_versao": VERSAO,
        "algoritmo": "RandomForestClassifier",
        "treinado_em": date.today().isoformat(),
        "atributos": atributos,
        "atributos_ignorados": IGNORADOS,
        "mapeamentos": MAPEAMENTOS,
        "classes": [int(c) for c in modelo.classes_],
        "classe_churn": 1,
        "explicacao": {
            "tipo": tipo_de_explicacao,
            "arquivo": "explainer.joblib" if explicador is not None else None,
            "importancias": importancias,
            "referencias": referencias,
        },
        "bibliotecas": {
            "scikit-learn": versao_de("scikit-learn"),
            "numpy": versao_de("numpy"),
            "joblib": versao_de("joblib"),
            "shap": versao_de("shap"),
        },
        "sementes": {"random_state": SEMENTE},
        "observacoes": (
            "ARTEFATO DE ENSAIO. Sem validacao por grupos, sem balanceamento, "
            "sem ajuste de hiperparametros. Nao usar no artigo."
        ),
    }
    (SAIDA / "metadados.json").write_text(
        json.dumps(metadados, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    casos = montar_casos(df, modelo, atributos)
    (SAIDA / "casos_de_referencia.json").write_text(
        json.dumps(casos, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Pacote de ensaio gravado em {SAIDA}")
    print(f"  atributos do modelo: {len(atributos)}")
    print(f"  explicacao: {tipo_de_explicacao}")
    print(f"  casos de referencia: {len(casos)}")
    print(f"  acuracia no teste: {modelo.score(X_teste, y_teste):.4f}  (ensaio, nao reportar)")


def montar_casos(df: pd.DataFrame, modelo, atributos: list[str]) -> list[dict]:
    """Monta casos de referencia cobrindo as tres faixas e o extremo de cobranca."""
    escolhidos: list[tuple[str, pd.Series]] = []

    com_cobranca_dez = df[df["charge_amount"] == 10]
    if not com_cobranca_dez.empty:
        escolhidos.append(("Cobranca na faixa 10, extremo do dominio", com_cobranca_dez.iloc[0]))

    com_reclamacao = df[(df["complains"] == 1) & (df["status"] == 2)]
    if not com_reclamacao.empty:
        escolhidos.append(("Com reclamacao e linha nao ativa", com_reclamacao.iloc[0]))

    fiel = df[(df["complains"] == 0) & (df["subscription_length"] > 40)]
    if not fiel.empty:
        escolhidos.append(("Sem reclamacao e assinatura longa", fiel.iloc[0]))

    # Completa com registros variados para exercitar as faixas intermediarias.
    for posicao in (0, 700, 1500, 2400):
        if posicao < len(df):
            escolhidos.append((f"Registro {posicao} da base", df.iloc[posicao]))

    # Extrair uma linha de um DataFrame de tipos mistos devolve tudo como
    # float. Guardar os tipos originais mantem os inteiros como inteiros na
    # entrada, que e o que o aplicativo envia e o que o mapeamento espera.
    inteiros = {
        campo for campo, tipo in df.dtypes.items()
        if pd.api.types.is_integer_dtype(tipo)
    }

    casos = []
    for descricao, linha in escolhidos:
        entrada = {
            campo: _simples(linha[campo], campo in inteiros)
            for campo in df.columns
            if campo != "churn"
        }

        preparada = {c: v for c, v in entrada.items() if c not in IGNORADOS}
        for campo, mapa in MAPEAMENTOS.items():
            preparada[campo] = mapa[str(preparada[campo])]

        X = pd.DataFrame([preparada])[atributos]
        indice = list(modelo.classes_).index(1)
        probabilidade = round(float(modelo.predict_proba(X)[0][indice]), 4)

        casos.append({
            "descricao": descricao,
            "entrada": entrada,
            "probabilidade_esperada": probabilidade,
            "faixa_esperada": _faixa(probabilidade),
        })

    return casos


def _faixa(p: float) -> str:
    if p < 0.30:
        return "baixo"
    if p <= 0.65:
        return "medio"
    return "alto"


def _simples(valor, inteiro: bool):
    """Converte tipos do numpy em tipos que o json aceita."""
    if hasattr(valor, "item"):
        valor = valor.item()
    if inteiro:
        return int(valor)
    return round(valor, 4) if isinstance(valor, float) else valor


if __name__ == "__main__":
    main()
