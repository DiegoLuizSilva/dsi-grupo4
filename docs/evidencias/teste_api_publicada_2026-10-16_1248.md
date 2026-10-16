# Teste da API publicada

- Data: 16/10/2026 12:48
- Endereço: `https://dsi-grupo4.onrender.com`
- Modelo: `rf-smotenc-1.0` (Random Forest | SMOTENC), explicação `local`
- Conta usada: `demo.gestor1@example.com`
- Máquina que executou: Windows 11, Python 3.12.10
- Script: `api/testar_api_publicada.py`

**Resultado: 30 de 30 verificações passaram.**

Primeira resposta (inclui o serviço acordar): 1.1 s. Mediana das demais: 267 ms.

| Código | Cenário | Esperado | Obtido | Tempo | Resultado |
|---|---|---|---|---|---|
| T01.1 | /health responde (inclui o tempo para acordar) | HTTP 200 | HTTP 200 | 1058 ms | passou |
| T01.2 | modelo treinado carregado | carregado=true | carregado=True versao=rf-smotenc-1.0 motivo=- | - | passou |
| T01.3 | explicacao local (SHAP) ativa | explicacao=local | explicacao=local | - | passou |
| T01.4 | banco conectado | conectado=true | conectado=True motivo=- | - | passou |
| T01.5 | autenticacao exigida no ambiente publicado | autenticacao_exigida=true | autenticacao_exigida=True | - | passou |
| T01.6 | stub de desenvolvimento desligado | stub_permitido=false | stub_permitido=False | - | passou |
| T02.1 | GET /clientes sem token | HTTP 401 | HTTP 401 {"detail":"Envie o token de identidade no cabecalho Authorization: Bearer <token>."} | 252 ms | passou |
| T02.2 | POST /predict sem token | HTTP 401 | HTTP 401 {"detail":"Envie o token de identidade no cabecalho Authorization: Bearer <token>."} | 325 ms | passou |
| T02.3 | POST /clientes sem token | HTTP 401 | HTTP 401 {"detail":"Envie o token de identidade no cabecalho Authorization: Bearer <token>."} | 255 ms | passou |
| T03.1 | token inventado | HTTP 401 | HTTP 401 {"detail":"Token de autenticacao invalido."} | 267 ms | passou |
| T03.2 | token com formato de JWT mas assinatura falsa | HTTP 401 | HTTP 401 {"detail":"Token de autenticacao invalido."} | 267 ms | passou |
| T03.3 | cabecalho sem o prefixo Bearer | HTTP 401 | HTTP 401 {"detail":"Envie o token de identidade no cabecalho Authorization: Bearer <token>."} | 257 ms | passou |
| T04.1 | GET /clientes com token valido | HTTP 200 com lista | HTTP 200, 12 clientes | 2166 ms | passou |
| T05.1 | Cobranca na faixa 10, extremo do dominio | faixa=baixo p=0.0000 3 fatores | faixa=baixo p=0.0000 3 fatores (status, frequency_of_use, seconds_of_use) | 610 ms | passou |
| T05.2 | Plano 1, situacao da linha 1 | faixa=baixo p=0.0100 3 fatores | faixa=baixo p=0.0100 3 fatores (frequency_of_use, status, complains) | 488 ms | passou |
| T05.3 | Plano 1, situacao da linha 2 | faixa=baixo p=0.0300 3 fatores | faixa=baixo p=0.0300 3 fatores (call_failure, age, status) | 409 ms | passou |
| T05.4 | Plano 2, situacao da linha 1 | faixa=baixo p=0.0200 3 fatores | faixa=baixo p=0.0200 3 fatores (complains, seconds_of_use, frequency_of_use) | 394 ms | passou |
| T05.5 | Plano 2, situacao da linha 2 | faixa=alto p=0.9400 3 fatores | faixa=alto p=0.9400 3 fatores (complains, frequency_of_use, status) | 812 ms | passou |
| T05.6 | Registro de risco medio | faixa=medio p=0.3188 3 fatores | faixa=medio p=0.3188 3 fatores (status, complains, call_failure) | 482 ms | passou |
| T05.7 | Registro de risco alto | faixa=alto p=0.7583 3 fatores | faixa=alto p=0.7583 3 fatores (status, frequency_of_use, seconds_of_use) | 415 ms | passou |
| T06.1 | campo obrigatorio ausente (complains) | HTTP 422 | HTTP 422 {"detail":[{"type":"missing","loc":["body","complains"],"msg":"Field required","input":{"call_failure":25,"subscription_length":36,"charge_amount":10,"seconds_o... | 248 ms | passou |
| T06.2 | faixa de cobranca acima de 10 | HTTP 422 | HTTP 422 {"detail":[{"type":"less_than_equal","loc":["body","charge_amount"],"msg":"Input should be less than or equal to 10","input":11,"ctx":{"le":10}}]} | 270 ms | passou |
| T06.3 | reclamacao com valor 2 | HTTP 422 | HTTP 422 {"detail":[{"type":"less_than_equal","loc":["body","complains"],"msg":"Input should be less than or equal to 1","input":2,"ctx":{"le":1}}]} | 263 ms | passou |
| T06.4 | idade negativa | HTTP 422 | HTTP 422 {"detail":[{"type":"greater_than_equal","loc":["body","age"],"msg":"Input should be greater than or equal to 0","input":-5,"ctx":{"ge":0}}]} | 237 ms | passou |
| T06.5 | plano tarifario 3 | HTTP 422 | HTTP 422 {"detail":[{"type":"less_than_equal","loc":["body","tariff_plan"],"msg":"Input should be less than or equal to 2","input":3,"ctx":{"le":2}}]} | 253 ms | passou |
| T06.6 | texto em campo numerico | HTTP 422 | HTTP 422 {"detail":[{"type":"int_parsing","loc":["body","seconds_of_use"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"muito"}]... | 262 ms | passou |
| T06.7 | corpo vazio | HTTP 422 | HTTP 422 {"detail":[{"type":"missing","loc":["body","call_failure"],"msg":"Field required","input":{}},{"type":"missing","loc":["body","complains"],"msg":"Field required... | 254 ms | passou |
| T06.8 | JSON quebrado | HTTP 422 | HTTP 422 {"detail":[{"type":"json_invalid","loc":["body",1],"msg":"JSON decode error","input":{},"ctx":{"error":"Expecting property name enclosed in double quotes"}}]} | 240 ms | passou |
| T07.1 | tres chamadas iguais, mesmo resultado | 3 respostas identicas | 1 resultado(s) distinto(s) em 3 | - | passou |
| T08.1 | /health depois das entradas invalidas | HTTP 200, modelo carregado | HTTP 200, modelo carregado | 235 ms | passou |

## Fora do escopo deste teste

Modelo indisponível e banco indisponível não são provocados no ambiente publicado, porque isso exigiria derrubá-lo. Ambos são verificados localmente por `api/testar_falhas.py` e registrados em `docs/REGISTRO_DE_TESTES.md`.
