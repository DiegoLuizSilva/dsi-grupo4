# Contrato da API do ChurnGuard

Versão 1.1 — Sprints 5 e 6

Este documento é a fonte da verdade sobre os campos trocados entre o aplicativo e a API. Qualquer alteração aqui precisa ser avisada no grupo antes de entrar na branch principal, porque quebra o app.

Base local: `http://localhost:8000`
Documentação interativa: `http://localhost:8000/docs`

---

## Estado atual

O endpoint `POST /predict` usa o Random Forest exportado de PISI3 quando o pacote em `ml/artefatos/` está disponível. Se o pacote faltar, pode responder pelo `stub-0.1` apenas em desenvolvimento. Em ambiente publicado, configurar `CHURNGUARD_PERMITIR_STUB=0` para devolver `503` em vez de apresentar uma predição simulada. Conferir `modelo_versao` e `/health` antes de usar qualquer resultado no artigo.

O formato da resposta continua o mesmo. As rotas de clientes e de predição agora exigem `Authorization: Bearer <token de identidade do Firebase>`; `/health` permanece público.

---

## Convenções

- Todos os campos em `snake_case`.
- As colunas originais do CSV têm espaço duplo em alguns nomes (`Call  Failure`, `Subscription  Length`, `Charge  Amount`). O aplicativo envia os nomes normalizados; o modelo recebe as 12 colunas na ordem declarada em `ml/artefatos/metadados.json`.
- `age_group` continua obrigatório no contrato de entrada, mas não é usado pelo classificador. `tariff_plan` e `status` são convertidos de `1/2` para `0/1` antes da inferência.
- Datas em ISO 8601, UTC.
- Campos inválidos retornam `422`; uma falha do pacote do modelo retorna `503` quando o stub está bloqueado.

---

## GET /health

Informa a versão da API, o motor carregado, o estado de inicialização do banco e as configurações de autenticação e stub. Deve ser consultado antes da demonstração.

```json
{ "status": "ok", "versao": "1.0.0", "modelo": { "carregado": true, "modelo_versao": "rf-smotenc-1.0" }, "banco": { "conectado": true }, "autenticacao_exigida": true, "stub_permitido": false }
```

---

## POST /predict

Avalia o risco de cancelamento de um cliente autenticado.

### Entrada

Todos os treze campos são obrigatórios.

| Campo | Tipo | Domínio | Significado |
|---|---|---|---|
| `call_failure` | inteiro | >= 0 | Falhas de chamada no período |
| `complains` | inteiro | 0 ou 1 | 0 sem reclamação, 1 com reclamação |
| `subscription_length` | inteiro | >= 0 | Meses de assinatura |
| `charge_amount` | inteiro | 0 a 10 | Faixa de cobrança, 0 menor, 10 maior |
| `seconds_of_use` | inteiro | >= 0 | Segundos totais de chamada |
| `frequency_of_use` | inteiro | >= 0 | Quantidade de chamadas |
| `frequency_of_sms` | inteiro | >= 0 | Quantidade de mensagens |
| `distinct_called_numbers` | inteiro | >= 0 | Números distintos acionados |
| `age_group` | inteiro | 1 a 5 | Faixa etária |
| `tariff_plan` | inteiro | 1 ou 2 | 1 pré-pago, 2 pós-pago |
| `status` | inteiro | 1 ou 2 | 1 ativo, 2 não ativo |
| `age` | inteiro | 0 a 120 | Idade |
| `customer_value` | decimal | >= 0 | Valor calculado do cliente |

Exemplo (primeira linha do dataset):

```json
{
  "call_failure": 8,
  "complains": 0,
  "subscription_length": 38,
  "charge_amount": 0,
  "seconds_of_use": 4370,
  "frequency_of_use": 71,
  "frequency_of_sms": 5,
  "distinct_called_numbers": 17,
  "age_group": 3,
  "tariff_plan": 1,
  "status": 1,
  "age": 30,
  "customer_value": 197.64
}
```

### Saída

```json
{
  "probabilidade": 0.01,
  "faixa": "baixo",
  "rotulo_faixa": "Risco baixo",
  "fatores": [
    {
      "campo": "frequency_of_use",
      "rotulo": "Frequencia de chamadas",
      "impacto": "reduz",
      "peso": 1.0,
      "sugestao": "Frequencia de uso saudavel"
    },
    {
      "campo": "status",
      "rotulo": "Situacao da linha",
      "impacto": "reduz",
      "peso": 0.9618,
      "sugestao": "Linha ativa"
    },
    {
      "campo": "complains",
      "rotulo": "Reclamacoes registradas",
      "impacto": "reduz",
      "peso": 0.4466,
      "sugestao": "Cliente sem reclamacoes no periodo"
    }
  ],
  "modelo_versao": "rf-smotenc-1.0",
  "gerado_em": "2026-09-29T14:01:06.054003Z"
}
```

| Campo | Tipo | Observação |
|---|---|---|
| `probabilidade` | decimal 0 a 1 | **Não exibir na tela.** Existe para registro e para o artigo |
| `faixa` | `baixo`, `medio`, `alto` | Use para escolher cor e ícone |
| `rotulo_faixa` | texto | **Exiba este texto.** Cumpre o RNF08, que proíbe depender só de cor |
| `fatores` | lista | Até três itens, ordenados por contribuição absoluta decrescente; fatores irrelevantes podem ser omitidos |
| `fatores[].campo` | texto | Nome técnico. Não exibir |
| `fatores[].rotulo` | texto | **Exiba este.** Nome legível do atributo |
| `fatores[].impacto` | `aumenta` ou `reduz` | Direção da contribuição |
| `fatores[].peso` | decimal 0 a 1 | Contribuição relativa ao maior fator. Serve para barra de proporção |
| `fatores[].sugestao` | texto | Ação de retenção sugerida, atende o HU08 |
| `modelo_versao` | texto | Identifica o motor usado; `stub-0.1` indica resultado simulado |
| `gerado_em` | data ISO | Momento da avaliação |

### Faixas de risco

Os pontos de corte são uma decisão do grupo, não vêm do dataset. O alvo `Churn` é binário e as três faixas derivam da probabilidade prevista.

| Faixa | Intervalo |
|---|---|
| `baixo` | menor que 0,30 |
| `medio` | de 0,30 a 0,65 |
| `alto` | maior que 0,65 |

Estão definidos em `api/faixas.py`, nas constantes `CORTE_BAIXO` e `CORTE_ALTO`. Precisam ser justificados no artigo.

---

## CRUD de clientes

| Método | Rota | Retorno |
|---|---|---|
| GET | `/clientes` | `200` com a lista |
| GET | `/clientes/{id}` | `200` ou `404` |
| POST | `/clientes` | `201` com identificador Firestore gerado pela API |
| PUT | `/clientes/{id}` | `200` com o cliente atualizado, `404` se não existir |
| DELETE | `/clientes/{id}` | `204` sem corpo, `404` se não existir |

Corpo do POST:

```json
{ "identificador": "CLI-001", "tariff_plan": 1, "observacao": "texto opcional" }
```

No PUT, envie apenas os campos que mudaram. A API associa os documentos criados por ela ao `uid` da conta autenticada e impede a troca de `proprietario` pela requisição.

---

## Persistência e responsabilidades

O Cloud Firestore é a fonte de dados do sistema. O aplicativo executa o CRUD
de clientes diretamente na coleção `clientes` pelo SDK cliente do Firebase. A
API também expõe endpoints de CRUD sobre essa coleção pelo Firebase Admin e
mantém o endpoint `POST /predict` para a avaliação de risco.

As contas são autenticadas pelo Firebase Authentication. O perfil de cada
pessoa usuária fica em `pessoas/{uid}`, usando o identificador da conta como
identificador do documento. As regras do arquivo `firestore.rules` restringem
os perfis aos respectivos usuários. As regras locais de clientes ainda permitem
CRUD compartilhado entre contas autenticadas no acesso direto do aplicativo,
enquanto os endpoints da API restringem clientes pelo campo `proprietario`.
Esses dois caminhos precisam ser alinhados antes de afirmar que a carteira é
privada por conta em todo o sistema.

A configuração atual depende de conexão com a internet. O aplicativo ainda não
oferece o funcionamento offline descrito nas versões antigas dos requisitos.
