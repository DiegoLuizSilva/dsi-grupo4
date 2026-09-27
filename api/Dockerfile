# Imagem da API do ChurnGuard.
#
# Construir a partir da RAIZ do repositorio, nao de dentro de api/, porque o
# pacote do modelo fica em ml/artefatos/:
#
#     docker build -f api/Dockerfile -t churnguard-api .
#     docker run -p 8000:8000 --env-file api/.env churnguard-api
#
# A imagem nao contem credencial nenhuma. Tudo entra por variavel de ambiente
# em tempo de execucao.

FROM python:3.12-slim

# Nao gravar .pyc e nao usar buffer na saida, para que o log apareca na hora
# no painel do servico de hospedagem.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# As dependencias entram antes do codigo para aproveitar o cache de camadas:
# alterar um arquivo .py nao refaz a instalacao.
COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api/ ./api/

# O pacote do modelo, gerado por ml/importar_modelo.py a partir do repositorio
# pisi3-grupo4. Precisa estar VERSIONADO neste repositorio: o servico de
# hospedagem constroi a imagem a partir do que esta no Git, entao um artefato
# ignorado produz uma imagem sem modelo. O .gitignore tem a excecao.
#
# Se o pacote nao existir no momento do build, a API sobe normalmente e responde
# 503 na predicao, informando o motivo no /health.
COPY ml/artefatos/ ./ml/artefatos/

ENV CHURNGUARD_ARTEFATOS=/app/ml/artefatos \
    CHURNGUARD_EXIGIR_AUTENTICACAO=1 \
    CHURNGUARD_PERMITIR_STUB=0

# Usuario sem privilegios.
RUN useradd --create-home --shell /bin/false churnguard \
    && chown -R churnguard:churnguard /app
USER churnguard

WORKDIR /app/api

EXPOSE 8000

# `${PORT:-8000}` porque a maioria dos servicos de hospedagem escolhe a porta
# e a informa por variavel de ambiente.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
