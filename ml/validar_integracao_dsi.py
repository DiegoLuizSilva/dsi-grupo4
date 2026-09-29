"""Confere o artefato integrado por Lucas e, opcionalmente, o POST /predict.

Uso local: python ml/validar_integracao_dsi.py
Com API:   CHURNGUARD_ID_TOKEN=<token> python ml/validar_integracao_dsi.py --api-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.exceptions import InconsistentVersionWarning


RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "ml" / "artefatos"
REFERENCIAS = RAIZ / "ml" / "reports" / "casos_shap_referencia.json"
SHA256_MODELO = "6aa328bb7f32c09867165722892fc1ae9c1a44fca40615251dbd894390a7b567"
sys.path.insert(0, str(RAIZ / "api"))
from faixas import ATRIBUTOS, classificar, descrever  # noqa: E402


def preparar(payload: dict, features: list[str]) -> pd.DataFrame:
    entrada = {campo: payload[campo] for campo in features}
    for campo in ("tariff_plan", "status"):
        entrada[campo] = {1: 0, 2: 1}[entrada[campo]]
    return pd.DataFrame([entrada], columns=features)


def consultar_api(url: str, payload: dict) -> dict:
    token = os.getenv("CHURNGUARD_ID_TOKEN")
    if not token:
        raise ValueError("Defina CHURNGUARD_ID_TOKEN para comparar com a API autenticada.")
    requisicao = urllib.request.Request(
        url.rstrip("/") + "/predict",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(requisicao, timeout=15) as resposta:
        return json.load(resposta)


def validar(api_url: str | None, fatores_estritos: bool, pisi_root: Path,
            rota_local: bool) -> None:
    meta = json.loads((PASTA / "metadados.json").read_text(encoding="utf-8"))
    casos = json.loads(REFERENCIAS.read_text(encoding="utf-8"))
    sha = hashlib.sha256((PASTA / "modelo.joblib").read_bytes()).hexdigest()
    assert sha == SHA256_MODELO, "O modelo integrado mudou; atualizar os casos de referência."
    atributos = meta["atributos"]
    assert "age_group" in meta["atributos_ignorados"]
    assert "age_group" not in atributos and len(atributos) == 12
    assert all(campo in ATRIBUTOS for campo in atributos)
    assert [classificar(p) for p in (0.2999, 0.30, 0.65, 0.6501)] == [
        "baixo", "medio", "medio", "alto"
    ]

    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always", InconsistentVersionWarning)
        modelo = joblib.load(PASTA / "modelo.joblib")
    n_avisos = sum(issubclass(a.category, InconsistentVersionWarning) for a in avisos)
    if n_avisos:
        print(f"AVISO: {n_avisos} alertas de versão sklearn; conferir versoes_do_treino nos metadados.")
    assert list(modelo.classes_) == [0, 1]
    assert meta["classe_churn"] == 1
    assert list(modelo.feature_names_in_) == atributos
    explicador = shap.TreeExplainer(modelo.named_steps["model"])
    nomes_transformados = list(modelo.named_steps["prep"].get_feature_names_out())
    if rota_local:
        from routers.predict import prever as prever_na_rota
        from schemas import PredictRequest
        from seguranca import Conta

    predicoes_pisi = pisi_root / "reports" / "tabelas" / "predicoes.csv"
    if predicoes_pisi.is_file():
        csv = RAIZ / "ml" / "data" / "raw" / "iranian_churn.csv"
        sha_csv = hashlib.sha256(csv.read_bytes()).hexdigest()
        assert sha_csv == meta["origem"]["sha256_da_base"]
        dados = pd.read_csv(csv)
        dados.columns = dados.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
        publicados = pd.read_csv(predicoes_pisi)
        publicados = publicados.loc[
            (publicados["experimento"] == "Random Forest | SMOTENC")
            & (publicados["conjunto"] == "teste")
        ]
        assert len(publicados) == meta["origem"]["n_teste"] == 633
        entradas = dados.iloc[publicados["row_id"].to_numpy()].drop(
            columns=["churn", "age_group"]
        ).copy()
        for campo in ("tariff_plan", "status"):
            entradas[campo] = entradas[campo].map({1: 0, 2: 1})
        scores = modelo.predict_proba(entradas.loc[:, atributos])[:, 1]
        desvio = float(np.max(np.abs(scores - publicados["score"].to_numpy())))
        assert desvio < 1e-9, f"As 633 predições divergem do PISI3: {desvio}"
        print(f"Teste PISI3: 633 scores reproduzidos; desvio máximo {desvio:.2g}.")
    else:
        print("Resultados de PISI3 não encontrados; comparação das 633 linhas não executada.")

    tempos_locais = []
    tempos_api = []
    for caso in casos:
        inicio = time.perf_counter()
        entrada = preparar(caso["entrada_api"], atributos)
        prob = float(modelo.predict_proba(entrada)[0, 1])
        assert np.isclose(prob, caso["probabilidade_exata"], atol=1e-9)
        transformado = modelo.named_steps["prep"].transform(entrada)
        valores = np.asarray(explicador.shap_values(transformado))[0, :, 1]
        assert np.isclose(explicador.expected_value[1] + valores.sum(), prob, atol=1e-8)
        indices = np.argsort(-np.abs(valores))[:3]
        maior = max(abs(valores[i]) for i in indices)
        fatores = [
            {
                "campo": nomes_transformados[i],
                "impacto": "aumenta" if valores[i] > 0 else "reduz",
                "peso": round(float(abs(valores[i]) / maior), 4),
            }
            for i in indices
        ]
        assert fatores == [
            {k: f[k] for k in ("campo", "impacto", "peso")}
            for f in caso["fatores_tree_shap"]
        ], "Os três fatores locais mudaram."
        for fator in fatores:
            traducao = descrever(fator["campo"], fator["impacto"])
            assert traducao["rotulo"] and traducao["sugestao"]
        tempos_locais.append(time.perf_counter() - inicio)

        if rota_local:
            resposta_local = prever_na_rota(
                PredictRequest(**caso["entrada_api"]), Conta("validacao-local")
            )
            assert abs(resposta_local["probabilidade"] - round(prob, 4)) <= 0.0001
            assert resposta_local["faixa"] == classificar(prob)
            assert resposta_local["modelo_versao"] == meta["modelo_versao"]
            assert [f["campo"] for f in resposta_local["fatores"]] == [
                f["campo"] for f in fatores
            ]
            assert [f["impacto"] for f in resposta_local["fatores"]] == [
                f["impacto"] for f in fatores
            ]

        if api_url:
            inicio = time.perf_counter()
            resposta = consultar_api(api_url, caso["entrada_api"])
            tempos_api.append(time.perf_counter() - inicio)
            assert abs(resposta["probabilidade"] - round(prob, 4)) <= 0.0001, (
                f"API divergiu para row_id={caso['row_id']}: "
                f"{resposta['probabilidade']} != {round(prob, 4)}"
            )
            assert resposta["faixa"] == classificar(prob)
            assert resposta["modelo_versao"] == meta["modelo_versao"]
            assert len(resposta["fatores"]) == 3
            pesos = [f["peso"] for f in resposta["fatores"]]
            assert pesos == sorted(pesos, reverse=True)
            for fator in resposta["fatores"]:
                assert fator["campo"] in ATRIBUTOS
                assert fator["impacto"] in ("aumenta", "reduz")
                assert fator["rotulo"] == descrever(fator["campo"], fator["impacto"])["rotulo"]
            if fatores_estritos:
                for atual, esperado in zip(resposta["fatores"], fatores):
                    assert atual["campo"] == esperado["campo"]
                    assert atual["impacto"] == esperado["impacto"]
                    assert abs(atual["peso"] - esperado["peso"]) <= 0.0001
        print(f"row_id={caso['row_id']}: classe_positiva=1, score={prob:.4f}, "
              f"faixa={classificar(prob)}, fatores={[f['campo'] for f in fatores]}")

    print(f"Validação local: {len(casos)} casos OK; maior duração "
          f"{max(tempos_locais):.3f}s, incluindo TreeSHAP.")
    if rota_local:
        print(f"Rota local: {len(casos)} respostas reais conferidas, sem stub.")
    if api_url:
        print(f"API: {len(tempos_api)} casos OK; maior duração HTTP {max(tempos_api):.3f}s.")
        print("O limite de 3s no celular ainda exige medição no dispositivo e na rede final.")
    else:
        print("Comparação HTTP pendente: execute com --api-url e CHURNGUARD_ID_TOKEN.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", help="Endereço da API publicada ou local")
    parser.add_argument(
        "--rota-local", action="store_true",
        help="Compara a função da rota /predict sem rede nem acesso ao Firestore",
    )
    parser.add_argument(
        "--pisi-root", type=Path, default=RAIZ.parent / "pisi3-grupo4",
        help="Repositório PISI3 para comparar todas as predições do teste",
    )
    parser.add_argument(
        "--fatores-estritos", action="store_true",
        help="Exige mesmos top-3, sinal e peso de TreeSHAP na resposta da API",
    )
    args = parser.parse_args()
    validar(args.api_url, args.fatores_estritos, args.pisi_root.resolve(), args.rota_local)
