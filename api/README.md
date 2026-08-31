# API do ChurnGuard

Serviço em Python (FastAPI) que expõe o CRUD de clientes e a avaliação de risco de cancelamento.

O contrato dos campos está em [CONTRATO.md](CONTRATO.md). Comece por ele.

## Rodando localmente

```bash
cd api
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000/docs` para a documentação interativa. Dá para testar todos os endpoints por ali, sem Postman e sem o app.

O `--host 0.0.0.0` é necessário para o celular alcançar a API pela rede local.

## Estrutura

```
api/
├── main.py          Ponto de entrada, CORS e registro das rotas
├── schemas.py       Contratos de entrada e saída (Pydantic)
├── faixas.py        Pontos de corte das faixas e tradução dos atributos
├── stub.py          Substituto do modelo, trocado na Sprint 5
├── db.py            Acesso ao SQLite
└── routers/
    ├── clientes.py  CRUD
    └── predict.py   Avaliação de risco
```

## O que muda na Sprint 5

O arquivo `routers/predict.py` tem uma linha marcada:

```python
_motor = stub.prever
```

Quando o modelo estiver treinado, cria-se um `modelo.py` que carrega o arquivo `.joblib`, expõe uma função `prever(dados)` com a mesma assinatura e o mesmo retorno, e troca-se a linha por `_motor = modelo.prever`.

Nada mais precisa mudar. O app não é afetado.

## Banco

O arquivo `churnguard.db` é criado automaticamente na primeira execução e está no `.gitignore`. Não versionar.
