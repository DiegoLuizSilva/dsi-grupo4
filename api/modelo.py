"""Carregamento do modelo treinado e inferencia real.

Este modulo substitui `stub.py` no caminho de execucao a partir da Sprint 5.
A assinatura de `prever` e identica a do stub, de proposito: o roteador nao
precisa saber qual dos dois esta ativo.

Nada do pre-processamento decidido pela frente de classificacao esta escrito
aqui. O modulo le `metadados.json`, exportado junto com o modelo, e executa o
que estiver declarado: quais atributos o modelo usa, em que ordem, quais campos
sao ignorados e quais valores precisam ser convertidos. Isso mantem a decisao
em um unico lugar, o notebook, e faz com que um ajuste de encoding seja uma
alteracao de metadado e nao de codigo.

O contrato do pacote esta em `ml/CONTRATO_MODELO.md`.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

from schemas import PredictRequest

logger = logging.getLogger("churnguard.modelo")

# Pasta do pacote exportado. Sobrescrita por variavel de ambiente na
# hospedagem, onde o artefato fica fora da arvore do repositorio.
PASTA_ARTEFATOS = Path(
    os.getenv("CHURNGUARD_ARTEFATOS", Path(__file__).resolve().parent.parent / "ml" / "artefatos")
)

ARQUIVO_MODELO = "modelo.joblib"
ARQUIVO_METADADOS = "metadados.json"

# Campos obrigatorios do metadado. A ausencia de qualquer um deles impede o
# carregamento: e melhor a API subir sem modelo e dizer por que do que
# responder com um modelo carregado pela metade.
CAMPOS_OBRIGATORIOS = ("modelo_versao", "atributos", "classe_churn")


class ErroDeCarregamento(RuntimeError):
    """O pacote do modelo nao existe, esta incompleto ou e incompativel."""


class ErroDeDominio(ValueError):
    """Um valor recebido nao pertence ao dominio que o modelo conhece."""


class Motor:
    """Guarda o pipeline carregado e o que e preciso saber para usa-lo."""

    def __init__(self, pipeline: Any, metadados: dict, explicador: Any = None):
        self.pipeline = pipeline
        self.metadados = metadados
        self.explicador = explicador

        self.versao: str = metadados["modelo_versao"]
        self.atributos: list[str] = list(metadados["atributos"])
        self.ignorados: list[str] = list(metadados.get("atributos_ignorados", []))

        # As chaves do JSON sao texto; o payload chega numerico. A conversao
        # acontece uma vez, no carregamento, e nao a cada requisicao.
        self.mapeamentos: dict[str, dict[Any, Any]] = {
            campo: {_chave(k): v for k, v in mapa.items()}
            for campo, mapa in metadados.get("mapeamentos", {}).items()
        }

        self.indice_churn = self._localizar_classe(metadados["classe_churn"])

        # A ordem que o estimador final ve pode nao ser a ordem de entrada: um
        # ColumnTransformer reordena as colunas. O vetor SHAP segue a ordem do
        # estimador, entao ela precisa ser descoberta e guardada separadamente.
        # Casar SHAP com a ordem de entrada inverte o sinal dos atributos que
        # mudaram de posicao. Ver o cabecalho de explicacao.py.
        self.transformar_para_explicar = bool(self._etapas_de_transformacao())
        self.atributos_explicados = self._descobrir_ordem_do_estimador()

    def _etapas_de_transformacao(self) -> list:
        """Etapas do pipeline antes do estimador final que sabem transformar.

        Um passo de reamostragem (SMOTE, SMOTENC) nao possui `transform` e e
        naturalmente ignorado aqui, que e o comportamento correto: reamostragem
        vale no treino e nao na inferencia.
        """
        passos = getattr(self.pipeline, "steps", None)
        if not passos:
            return []
        return [etapa for _, etapa in passos[:-1] if hasattr(etapa, "transform")]

    def estimador_final(self) -> Any:
        """O estimador no fim do pipeline, ou o proprio objeto se nao houver."""
        passos = getattr(self.pipeline, "steps", None)
        return passos[-1][1] if passos else self.pipeline

    def transformar(self, X: Any) -> Any:
        """Aplica as etapas de transformacao anteriores ao estimador final."""
        for etapa in self._etapas_de_transformacao():
            X = etapa.transform(X)
        return X

    def _descobrir_ordem_do_estimador(self) -> list[str]:
        """Nomes dos atributos na ordem vista pelo estimador final.

        Tenta, em ordem: o que o metadado declarar explicitamente; os nomes de
        saida das etapas de transformacao; a ordem de entrada. Se a contagem nao
        fechar com o que o estimador espera, recusa o carregamento em vez de
        seguir com um alinhamento errado, porque o sintoma de um alinhamento
        errado e um fator com o sinal invertido, nao um erro.
        """
        declarada = (self.metadados.get("explicacao") or {}).get("atributos_transformados")
        if declarada:
            return list(declarada)

        if not self.transformar_para_explicar:
            return list(self.atributos)

        etapas = self._etapas_de_transformacao()
        ultima = etapas[-1]

        obter = getattr(ultima, "get_feature_names_out", None)
        if obter is not None:
            try:
                nomes = [str(n) for n in obter()]
            except Exception as erro:
                raise ErroDeCarregamento(
                    "Nao foi possivel obter a ordem dos atributos apos a "
                    f"transformacao ({erro}). Declarar a lista em "
                    "explicacao.atributos_transformados no metadado."
                ) from erro

            esperado = getattr(self.estimador_final(), "n_features_in_", None)
            if esperado is not None and len(nomes) != esperado:
                raise ErroDeCarregamento(
                    f"A transformacao devolve {len(nomes)} colunas, mas o "
                    f"estimador espera {esperado}. Declarar a ordem correta em "
                    "explicacao.atributos_transformados."
                )
            return nomes

        raise ErroDeCarregamento(
            "O pipeline transforma os dados mas nao expoe get_feature_names_out. "
            "Declarar explicacao.atributos_transformados no metadado, na ordem "
            "vista pelo estimador final."
        )

    def _localizar_classe(self, classe_churn: Any) -> int:
        """Descobre qual coluna de predict_proba corresponde ao cancelamento.

        Assumir a coluna 1 funciona por acidente na maioria dos casos e falha
        em silencio quando o estimador ordena as classes de outra forma.
        """
        classes = getattr(self.pipeline, "classes_", None)
        if classes is None:
            raise ErroDeCarregamento(
                "O pipeline nao expoe `classes_`; nao e possivel saber qual "
                "coluna de predict_proba corresponde ao churn."
            )

        disponiveis = [_chave(c) for c in classes]
        alvo = _chave(classe_churn)

        if alvo not in disponiveis:
            raise ErroDeCarregamento(
                f"classe_churn={classe_churn!r} nao esta em classes_={list(classes)!r}."
            )
        return disponiveis.index(alvo)

    def preparar(self, bruto: dict) -> dict:
        """Aplica o tratamento declarado e devolve as colunas do modelo.

        Levanta ErroDeDominio se um valor nao estiver no mapeamento. Converter
        por omissao seria pior que falhar: produziria uma predicao plausivel a
        partir de uma entrada que o modelo nunca viu.
        """
        preparado = {campo: valor for campo, valor in bruto.items() if campo not in self.ignorados}

        for campo, mapa in self.mapeamentos.items():
            if campo not in preparado:
                continue
            chave = _chave(preparado[campo])
            if chave not in mapa:
                esperados = ", ".join(str(k) for k in sorted(mapa, key=str))
                raise ErroDeDominio(
                    f"O atributo '{campo}' recebeu o valor {preparado[campo]!r}, "
                    f"que nao foi visto no treino. Valores aceitos: {esperados}."
                )
            preparado[campo] = mapa[chave]

        faltando = [campo for campo in self.atributos if campo not in preparado]
        if faltando:
            raise ErroDeDominio(
                "Atributos exigidos pelo modelo ausentes na requisicao: "
                + ", ".join(faltando)
            )

        return {campo: preparado[campo] for campo in self.atributos}

    def probabilidade(self, linha: dict) -> float:
        """Probabilidade de cancelamento para uma unica instancia."""
        import pandas as pd

        X = pd.DataFrame([linha], columns=self.atributos)
        return float(self.pipeline.predict_proba(X)[0][self.indice_churn])


# --------------------------------------------------------------- carregamento

_motor: Motor | None = None
_falha: str | None = None
_trava = threading.Lock()


def _chave(valor: Any) -> Any:
    """Normaliza chaves de comparacao entre JSON (texto) e payload (numero)."""
    if isinstance(valor, bool):
        return int(valor)
    if isinstance(valor, str):
        try:
            return int(valor)
        except ValueError:
            try:
                return float(valor)
            except ValueError:
                return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    return valor


def _conferir_bibliotecas(metadados: dict) -> None:
    """Avisa quando a versao de treino difere da versao instalada.

    Divergencia de versao maior do scikit-learn entre treino e inferencia
    muda resultado sem gerar erro, e e das causas mais dificeis de rastrear
    depois. O aviso fica no log da API.
    """
    import importlib.metadata as md

    for pacote, versao_treino in (metadados.get("bibliotecas") or {}).items():
        try:
            instalada = md.version(pacote)
        except md.PackageNotFoundError:
            logger.warning("Biblioteca %s usada no treino nao esta instalada na API.", pacote)
            continue

        if instalada.split(".")[0] != str(versao_treino).split(".")[0]:
            logger.warning(
                "Divergencia de versao maior em %s: treino %s, API %s. "
                "Conferir os casos de referencia antes da demonstracao.",
                pacote, versao_treino, instalada,
            )


def _diagnosticar_carga(caminho: Path, erro: Exception) -> str:
    """Traduz a falha de desserializacao na causa provavel.

    A mensagem original dizia sempre "divergencia de versao de scikit-learn",
    o que mandava quem lia para o lado errado quando a causa era outra. As
    causas abaixo foram todas observadas no projeto.
    """
    texto = str(erro)
    baixo = texto.lower()

    if "imblearn" in baixo or "imbalanced" in baixo:
        return (
            f"Nao foi possivel carregar {caminho.name}: {texto}\n"
            "CAUSA: o pipeline usa SMOTENC e o pacote imbalanced-learn nao esta "
            "instalado.\n"
            "SOLUCAO: pip install -r requirements.txt"
        )

    if "dll load failed" in baixo or "controle de aplicativo" in baixo or "application control" in baixo:
        return (
            f"Nao foi possivel carregar {caminho.name}: {texto}\n"
            "CAUSA: uma politica do Windows (Smart App Control ou antivirus) esta "
            "bloqueando uma biblioteca nativa, geralmente do SciPy. Nao e problema "
            "de versao nem do modelo.\n"
            "SOLUCAO: conferir se o venv foi criado com Python 3.12, a mesma versao "
            "do treino. Wheels recem-lancados costumam ser bloqueados por falta de "
            "reputacao. Ver api/README.md."
        )

    if "no module named" in baixo:
        return (
            f"Nao foi possivel carregar {caminho.name}: {texto}\n"
            "CAUSA: falta um pacote que o pipeline referencia.\n"
            "SOLUCAO: pip install -r requirements.txt"
        )

    return (
        f"Nao foi possivel carregar {caminho.name}: {texto}\n"
        "CAUSA PROVAVEL: divergencia entre a versao de scikit-learn do treino e a "
        "instalada aqui. O metadado registra as versoes do treino em "
        "`origem.versoes_do_treino`.\n"
        "SOLUCAO: conferir requirements.txt, que fixa as versoes de proposito."
    )


def carregar(forcar: bool = False) -> Motor:
    """Carrega o pacote do modelo. Idempotente e seguro entre requisicoes."""
    global _motor, _falha

    with _trava:
        if _motor is not None and not forcar:
            return _motor

        caminho_modelo = PASTA_ARTEFATOS / ARQUIVO_MODELO
        caminho_metadados = PASTA_ARTEFATOS / ARQUIVO_METADADOS

        for caminho in (caminho_modelo, caminho_metadados):
            if not caminho.exists():
                _falha = f"Arquivo nao encontrado: {caminho}"
                raise ErroDeCarregamento(
                    f"{_falha}. Conferir CHURNGUARD_ARTEFATOS e o pacote descrito "
                    "em ml/CONTRATO_MODELO.md."
                )

        try:
            import joblib
        except ImportError as erro:
            _falha = "joblib nao instalado"
            raise ErroDeCarregamento(
                "joblib nao esta instalado na API. Rodar: pip install -r requirements.txt"
            ) from erro

        metadados = json.loads(caminho_metadados.read_text(encoding="utf-8"))

        ausentes = [c for c in CAMPOS_OBRIGATORIOS if c not in metadados]
        if ausentes:
            _falha = f"metadados.json sem os campos {ausentes}"
            raise ErroDeCarregamento(
                f"metadados.json nao declara: {', '.join(ausentes)}. "
                "Ver ml/CONTRATO_MODELO.md, secao 4."
            )

        try:
            pipeline = joblib.load(caminho_modelo)
        except Exception as erro:
            _falha = f"falha ao desserializar o pipeline: {erro}"
            raise ErroDeCarregamento(_diagnosticar_carga(caminho_modelo, erro)) from erro

        if not hasattr(pipeline, "predict_proba"):
            _falha = "pipeline sem predict_proba"
            raise ErroDeCarregamento(
                "O pipeline exportado nao possui predict_proba. As faixas de risco "
                "derivam da probabilidade, entao ela e obrigatoria. Para SVM, "
                "exportar com probability=True ou via CalibratedClassifierCV."
            )

        _conferir_bibliotecas(metadados)

        explicador = _carregar_explicador(metadados, pipeline)
        motor = Motor(pipeline, metadados, explicador)

        _motor = motor
        _falha = None

        logger.info(
            "Modelo %s carregado de %s com %d atributos; explicacao: %s.",
            motor.versao, caminho_modelo, len(motor.atributos),
            (metadados.get("explicacao") or {}).get("tipo", "global"),
        )
        return motor


def _carregar_explicador(metadados: dict, pipeline: Any) -> Any:
    """Obtem o explicador SHAP, carregando de arquivo ou construindo na hora.

    Construir e o caminho preferido para modelos de arvore: `TreeExplainer`
    sai do proprio estimador em cerca de 15 ms e nao exige que a frente de
    classificacao serialize nada. Serializar um explicador e mais fragil, porque
    ele carrega uma referencia ao modelo e as vezes aos dados de fundo.

    A ausencia do explicador nao impede a API de responder: a camada de
    explicacao cai para a estrategia global declarada no metadado.
    """
    explicacao = metadados.get("explicacao") or {}
    if explicacao.get("tipo") != "tree":
        return None

    arquivo = explicacao.get("arquivo")
    if arquivo:
        caminho = PASTA_ARTEFATOS / arquivo
        if caminho.exists():
            try:
                import joblib
                explicador = joblib.load(caminho)
                logger.info("Explicador SHAP carregado de %s.", caminho)
                return explicador
            except Exception as erro:
                logger.warning(
                    "Falha ao carregar %s (%s); tentando construir a partir do modelo.",
                    caminho.name, erro,
                )
        else:
            logger.info(
                "Explicador %s nao encontrado; construindo a partir do modelo.",
                caminho.name,
            )

    try:
        import shap
    except ImportError:
        logger.warning(
            "shap nao instalado; usando a estrategia global. "
            "Rodar: pip install -r requirements.txt"
        )
        return None

    passos = getattr(pipeline, "steps", None)
    estimador = passos[-1][1] if passos else pipeline

    try:
        explicador = shap.TreeExplainer(estimador)
        logger.info(
            "Explicador SHAP construido a partir de %s.", type(estimador).__name__
        )
        return explicador
    except Exception as erro:
        logger.warning(
            "Nao foi possivel construir o TreeExplainer (%s); usando estrategia "
            "global. Se o modelo final nao for baseado em arvore, declarar "
            "explicacao.tipo = 'global' no metadado.", erro,
        )
        return None


def disponivel() -> bool:
    """Diz se o modelo real pode ser usado, sem levantar excecao."""
    if _motor is not None:
        return True
    try:
        carregar()
        return True
    except ErroDeCarregamento:
        return False


def situacao() -> dict:
    """Resumo para o endpoint /health, util na hospedagem."""
    if _motor is not None:
        explicacao = (_motor.metadados.get("explicacao") or {}).get("tipo", "global")
        return {
            "carregado": True,
            "modelo_versao": _motor.versao,
            "algoritmo": _motor.metadados.get("algoritmo"),
            "atributos": len(_motor.atributos),
            "explicacao": "local" if _motor.explicador is not None else explicacao,
            # Exposto porque foi a origem de um sinal invertido nos fatores: se
            # esta ordem nao for a que o estimador ve, os fatores saem trocados
            # sem nenhum erro aparecer.
            "ordem_da_explicacao": _motor.atributos_explicados,
        }
    return {"carregado": False, "motivo": _falha or "ainda nao carregado"}


# ---------------------------------------------------------------- inferencia

def prever(dados: PredictRequest) -> dict:
    """Mesma assinatura e mesmo formato de retorno de `stub.prever`."""
    import explicacao as camada_de_explicacao

    motor = carregar()
    bruto = dados.model_dump()

    linha = motor.preparar(bruto)
    probabilidade = motor.probabilidade(linha)

    fatores = camada_de_explicacao.calcular(motor, bruto, linha)

    return {
        "probabilidade": round(probabilidade, 4),
        "fatores": fatores,
        "modelo_versao": motor.versao,
    }