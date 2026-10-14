# Registro de testes

Este documento reúne as falhas encontradas durante a integração e a publicação da API, cada uma com reprodução, correção e reteste, e o histórico de execuções das baterias de teste. Os relatórios gerados automaticamente ficam em `docs/evidencias/`.

## Baterias de teste

| Script | Onde roda | O que cobre | Verificações |
|---|---|---|---|
| `api/testar_predicao.py` | máquina local | faixas, carregamento, preparação da entrada, domínio, fatores, alinhamento das colunas, sinal da explicação, consistência com os casos de referência, determinismo, tempo, autorização, política da carteira | 79 |
| `api/testar_falhas.py` | máquina local | modelo indisponível, stub identificado, troca do modelo sem reiniciar, banco indisponível, erro inesperado, erro de domínio | 12 |
| `api/testar_api_publicada.py` | contra o endereço publicado | estado do serviço, recusa sem token, token inválido, leitura autenticada, casos de referência, entradas inválidas, determinismo, estabilidade | 30 |

## Falhas encontradas e corrigidas

### F-01. Codificação de plano tarifário e situação da linha não aplicada

- **Falha:** o treino (repositório pisi3-grupo4, `load_data`) converte `tariff_plan` e `status` de 1/2 para 0/1. A primeira versão da API enviava os valores originais ao modelo.
- **Reprodução:** prever toda a base com e sem a conversão e comparar as faixas. Sem a conversão, 741 dos 3.150 registros mudam de faixa de risco.
- **Correção:** a conversão passou a ser declarada em `ml/artefatos/metadados.json` (campo `mapeamentos`) e executada pela API em `modelo.preparar()`, sem regra escrita no código da API.
- **Reteste:** os casos de referência cobrem as quatro combinações de plano e situação da linha; se a conversão deixar de ser aplicada, algum deles muda de faixa e o teste falha. Passa em `testar_predicao.py` e em `testar_api_publicada.py` (T05.2 a T05.5).

### F-02. Fatores explicativos com sinal invertido

- **Falha:** o `ColumnTransformer` do pipeline reordena as colunas (numéricas escalonadas primeiro, `complains`, `tariff_plan` e `status` ao final). Os valores SHAP saem na ordem que o estimador vê, mas eram associados aos nomes na ordem de entrada.
- **Reprodução:** para um cliente com reclamação registrada, a contribuição de `complains` aparecia como −0,046 (reduz o risco), quando o valor correto era +0,408 (aumenta o risco). Nenhum erro era lançado.
- **Correção:** a API passou a obter a ordem pós-transformação com `get_feature_names_out()` (`Motor.atributos_explicados`) e a declará-la em `metadados.json`. A ordem fica exposta em `/health`, no campo `ordem_da_explicacao`.
- **Reteste:** testes dedicados de alinhamento das colunas e de sinal da explicação em `testar_predicao.py`, que falham com a versão anterior e passam com a corrigida.

### F-03. Dependência `imbalanced-learn` ausente

- **Falha:** o pipeline treinado usa `SMOTENC` do `imbalanced-learn`. Sem a biblioteca instalada, a API não conseguia desserializar o modelo.
- **Reprodução:** instalar a partir do `requirements.txt` original e iniciar a API; `/health` mostrava `carregado: false` com erro de módulo `imblearn` não encontrado.
- **Correção:** `imbalanced-learn==0.14.2` declarado no `requirements.txt`, e `modelo._diagnosticar_carga()` passou a dizer qual pacote falta.
- **Reteste:** instalação limpa seguida de `/health` com `carregado: true`.

### F-04. Driver do Firestore removido por reinstalação

- **Falha:** depois de uma reinstalação forçada das dependências, o pacote `google-cloud-firestore`, que vinha apenas como dependência indireta, deixou de estar presente e o banco não inicializava.
- **Reprodução:** `pip install --force-reinstall -r requirements.txt` seguido de `/health` com `banco.conectado: false`.
- **Correção:** `google-cloud-firestore` declarado explicitamente no `requirements.txt`.
- **Reteste:** `/health` com `banco.conectado: true` após instalação limpa.

### F-05. Bloqueio de bibliotecas pelo Controle Inteligente de Aplicativos do Windows

- **Falha:** em uma máquina com Windows 11, Python 3.14 e scikit-learn 1.9.1, o sistema bloqueou o carregamento de extensões compiladas do SciPy e do scikit-learn, e a mensagem de erro da API atribuía a falha ao scikit-learn.
- **Reprodução:** `import sklearn` falhava com erro de DLL bloqueada por política de controle de aplicativo.
- **Correção:** ambiente fixado em Python 3.12 com as mesmas versões do treino (scikit-learn 1.8.0, numpy 2.3.5, pandas 2.3.3, imbalanced-learn 0.14.2, shap 0.52.0). A mensagem de diagnóstico passou a identificar o bloqueio por política do sistema.
- **Reteste:** instalação na mesma máquina com as versões fixadas; `testar_predicao.py` com todas as verificações passando.

### F-06. Teste do endpoint dependente de variável de ambiente

- **Falha:** o teste do endpoint de predição recebia 401 quando a variável `CHURNGUARD_EXIGIR_AUTENTICACAO` não estava definida na máquina, porque a autenticação é exigida por padrão.
- **Reprodução:** rodar `testar_predicao.py` em um terminal novo, sem a variável.
- **Correção:** o próprio teste passou a controlar a variável durante a execução e a restaurá-la ao final.
- **Reteste:** execução em terminal limpo com todas as verificações passando.

### F-07. Política de acesso divergente entre API e regras do Firestore

- **Falha:** a API filtrava clientes por `proprietario`, enquanto `firestore.rules` liberava a carteira inteira para qualquer conta autenticada. Como o aplicativo lê os clientes direto do Firestore, valia a regra mais permissiva e o sistema afirmava uma privacidade que não tinha.
- **Reprodução:** duas contas distintas; a segunda via no aplicativo os clientes cadastrados pela primeira, embora a API dissesse que não.
- **Correção:** decisão de domínio pela carteira compartilhada, aplicada igualmente na API e nas regras. O campo `proprietario` passou a registrar autoria, sem restringir acesso.
- **Reteste:** teste de política da carteira em `testar_predicao.py`.

## Histórico de execuções

Acrescentar uma linha a cada execução relevante. O relatório completo de cada uma fica em `docs/evidencias/`.

| Data | Script | Ambiente | Resultado | Relatório |
|---|---|---|---|---|
| | `testar_predicao.py` | local | /79 | saída do terminal |
| | `testar_falhas.py` | local | /12 | `docs/evidencias/teste_falhas_...md` |
| | `testar_api_publicada.py` | Render | /30 | `docs/evidencias/teste_api_publicada_...md` |
| | instalação seguindo o README | outra máquina | | descrever abaixo |

## Instalação em outra máquina

Registro da verificação de que o README é suficiente para colocar o sistema de pé a partir de um clone limpo.

- Data:
- Quem executou e em qual máquina:
- Passos do README que funcionaram sem ajuste:
- Passos que precisaram de ajuste (e o que foi corrigido no README):
- Resultado de `testar_predicao.py` nessa máquina: