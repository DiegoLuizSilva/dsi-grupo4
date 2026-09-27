# Pacote do modelo servido pela API

A frente de classificação supervisionada vive em outro repositório,
**`pisi3-grupo4`**, com organização própria. A API deste repositório consome o
modelo dela. Este documento descreve a ponte entre os dois e o formato que a API
espera.

Responsável pelo modelo: Diego Luiz, em `pisi3-grupo4`.
Responsável pela integração: Lucas Guerra, aqui.

---

## 1. Onde o modelo é produzido

No `pisi3-grupo4`:

| Arquivo | Conteúdo |
|---|---|
| `models/modelo_final.joblib` | pipeline `imblearn` completo, já ajustado |
| `reports/tabelas/model_metadata.json` | algoritmo vencedor, critério, features, versões |
| `reports/tabelas/shap_metadata.json` | parâmetros da explicabilidade |
| `src/common.py` | `load_data()` e `preprocessor()` — onde as decisões de preparação vivem |

O modelo atual é **Random Forest com SMOTENC**, escolhido por F1 de churn médio
em validação cruzada agrupada de 5 folds (0,8687), sobre 2.517 registros de
treino e 633 de teste reservado.

---

## 2. Como importar

Não copie os arquivos à mão. O script faz a tradução e gera os casos de
referência:

```
cd ml
python importar_modelo.py --pisi ..\..\pisi3-grupo4
```

Ele produz em `ml/artefatos/`:

```
modelo.joblib               cópia do pipeline
metadados.json              traduzido para o formato que a API lê
casos_de_referencia.json    entradas com a probabilidade obtida do pipeline
```

Depois:

```
cd ..\api
python testar_predicao.py
```

Os casos de referência precisam reproduzir com diferença menor que `0,0001`.

### Por que o pacote é versionado aqui

`*.joblib` está no `.gitignore`, com **exceção** para `ml/artefatos/`. A exceção
é deliberada: o serviço de hospedagem constrói a imagem a partir do que está no
Git, então um artefato ignorado produziria uma imagem sem modelo. Além disso, o
artefato que gerou os números do artigo precisa estar versionado junto com a API
que o serve, senão não é possível reconstituir depois qual modelo gerou qual
número.

---

## 3. As três decisões que a API não pode adivinhar

`src/common.py`, em `load_data()`, faz três coisas **antes** de o pipeline
começar:

```python
X = original.drop(columns='age_group').copy()
for c in ['tariff_plan', 'status']:
    X[c] = X[c].map({1: 0, 2: 1})
```

| Decisão | Consequência para a API |
|---|---|
| `age_group` é descartada (determinada por `age`) | A API recebe o campo e não o repassa: o modelo usa **12** atributos, não 13 |
| `tariff_plan` mapeada de `{1,2}` para `{0,1}` | A API recebe 1 ou 2 e precisa converter |
| `status` mapeada de `{1,2}` para `{0,1}` | A API recebe 1 ou 2 e precisa converter |

### O que acontece se o mapeamento não for aplicado

Foi medido sobre os 3.150 registros da base, com o modelo atual:

| | Probabilidade média |
|---|---|
| Com o mapeamento | 0,1736 |
| Sem o mapeamento | 0,3674 |

**741 registros (23,5%) mudam de faixa de risco.** Um exemplo: o registro da
linha 25 vai de 0,025 (baixo) para 0,840 (alto) — um cliente que não cancelou
apareceria como risco alto na tela. E nada acusa erro: o modelo aceita 1 e 2
como valores válidos, porque são números plausíveis para aquela coluna.

Por isso o tratamento é **declarado** em `metadados.json` e executado pela API,
em vez de reimplementado no código dela. Duplicar a decisão em dois lugares
deixaria a API dessincronizada ao primeiro ajuste no notebook.

---

## 4. A reordenação das colunas

O ponto mais sutil, e o que causou um bug real durante a integração.

O `preprocessor()` de `src/common.py` monta um `ColumnTransformer` que escala os
nove atributos numéricos primeiro e passa os três binários depois. A ordem que o
estimador vê **não** é a ordem de `features`:

```
entrada (features):
  call_failure, complains, subscription_length, charge_amount, seconds_of_use,
  frequency_of_use, frequency_of_sms, distinct_called_numbers, tariff_plan,
  status, age, customer_value

saída do ColumnTransformer (o que o Random Forest vê):
  call_failure, subscription_length, charge_amount, seconds_of_use,
  frequency_of_use, frequency_of_sms, distinct_called_numbers, age,
  customer_value, complains, tariff_plan, status
```

O vetor SHAP segue a ordem de **saída**. Casá-lo com a ordem de entrada atribui
as contribuições aos atributos errados. Medido em um cliente com reclamação
registrada:

| Alinhamento | `shap(complains)` | O que a tela mostraria |
|---|---|---|
| Ordem de entrada (errado) | −0,046 | "reclamação **reduz** o risco" |
| Ordem de saída (correto) | +0,408 | "reclamação **aumenta** o risco" |

A probabilidade do mesmo cliente salta de 0,01 para 0,605 quando a reclamação
entra, o que confirma qual é a correta. Com o alinhamento errado, a tela diria
que a reclamação protege o cliente, com a probabilidade certa ao lado — o pior
tipo de erro, porque parece consistente.

`importar_modelo.py` descobre essa ordem por `get_feature_names_out()` e a
declara em `explicacao.atributos_transformados`. A API recusa carregar o pacote
se a contagem não fechar com o que o estimador espera, e
`testar_predicao.py` tem um teste dedicado a isso.

---

## 5. Formato de `metadados.json`

Gerado pelo script; esta seção documenta o que cada campo significa, para o caso
de precisar ajustar à mão.

```json
{
  "modelo_versao": "rf-smotenc-1.0",
  "algoritmo": "Random Forest | SMOTENC",
  "treinado_em": "2026-09-27",

  "atributos": ["call_failure", "complains", "...", "customer_value"],
  "atributos_ignorados": ["age_group"],
  "mapeamentos": {
    "tariff_plan": {"1": 0, "2": 1},
    "status": {"1": 0, "2": 1}
  },

  "classes": [0, 1],
  "classe_churn": 1,

  "explicacao": {
    "tipo": "tree",
    "arquivo": null,
    "atributos_transformados": ["call_failure", "subscription_length", "..."],
    "importancias": null,
    "referencias": { "call_failure": 8, "...": 0 }
  },

  "bibliotecas": { "scikit-learn": "1.8.0", "...": "..." },
  "sementes": { "seed_holdout": 42, "seed_cv": 43 },
  "origem": { "repositorio": "pisi3-grupo4", "...": "..." }
}
```

**`modelo_versao`** — aparece na resposta da API e fica gravado no histórico de
cada avaliação. Precisa mudar a cada reimportação. Sem isso não é possível
distinguir uma avaliação antiga de uma nova, e a Sprint 6 exige registrar a
versão usada na demonstração.

**`atributos`** — a ordem de entrada, em que a API monta o `DataFrame`.

**`atributos_ignorados`** — campos que a API recebe e não repassa. Hoje só
`age_group`.

**`mapeamentos`** — conversão por coluna. As chaves são texto porque JSON não
aceita chave numérica; a API converte. Valor fora do mapeamento é **recusado**
com 422, nunca convertido por omissão.

**`classe_churn`** — qual classe corresponde ao cancelamento. A API localiza a
posição dela em `pipeline.classes_`; nunca assume que é a coluna 1.

**`explicacao.tipo`** — `"tree"` faz a API construir o `shap.TreeExplainer` a
partir do estimador final no carregamento, em cerca de 15 ms. Não é preciso
serializar explicador nenhum, e é melhor assim: um explicador serializado carrega
referência ao modelo e às vezes aos dados de fundo, o que é mais frágil.
`"global"` usa `importancias` ponderadas pelo desvio — aproximação declarada, que
enfraquece a Seção 6.1 e só serve como rede de segurança.

**`explicacao.atributos_transformados`** — a ordem da seção 4. Se o pipeline não
reordenar, é igual a `atributos`.

**`explicacao.referencias`** — mediana de cada atributo, no domínio original. Só
é usada pela estratégia global.

**`bibliotecas`** — versões desta máquina. A API compara com o que está
instalado e avisa no log em divergência de versão maior, que muda resultado sem
gerar erro. O script também avisa, comparando com `versoes` do metadado de
origem.

---

## 6. Dependência obrigatória

O pipeline usa **SMOTENC**, de `imbalanced-learn`. Sem esse pacote instalado na
API, `joblib.load` falha com `ModuleNotFoundError: imblearn`. Está no
`api/requirements.txt`.

Um passo de reamostragem não é aplicado na inferência — `imblearn.Pipeline`
ignora o `sampler` em `predict_proba`, que é o comportamento correto. Ele precisa
estar instalado apenas para o objeto ser desserializado.

---

## 7. Quando o modelo for retreinado

1. No `pisi3-grupo4`, gerar o novo `models/modelo_final.joblib`
2. Aqui: `python importar_modelo.py --pisi <caminho> --versao rf-smotenc-1.1`
3. `cd ..\api && python testar_predicao.py`
4. Commitar os três arquivos de `ml/artefatos/`
5. Republicar, e conferir `modelo_versao` em `/health`

Nenhuma linha de Python da API muda em nenhum desses passos.

---

## 8. O que não entra no pacote

- **Nenhum resultado do stub ou do ensaio.** São encanamento de
  desenvolvimento e seus números não aparecem no artigo.
- **Nenhuma credencial** ou arquivo `.env`.
- **Nenhum modelo treinado com `age_group`**, salvo se a decisão de
  `src/common.py` for revista — e então `atributos` e `atributos_ignorados`
  mudam juntos.
