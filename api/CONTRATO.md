# Contrato da API do ChurnGuard

Versão 1.0 — Sprint 2

Este documento é a fonte da verdade sobre os campos trocados entre o aplicativo e a API. Qualquer alteração aqui precisa ser avisada no grupo antes de entrar na branch principal, porque quebra o app.

Base local: `http://localhost:8000`
Documentação interativa: `http://localhost:8000/docs`

---

## Estado atual

O endpoint `POST /predict` responde a partir de um substituto (`stub`), não do modelo treinado. O campo `modelo_versao` devolve `stub-0.1` e é assim que se identifica isso.

Na Sprint 5 o stub é trocado pelo modelo real. **O formato da resposta não muda.** Só o valor de `modelo_versao` passa a identificar o modelo treinado. O app não precisa de nenhuma alteração por causa dessa troca.

---

## Convenções

- Todos os campos em `snake_case`.
- As colunas originais do CSV têm espaço duplo em alguns nomes (`Call  Failure`, `Subscription  Length`, `Charge  Amount`). A normalização é responsabilidade da API. O app nunca vê os nomes originais.
- Datas em ISO 8601, UTC.
- Erros de validação retornam `422` com a lista de campos inválidos, formato padrão do FastAPI.

---

## GET /health

Verifica se a API está de pé. Útil para o app mostrar aviso de serviço indisponível.

```json
{ "status": "ok", "versao": "0.1.0" }
```

---

## POST /predict

Avalia o risco de cancelamento de um cliente.

### Entrada

Todos os treze campos são obrigatórios.

| Campo | Tipo | Domínio | Significado |
|---|---|---|---|
| `call_failure` | inteiro | >= 0 | Falhas de chamada no período |
| `complains` | inteiro | 0 ou 1 | 0 sem reclamação, 1 com reclamação |
| `subscription_length` | inteiro | >= 0 | Meses de assinatura |
| `charge_amount` | inteiro | 0 a 9 | Faixa de cobrança, 0 menor, 9 maior |
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
  "probabilidade": 0.2977,
  "faixa": "baixo",
  "rotulo_faixa": "Risco baixo",
  "fatores": [
    {
      "campo": "seconds_of_use",
      "rotulo": "Tempo total de uso",
      "impacto": "reduz",
      "peso": 1.0,
      "sugestao": "Uso consistente, manter o plano atual"
    }
  ],
  "modelo_versao": "stub-0.1",
  "gerado_em": "2026-08-31T14:01:06.054003Z"
}
```

| Campo | Tipo | Observação |
|---|---|---|
| `probabilidade` | decimal 0 a 1 | **Não exibir na tela.** Existe para registro e para o artigo |
| `faixa` | `baixo`, `medio`, `alto` | Use para escolher cor e ícone |
| `rotulo_faixa` | texto | **Exiba este texto.** Cumpre o RNF08, que proíbe depender só de cor |
| `fatores` | lista | Sempre três itens, ordenados por contribuição decrescente |
| `fatores[].campo` | texto | Nome técnico. Não exibir |
| `fatores[].rotulo` | texto | **Exiba este.** Nome legível do atributo |
| `fatores[].impacto` | `aumenta` ou `reduz` | Direção da contribuição |
| `fatores[].peso` | decimal 0 a 1 | Contribuição relativa ao maior fator. Serve para barra de proporção |
| `fatores[].sugestao` | texto | Ação de retenção sugerida, atende o HU08 |
| `modelo_versao` | texto | `stub-0.1` até a Sprint 5 |
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
| POST | `/clientes` | `201` com o cliente criado, `409` se o identificador já existir |
| PUT | `/clientes/{id}` | `200` com o cliente atualizado, `404` se não existir |
| DELETE | `/clientes/{id}` | `204` sem corpo, `404` se não existir |

Corpo do POST:

```json
{ "identificador": "CLI-001", "tariff_plan": 1, "observacao": "texto opcional" }
```

No PUT, envie apenas os campos que mudaram. `identificador` não é alterável.

---

## Pendência a decidir no grupo

O aplicativo mantém a própria base local em `expo-sqlite`, e a API mantém uma base própria em SQLite. Hoje as duas existem em paralelo e não conversam.

O documento de requisitos exige, no RNF05, que o CRUD funcione sem conexão. Isso obriga a base local a existir. A questão em aberto é se a base da API passa a ser a fonte da verdade quando há conexão, com sincronização, ou se ela permanece apenas como demonstração dos endpoints REST.

Enquanto a decisão não for tomada, o app deve usar a base local para o CRUD e a API apenas para `POST /predict`.
