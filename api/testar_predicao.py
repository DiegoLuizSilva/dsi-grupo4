"""Testes de integracao do motor de predicao.

Cobre os cenarios exigidos na Sprint 5: entrada valida, campo ausente, valor
fora do dominio, falha de carregamento do modelo e consistencia entre a
predicao direta no pipeline e a resposta da API.

Roda sem pytest, para nao acrescentar dependencia ao requirements da API:

    cd api
    python testar_predicao.py

Saida esperada: todas as linhas com `ok`. Qualquer `FALHOU` precisa ser
resolvido antes de considerar a integracao concluida.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# A API usa imports planos (`import modelo`), entao a pasta precisa estar no
# caminho de busca quando o teste e chamado de fora dela.
sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("CHURNGUARD_PERMITIR_STUB", "0")

import modelo  # noqa: E402
from faixas import CORTE_ALTO, CORTE_BAIXO, classificar  # noqa: E402
from schemas import PredictRequest  # noqa: E402

TOLERANCIA = 1e-4

_passou = 0
_falhou = 0


def verificar(condicao: bool, descricao: str, detalhe: str = "") -> None:
    global _passou, _falhou
    if condicao:
        _passou += 1
        print(f"ok      {descricao}")
    else:
        _falhou += 1
        print(f"FALHOU  {descricao}")
        if detalhe:
            print(f"        {detalhe}")


def secao(titulo: str) -> None:
    print(f"\n--- {titulo} ---")


ENTRADA_VALIDA = {
    "call_failure": 8, "complains": 0, "subscription_length": 38,
    "charge_amount": 0, "seconds_of_use": 4370, "frequency_of_use": 71,
    "frequency_of_sms": 5, "distinct_called_numbers": 17, "age_group": 3,
    "tariff_plan": 1, "status": 1, "age": 30, "customer_value": 197.64,
}


# ------------------------------------------------------- 1. faixas de risco

def testar_faixas() -> None:
    secao("Faixas de risco nos limites")

    verificar(classificar(0.0) == "baixo", "probabilidade 0 cai em baixo")
    verificar(classificar(0.2999) == "baixo", "0,2999 cai em baixo")
    verificar(classificar(CORTE_BAIXO) == "medio",
              f"o proprio corte {CORTE_BAIXO} cai em medio")
    verificar(classificar(0.5) == "medio", "0,5 cai em medio")
    verificar(classificar(CORTE_ALTO) == "medio",
              f"o proprio corte {CORTE_ALTO} cai em medio")
    verificar(classificar(0.6501) == "alto", "0,6501 cai em alto")
    verificar(classificar(1.0) == "alto", "probabilidade 1 cai em alto")


# ------------------------------------------- 2. carregamento e disponibilidade

def testar_carregamento() -> None:
    secao("Carregamento do pacote do modelo")

    try:
        motor = modelo.carregar()
    except modelo.ErroDeCarregamento as erro:
        verificar(False, "pacote do modelo carregado", str(erro))
        print("\n        Sem pacote em ml/artefatos/ nao ha o que testar.")
        print("        Rodar: cd ml && python gerar_artefato_de_ensaio.py")
        resumo()
        sys.exit(1)

    verificar(True, f"pacote carregado, versao {motor.versao}")
    verificar(len(motor.atributos) > 0, "metadado declara atributos")
    verificar("age_group" in motor.ignorados,
              "age_group esta declarada como ignorada",
              f"ignorados: {motor.ignorados}")
    verificar(motor.indice_churn in (0, 1),
              "coluna da classe de churn localizada em classes_",
              f"indice: {motor.indice_churn}")

    situacao = modelo.situacao()
    verificar(situacao["carregado"] is True, "/health reporta modelo carregado")
    verificar(situacao["modelo_versao"] == motor.versao,
              "/health reporta a mesma versao do motor")


def testar_falha_de_carregamento() -> None:
    secao("Falha de carregamento com pasta inexistente")

    original = modelo.PASTA_ARTEFATOS
    try:
        modelo.PASTA_ARTEFATOS = Path("/caminho/que/nao/existe")
        try:
            modelo.carregar(forcar=True)
            verificar(False, "ErroDeCarregamento levantado quando o pacote nao existe")
        except modelo.ErroDeCarregamento as erro:
            verificar("nao encontrado" in str(erro).lower(),
                      "ErroDeCarregamento levantado com mensagem util",
                      str(erro)[:120])
    finally:
        modelo.PASTA_ARTEFATOS = original
        modelo.carregar(forcar=True)

    verificar(modelo.disponivel() is True,
              "modelo volta a ficar disponivel apos restaurar a pasta")


# --------------------------------------------------- 3. tratamento da entrada

def testar_preparacao() -> None:
    secao("Tratamento declarado da entrada")

    motor = modelo.carregar()
    linha = motor.preparar(dict(ENTRADA_VALIDA))

    verificar("age_group" not in linha,
              "age_group foi retirada antes de chegar ao modelo")
    verificar(list(linha.keys()) == motor.atributos,
              "colunas na ordem exata declarada no metadado",
              f"obtido: {list(linha.keys())}")

    if "tariff_plan" in motor.mapeamentos:
        verificar(linha["tariff_plan"] == 0,
                  "tariff_plan 1 convertido para 0 conforme o mapeamento",
                  f"obtido: {linha['tariff_plan']}")
    if "status" in motor.mapeamentos:
        verificar(linha["status"] == 0,
                  "status 1 convertido para 0 conforme o mapeamento",
                  f"obtido: {linha['status']}")

    # Cobranca 10: os sete registros do CSV que o app e a API ja recusaram.
    entrada = dict(ENTRADA_VALIDA, charge_amount=10)
    try:
        motor.preparar(entrada)
        verificar(True, "charge_amount = 10 aceito no tratamento")
    except modelo.ErroDeDominio as erro:
        verificar(False, "charge_amount = 10 aceito no tratamento", str(erro))


def testar_dominio() -> None:
    secao("Valor fora do dominio e campo ausente")

    motor = modelo.carregar()

    if motor.mapeamentos:
        campo = next(iter(motor.mapeamentos))
        entrada = dict(ENTRADA_VALIDA)
        entrada[campo] = 99
        try:
            motor.preparar(entrada)
            verificar(False, f"{campo} = 99 recusado em vez de convertido por omissao")
        except modelo.ErroDeDominio as erro:
            verificar(campo in str(erro),
                      f"{campo} fora do mapeamento recusado com mensagem clara",
                      str(erro)[:140])

    incompleta = {c: v for c, v in ENTRADA_VALIDA.items() if c != "customer_value"}
    try:
        motor.preparar(incompleta)
        verificar(False, "atributo ausente recusado")
    except modelo.ErroDeDominio as erro:
        verificar("customer_value" in str(erro),
                  "atributo ausente recusado nomeando o campo",
                  str(erro)[:140])

    # O Pydantic barra antes de chegar ao motor. Vale confirmar que continua
    # barrando, porque o app depende dessa mensagem.
    try:
        PredictRequest(**dict(ENTRADA_VALIDA, charge_amount=11))
        verificar(False, "Pydantic recusa charge_amount = 11")
    except Exception:
        verificar(True, "Pydantic recusa charge_amount = 11")

    try:
        PredictRequest(**{c: v for c, v in ENTRADA_VALIDA.items() if c != "age"})
        verificar(False, "Pydantic recusa requisicao sem age")
    except Exception:
        verificar(True, "Pydantic recusa requisicao sem age")


# ------------------------------------------------------- 4. fatores e resposta

def testar_fatores() -> None:
    secao("Fatores da explicacao")

    resultado = modelo.prever(PredictRequest(**ENTRADA_VALIDA))

    verificar(0.0 <= resultado["probabilidade"] <= 1.0,
              "probabilidade dentro de [0, 1]",
              f"obtido: {resultado['probabilidade']}")
    verificar(len(resultado["fatores"]) <= 3,
              "no maximo tres fatores",
              f"obtido: {len(resultado['fatores'])}")
    verificar(len(resultado["fatores"]) > 0, "ao menos um fator devolvido")

    pesos = [f["peso"] for f in resultado["fatores"]]
    verificar(pesos == sorted(pesos, reverse=True),
              "fatores ordenados por peso decrescente",
              f"pesos: {pesos}")
    verificar(all(0.0 <= p <= 1.0 for p in pesos),
              "pesos normalizados entre 0 e 1", f"pesos: {pesos}")
    if pesos:
        verificar(abs(pesos[0] - 1.0) < TOLERANCIA,
                  "o maior fator tem peso relativo 1",
                  f"obtido: {pesos[0]}")
    verificar(all(f["impacto"] in ("aumenta", "reduz") for f in resultado["fatores"]),
              "impacto de cada fator e aumenta ou reduz")

    motor = modelo.carregar()
    verificar(all(f["campo"] in motor.atributos for f in resultado["fatores"]),
              "campos dos fatores existem no metadado",
              f"campos: {[f['campo'] for f in resultado['fatores']]}")

    verificar(resultado["modelo_versao"] == motor.versao,
              "resposta carrega a versao do modelo carregado")


def testar_sinal_da_explicacao() -> None:
    secao("Sinal da explicacao")

    # Se a classe explicada estiver invertida, todos os fatores apontam para o
    # lado errado sem gerar erro. Comparar dois clientes identicos que diferem
    # apenas na reclamacao e a forma mais direta de detectar isso.
    sem = modelo.prever(PredictRequest(**dict(ENTRADA_VALIDA, complains=0)))
    com = modelo.prever(PredictRequest(**dict(ENTRADA_VALIDA, complains=1)))

    verificar(com["probabilidade"] >= sem["probabilidade"],
              "registrar reclamacao nao reduz a probabilidade de cancelamento",
              f"sem: {sem['probabilidade']}  com: {com['probabilidade']}")

    salto = com["probabilidade"] - sem["probabilidade"]
    fator = next((f for f in com["fatores"] if f["campo"] == "complains"), None)

    if fator is not None:
        verificar(fator["impacto"] == "aumenta",
                  "reclamacao aparece como fator que aumenta o risco",
                  f"obtido: {fator['impacto']}")
    elif salto > 0.10:
        # A reclamacao mexeu muito na probabilidade mas nao entrou nos tres
        # fatores. O sintoma classico de vetor SHAP desalinhado das colunas:
        # as contribuicoes sao atribuidas aos atributos errados.
        verificar(False,
                  "reclamacao entra nos fatores quando muda a probabilidade",
                  f"probabilidade subiu {salto:.3f} mas complains ficou fora de "
                  f"{[f['campo'] for f in com['fatores']]}. Conferir "
                  f"explicacao.atributos_transformados no metadado.")
    else:
        print("aviso   complains nao entrou nos tres fatores, e o salto foi pequeno")


def testar_alinhamento_das_colunas() -> None:
    """Confere que a ordem usada na explicacao e a que o estimador ve.

    Existe porque o erro aqui nao gera excecao: o pipeline do projeto tem um
    ColumnTransformer que escala os numericos primeiro e passa os binarios
    depois, entao a ordem de saida difere da de entrada. Casar o vetor SHAP com
    a ordem de entrada troca as contribuicoes entre atributos, e o resultado e
    um fator com o sinal invertido na tela, com a probabilidade correta ao lado.
    """
    secao("Alinhamento das colunas da explicacao")

    motor = modelo.carregar()

    verificar(len(motor.atributos_explicados) == len(motor.atributos),
              "a ordem da explicacao tem a mesma quantidade de atributos",
              f"entrada {len(motor.atributos)}, explicacao "
              f"{len(motor.atributos_explicados)}")

    verificar(set(motor.atributos_explicados) == set(motor.atributos),
              "a ordem da explicacao cobre os mesmos atributos da entrada",
              f"diferenca: {set(motor.atributos) ^ set(motor.atributos_explicados)}")

    estimador = motor.estimador_final()
    esperado = getattr(estimador, "n_features_in_", None)
    if esperado is not None:
        verificar(len(motor.atributos_explicados) == esperado,
                  "a ordem da explicacao bate com o que o estimador espera",
                  f"estimador espera {esperado}")

    if motor.transformar_para_explicar:
        import pandas as pd

        X = pd.DataFrame([motor.preparar(dict(ENTRADA_VALIDA))], columns=motor.atributos)
        transformado = motor.transformar(X)
        largura = transformado.shape[1]

        verificar(largura == len(motor.atributos_explicados),
                  "a transformacao devolve tantas colunas quanto a ordem declarada",
                  f"transformacao {largura}, declarada {len(motor.atributos_explicados)}")

        if motor.atributos_explicados != motor.atributos:
            print("aviso   o pipeline reordena as colunas; ordem do estimador:")
            print(f"        {', '.join(motor.atributos_explicados)}")


# -------------------------------------------- 5. consistencia com o pipeline

def testar_consistencia() -> None:
    secao("Consistencia entre predicao direta e motor da API")

    motor = modelo.carregar()
    caminho = modelo.PASTA_ARTEFATOS / "casos_de_referencia.json"

    if not caminho.exists():
        print("aviso   casos_de_referencia.json ausente; teste nao executado")
        print("        Exigir o arquivo conforme ml/CONTRATO_MODELO.md, secao 5.")
        return

    casos = json.loads(caminho.read_text(encoding="utf-8"))
    verificar(len(casos) >= 6,
              "pacote traz ao menos seis casos de referencia",
              f"obtido: {len(casos)}")

    for caso in casos:
        entrada = caso["entrada"]
        esperado = caso["probabilidade_esperada"]

        obtido = modelo.prever(PredictRequest(**entrada))["probabilidade"]
        diferenca = abs(obtido - esperado)

        verificar(diferenca < TOLERANCIA,
                  f"caso reproduzido: {caso['descricao']}",
                  f"esperado {esperado}, obtido {obtido}, diferenca {diferenca:.2e}")

        if "faixa_esperada" in caso:
            verificar(classificar(obtido) == caso["faixa_esperada"],
                      f"faixa correta: {caso['descricao']}",
                      f"esperada {caso['faixa_esperada']}, obtida {classificar(obtido)}")


def testar_determinismo() -> None:
    secao("Determinismo")

    a = modelo.prever(PredictRequest(**ENTRADA_VALIDA))
    b = modelo.prever(PredictRequest(**ENTRADA_VALIDA))

    verificar(a["probabilidade"] == b["probabilidade"],
              "a mesma entrada produz a mesma probabilidade")
    verificar([f["campo"] for f in a["fatores"]] == [f["campo"] for f in b["fatores"]],
              "a mesma entrada produz os mesmos fatores")


def testar_tempo() -> None:
    secao("Tempo de resposta")

    import time

    # Primeira chamada com o modelo ja carregado, para medir a inferencia e a
    # explicacao sem o custo de leitura do disco.
    modelo.prever(PredictRequest(**ENTRADA_VALIDA))

    inicio = time.perf_counter()
    for _ in range(10):
        modelo.prever(PredictRequest(**ENTRADA_VALIDA))
    medio = (time.perf_counter() - inicio) / 10

    verificar(medio < 3.0,
              f"inferencia com explicacao em {medio * 1000:.1f} ms, dentro de 3 s")
    print(f"        media de {medio * 1000:.1f} ms por avaliacao (10 chamadas)")


# --------------------------------------------------------- 6. contrato da API

def testar_endpoint() -> None:
    secao("Endpoint /predict pelo cliente de teste")

    try:
        from fastapi.testclient import TestClient
    except ImportError:
        print("aviso   httpx nao instalado; teste do endpoint nao executado")
        print("        Rodar: pip install httpx")
        return

    try:
        from main import app
    except Exception as erro:
        print(f"aviso   app nao importado ({type(erro).__name__}: {erro})")
        print("        Normal sem credencial do Firebase; os testes acima cobrem o motor.")
        return

    # Esta secao exercita o contrato da resposta e a validacao de entrada, que
    # exigem requisicoes ACEITAS. A autorizacao e verificada na secao seguinte,
    # que liga a exigencia de volta. Controlar a variavel aqui deixa o arquivo
    # rodavel com um `python testar_predicao.py` simples, sem preparo nenhum.
    original = os.environ.get("CHURNGUARD_EXIGIR_AUTENTICACAO")
    os.environ["CHURNGUARD_EXIGIR_AUTENTICACAO"] = "0"

    try:
        _testar_endpoint_sem_autenticacao(TestClient(app))
    finally:
        if original is None:
            os.environ.pop("CHURNGUARD_EXIGIR_AUTENTICACAO", None)
        else:
            os.environ["CHURNGUARD_EXIGIR_AUTENTICACAO"] = original


def _testar_endpoint_sem_autenticacao(cliente) -> None:
    resposta = cliente.post("/predict", json=ENTRADA_VALIDA)
    verificar(resposta.status_code == 200,
              "entrada valida devolve 200",
              f"obtido {resposta.status_code}: {resposta.text[:200]}")

    if resposta.status_code == 200:
        corpo = resposta.json()
        esperados = {"probabilidade", "faixa", "rotulo_faixa", "fatores",
                     "modelo_versao", "gerado_em"}
        verificar(esperados.issubset(corpo.keys()),
                  "resposta traz todos os campos do contrato",
                  f"faltando: {esperados - set(corpo.keys())}")
        verificar(corpo["faixa"] in ("baixo", "medio", "alto"), "faixa valida")
        verificar(corpo["faixa"] == classificar(corpo["probabilidade"]),
                  "faixa coerente com a probabilidade devolvida")
        verificar(all({"campo", "rotulo", "impacto", "peso", "sugestao"} <= set(f)
                      for f in corpo["fatores"]),
                  "cada fator traz rotulo e sugestao para a tela")
        verificar(not corpo["modelo_versao"].startswith("stub"),
                  "resposta nao vem do stub",
                  f"versao: {corpo['modelo_versao']}")

    fora = cliente.post("/predict", json=dict(ENTRADA_VALIDA, charge_amount=11))
    verificar(fora.status_code == 422,
              "charge_amount = 11 devolve 422",
              f"obtido {fora.status_code}")

    ausente = cliente.post(
        "/predict",
        json={c: v for c, v in ENTRADA_VALIDA.items() if c != "complains"},
    )
    verificar(ausente.status_code == 422,
              "campo ausente devolve 422",
              f"obtido {ausente.status_code}")

    saude = cliente.get("/health")
    verificar(saude.status_code == 200, "/health responde 200")
    if saude.status_code == 200:
        bloco = saude.json().get("modelo", {})
        verificar(bloco.get("carregado") is True,
                  "/health informa que o modelo esta carregado",
                  json.dumps(bloco, ensure_ascii=False))


def testar_autorizacao() -> None:
    """Confere que as rotas recusam requisicao sem token quando exigido.

    E o cenario que importa na hospedagem: uma requisicao direta ao endereco
    do servico, sem passar pelo aplicativo, precisa ser recusada pelo servidor.
    """
    secao("Autorizacao das rotas")

    try:
        from fastapi.testclient import TestClient
        from main import app
    except Exception:
        print("aviso   app nao importado; teste de autorizacao nao executado")
        return

    import seguranca

    original = os.environ.get("CHURNGUARD_EXIGIR_AUTENTICACAO")
    os.environ["CHURNGUARD_EXIGIR_AUTENTICACAO"] = "1"

    try:
        cliente = TestClient(app)

        sem_token = cliente.post("/predict", json=ENTRADA_VALIDA)
        verificar(sem_token.status_code == 401,
                  "/predict sem token devolve 401",
                  f"obtido {sem_token.status_code}: {sem_token.text[:160]}")

        lista = cliente.get("/clientes")
        verificar(lista.status_code == 401,
                  "GET /clientes sem token devolve 401",
                  f"obtido {lista.status_code}: {lista.text[:160]}")

        remocao = cliente.delete("/clientes/qualquer-id")
        verificar(remocao.status_code == 401,
                  "DELETE /clientes sem token devolve 401",
                  f"obtido {remocao.status_code}: {remocao.text[:160]}")

        invalido = cliente.post(
            "/predict",
            json=ENTRADA_VALIDA,
            headers={"Authorization": "Bearer token-invalido"},
        )
        verificar(invalido.status_code in (401, 503),
                  "token invalido recusado sem chegar ao modelo",
                  f"obtido {invalido.status_code}: {invalido.text[:160]}")

        saude = cliente.get("/health")
        verificar(saude.status_code == 200,
                  "/health continua aberto, para monitoramento")
        if saude.status_code == 200:
            verificar(saude.json().get("autenticacao_exigida") is True,
                      "/health informa que a autenticacao esta exigida")

        verificar(seguranca._exige_autenticacao() is True,
                  "o padrao da configuracao e exigir autenticacao")
    finally:
        if original is None:
            os.environ.pop("CHURNGUARD_EXIGIR_AUTENTICACAO", None)
        else:
            os.environ["CHURNGUARD_EXIGIR_AUTENTICACAO"] = original


# ------------------------------------------------------------------- resumo

def resumo() -> None:
    print(f"\n{'=' * 60}")
    print(f"{_passou} verificacoes passaram, {_falhou} falharam")
    print("=" * 60)


def main() -> int:
    print("Testes do motor de predicao do ChurnGuard")
    print(f"Pasta de artefatos: {modelo.PASTA_ARTEFATOS}")

    testar_faixas()
    testar_carregamento()
    testar_preparacao()
    testar_dominio()
    testar_fatores()
    testar_alinhamento_das_colunas()
    testar_sinal_da_explicacao()
    testar_consistencia()
    testar_determinismo()
    testar_tempo()
    testar_falha_de_carregamento()
    testar_endpoint()
    testar_autorizacao()

    resumo()
    return 1 if _falhou else 0


if __name__ == "__main__":
    sys.exit(main())