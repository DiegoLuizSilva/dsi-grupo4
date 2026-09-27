# API do ChurnGuard

Serviço em Python (FastAPI) que expõe o CRUD de clientes, a avaliação de risco de cancelamento e a verificação de sessão.

O contrato dos campos está em [CONTRATO.md](CONTRATO.md). O formato do pacote do modelo está em [../ml/CONTRATO_MODELO.md](../ml/CONTRATO_MODELO.md).

## Rodando localmente

```bash
cd api
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000/docs` para a documentação interativa.

O `--host 0.0.0.0` é necessário para o celular alcançar a API pela rede local. No aparelho, o endereço é o IP da máquina na rede, não `localhost` — `localhost` no celular aponta para o próprio celular.

### Antes da primeira execução

**1. Credencial do Firebase.** Baixe o JSON da conta de serviço no console do Firebase (Configurações do projeto → Contas de serviço → Gerar nova chave privada) e salve como `api/serviceAccountKey.json`. O arquivo está no `.gitignore` e **não pode ser versionado**.

Conferir que é o **mesmo projeto Firebase** que o aplicativo usa em `app/src/database/firebaseConfig.ts`. Projetos diferentes fazem a API recusar todo token com "Token de autenticação inválido", sem nenhuma pista do motivo real.

**2. Configuração.** Copie `.env.example` para `.env`. Para desenvolvimento os padrões já servem; o arquivo documenta cada variável.

**3. Testar sem token.** As rotas exigem token de identidade do Firebase. Para exercitar o CRUD pelo `/docs` sem passar pelo aplicativo:

```bash
CHURNGUARD_EXIGIR_AUTENTICACAO=0 uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Nesse modo tudo responde como a conta fictícia `desenvolvimento-local`, e o log avisa em cada requisição. **Nunca usar em ambiente publicado.**

## Estrutura

```
api/
├── main.py             Ponto de entrada, CORS, /health e registro das rotas
├── schemas.py          Contratos de entrada e saída (Pydantic)
├── faixas.py           Pontos de corte das faixas e tradução dos atributos
├── seguranca.py        Verificação do token e restrição por conta
├── modelo.py           Carregamento do modelo treinado e inferência
├── explicacao.py       Cálculo dos três fatores (SHAP local ou global)
├── stub.py             Substituto do modelo, usado só em desenvolvimento
├── db.py               Acesso ao Firestore (Firebase Admin)
├── testar_predicao.py  Testes de integração do motor e das rotas
├── Dockerfile          Imagem para hospedagem
└── routers/
    ├── clientes.py     CRUD restrito à conta autenticada
    └── predict.py      Avaliação de risco
```

## Verificando o estado do serviço

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "versao": "1.0.0",
  "modelo": {
    "carregado": true,
    "modelo_versao": "rf-1.0",
    "algoritmo": "RandomForestClassifier",
    "atributos": 12,
    "explicacao": "local"
  },
  "banco": { "conectado": true },
  "autenticacao_exigida": true,
  "stub_permitido": false
}
```

**Conferir este endpoint antes de qualquer demonstração ou de coletar resultado para o artigo.** Se `modelo_versao` começa com `stub` ou `ensaio`, o número que apareceu na tela não vale como resultado.

## Motor de predição

O `/predict` responde pelo modelo treinado, carregado por `modelo.py` a partir de `ml/artefatos/`. O pacote e o formato dos metadados estão especificados em [../ml/CONTRATO_MODELO.md](../ml/CONTRATO_MODELO.md).

Nenhuma decisão de pré-processamento está escrita no código da API. O `metadados.json` declara quais atributos o modelo usa, em que ordem, quais campos são descartados e quais valores precisam ser convertidos; a API executa a declaração. Ajustar o encoding é alterar o metadado, não o Python.

### Trocar o artefato

1. Colocar `modelo.joblib`, `metadados.json` e `casos_de_referencia.json` em `ml/artefatos/`, com `modelo_versao` novo.
2. Rodar `python testar_predicao.py`. Os casos de referência precisam ser reproduzidos com diferença menor que `0,0001`.
3. Reiniciar o serviço, ou apenas chamar `/predict`: o motor é resolvido por requisição, então o artefato novo passa a valer sem reinício.
4. Conferir `modelo_versao` em `/health`.

### Quando o modelo não está presente

Sem pacote em `ml/artefatos/`, a API cai para `stub.py` em desenvolvimento, para não bloquear as frentes de aplicativo. A resposta se identifica como `stub-0.1`, e o log avisa em cada requisição.

Em ambiente publicado, `CHURNGUARD_PERMITIR_STUB=0` faz a API responder **503** em vez de cair para o stub. Isso evita uma demonstração acidental sem modelo.

**Nenhum número produzido pelo stub entra no artigo.**

### De onde vem o modelo

O modelo é produzido no repositório **`pisi3-grupo4`**, em `models/modelo_final.joblib`. Para importá-lo:

```bash
cd ml
python importar_modelo.py --pisi ../../pisi3-grupo4
```

O script traduz o metadado dele para o formato que a API lê, descobre a ordem das colunas após a transformação e gera os casos de referência chamando o pipeline diretamente. Detalhes em [../ml/CONTRATO_MODELO.md](../ml/CONTRATO_MODELO.md).

O pacote em `ml/artefatos/` **é versionado** — exceção deliberada à regra `*.joblib` do `.gitignore`, porque o serviço de hospedagem constrói a imagem a partir do que está no Git.

### Artefato de ensaio

Para exercitar o caminho completo sem o modelo real (por exemplo, ao testar uma mudança na API):

```bash
cd ml
python gerar_artefato_de_ensaio.py
```

Gera um pacote identificado como `ensaio-0.1`. Não tem protocolo de validação, balanceamento nem ajuste de hiperparâmetros, e seus números não valem para nada além do teste do encanamento. O `.gitignore` impede que ele seja commitado.

## Testes

```bash
cd api
python testar_predicao.py
```

Cobre faixas de risco nos limites, carregamento do pacote, tratamento declarado da entrada, valor fora do domínio, campo ausente, ordenação e sinal dos fatores, consistência com os casos de referência, determinismo, tempo de resposta, falha de carregamento e autorização das rotas.

Saída esperada: todas as linhas com `ok`.

## Autorização

Toda rota de dados e a de predição exigem o token de identidade do Firebase no cabeçalho:

```
Authorization: Bearer <token>
```

O aplicativo envia automaticamente, em `app/src/services/api.ts`. A verificação acontece no **servidor**: o aplicativo saber quem está logado não protege nada, porque a API pode ser chamada direto, sem passar por ele.

Cada documento da coleção `clientes` guarda `proprietario` com o `uid` de quem o criou. A listagem filtra por esse campo e as demais operações conferem o dono antes de responder. Acesso a registro de outra conta devolve **404**, não 403: responder 403 confirmaria que aquele identificador existe em outra conta.

`/health` fica aberto de propósito, para monitoramento.

### Registros anteriores a esta mudança

Documentos gravados antes da autorização não têm o campo `proprietario`. Eles continuam visíveis, por compatibilidade, e a API registra um aviso no log. **Migrar ou apagar antes da entrega final** — um documento sem dono é visível para qualquer conta.

Para atribuir os registros existentes a uma conta:

```python
# Rodar uma vez, com a API parada.
import db
uid = "COLE_AQUI_O_UID_DA_CONTA"

banco = db.obter_db()
for doc in banco.collection("clientes").stream():
    if "proprietario" not in doc.to_dict():
        doc.reference.update({"proprietario": uid})
        print("atualizado:", doc.id)
```

## Hospedagem

A imagem é construída a partir da **raiz do repositório**, porque o pacote do modelo fica em `ml/artefatos/`:

```bash
docker build -f api/Dockerfile -t churnguard-api .
docker run -p 8000:8000 --env-file api/.env churnguard-api
```

Em serviço de hospedagem, configurar como variáveis de ambiente:

| Variável | Valor |
|---|---|
| `FIREBASE_CREDENCIAL_JSON` | o JSON da conta de serviço, em uma linha |
| `CHURNGUARD_EXIGIR_AUTENTICACAO` | `1` |
| `CHURNGUARD_PERMITIR_STUB` | `0` |
| `CHURNGUARD_ORIGENS` | origens do navegador, separadas por vírgula |
| `CHURNGUARD_ARTEFATOS` | `/app/ml/artefatos` |

Nenhuma credencial entra na imagem. Nenhum `.env` é versionado.

Depois de publicar, no aplicativo: definir `EXPO_PUBLIC_API_URL` com o endereço do serviço, em `app/.env`.

### Conferir depois de publicar

```bash
# 1. O serviço está de pé e com o modelo certo?
curl https://SEU-ENDERECO/health

# 2. As rotas estão protegidas? Ambas precisam devolver 401.
curl -i https://SEU-ENDERECO/clientes
curl -i -X POST https://SEU-ENDERECO/predict -H 'Content-Type: application/json' -d '{}'
```

Se o `GET /clientes` devolver a lista de clientes sem token, **não demonstrar**: a base está aberta.

## Banco de dados

Firestore, pelo Firebase Admin. Não há SQLite e não há funcionamento offline — o modelo não roda no aparelho, então a avaliação de risco depende da API estar alcançável.

Duas coleções, que não devem ser confundidas:

| Coleção | Conteúdo |
|---|---|
| `pessoas` | quem **usa** o aplicativo: `uid`, nome, e-mail |
| `clientes` | os assinantes **avaliados** pelo ChurnGuard, com `proprietario` |
