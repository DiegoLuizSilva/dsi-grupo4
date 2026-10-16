# Registro de testes

Este documento reúne as falhas encontradas durante a integração e a publicação da API, cada uma com reprodução, correção e reteste, e o histórico de execuções das baterias de teste. Os relatórios gerados automaticamente ficam em `docs/evidencias/`.

## Baterias de teste

| Script | Onde roda | O que cobre | Verificações |
|---|---|---|---|
| `api/testar_predicao.py` | máquina local | faixas, carregamento, preparação da entrada, domínio, fatores, alinhamento das colunas, sinal da explicação, consistência com os casos de referência, determinismo, tempo, autorização, política da carteira, sugestões coerentes com o valor | 86 |
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

### F-08. Ambiente publicado desatualizado em relação ao repositório

- **Falha:** o serviço no Render continuava no commit `ed438f1`, cinco commits atrás da API no repositório. Faltavam as versões fixadas, a declaração do `google-cloud-firestore` e a política de carteira compartilhada, então a API publicada ainda filtrava clientes por dono, divergindo de `firestore.rules`.
- **Reprodução:** comparar o commit exibido no painel do Render com o último commit da branch `main`.
- **Correção:** nova publicação manual do último commit. A conferência do commit publicado passou a fazer parte da preparação de qualquer demonstração (`docs/RECUPERACAO_E_DEMONSTRACAO.md`, seção 3).
- **Reteste:** `testar_api_publicada.py` contra `https://dsi-grupo4.onrender.com`, 30/30 em 14/10/2026 (`docs/evidencias/teste_api_publicada_2026-10-14_0935.md`).

### F-09. Explicação SHAP bloqueada no Windows, com diagnóstico enganoso

- **Falha:** em Windows 11 com o Controle Inteligente de Aplicativos ativo, o `shap` instala normalmente, mas o sistema bloqueia uma biblioteca nativa do `numba`, da qual ele depende (`_devicearray`). A API caía para a explicação global e registrava "shap nao instalado", mandando reinstalar, o que não resolve.
- **Reprodução:** clone limpo, venv novo, `pip install -r requirements.txt` sem erro e `python testar_predicao.py`. O log mostra `DLL load failed while importing _devicearray: Uma política de Controle de Aplicativo bloqueou este arquivo`, seguido de "shap nao instalado", e `/health` informa `explicacao: tree` em vez de `local`.
- **Correção:** `modelo._carregar_explicador()` passou a distinguir pacote ausente de pacote bloqueado pelo sistema e a dizer que o ambiente publicado não é afetado. O README documenta o comportamento no Windows. O ambiente publicado roda em Linux e usa a explicação local (T01.3 de `testar_api_publicada.py`), por isso é a referência para os fatores exibidos.
- **Reteste:** caminho com o shap disponível: `testar_predicao.py` com 79/79 no Windows em 14/10/2026, já com explicação local, numa execução em que o bloqueio não ocorreu. Caminho com o shap bloqueado: simulado com um módulo que reproduz o mesmo `ImportError`, com 79/79 e a mensagem nova no log; o bloqueio real não voltou a ocorrer depois da correção para ser observado de novo.

### F-10. README sem a configuração do aplicativo

- **Falha:** seguindo apenas o README, o aplicativo não abria. O README mandava rodar `npm install` e `npx expo start`, sem instruir a criação de `app/.env`.
- **Reprodução:** clone limpo, `npm install`, `npx expo start` e tecla `w`. Erro: `EXPO_PUBLIC_FIREBASE_API_KEY não definida. Copie app/.env.example para app/.env e preencha a chave antes de rodar o app.`
- **Correção:** README passou a incluir a cópia de `app/.env.example` para `app/.env` e o preenchimento da chave, e a fixar o Python 3.12 nos pré-requisitos.
- **Reteste:** com o `.env` criado, o aplicativo abriu no navegador, a conta de demonstração entrou e a cliente Eduarda Freitas foi avaliada como risco alto, com os mesmos três fatores do teste publicado (reclamações, frequência de chamadas, situação da linha).

### F-11. Sugestão de retenção contradizendo o valor do cliente

- **Falha:** os textos de sugestão em `api/faixas.py` supõem um sentido fixo para cada atributo (por exemplo, "Rede de contatos reduzida" sempre que contatos distintos aumentam o risco). O Random Forest não é monótono: o mesmo atributo pode aumentar o risco com valor alto em um perfil e com valor baixo em outro. A tela afirmava algo falso sobre o cliente.
- **Reprodução:** prever os 3.150 registros e comparar o fator exibido com o valor do atributo em relação à mediana da carteira. `distinct_called_numbers` aparecia como "aumenta" com valor acima da mediana em 46 de 57 casos, com o texto "Rede de contatos reduzida"; também havia contradições em `seconds_of_use` (44 de 188), `customer_value` (20 de 56) e `subscription_length` ("Cliente de longa data" com valor abaixo da mediana).
- **Correção:** cada atributo contínuo declara em `ATRIBUTOS` de que lado da mediana o texto específico foi escrito (`aumenta_quando`). `descrever()` recebe o valor do cliente e a referência de `metadados.json` (`modelo.referencias()`); quando o sinal do fator e o lado do valor não combinam, a sugestão passa a ser neutra ("… acima da mediana da carteira; neste perfil, esse valor pesa a favor do cancelamento …"). O rótulo, o sinal, o peso e a ordem dos fatores não mudam.
- **Reteste:** nova seção "Sugestões coerentes com o valor do cliente" em `testar_predicao.py`, que passa os registros pela própria rota `/predict` e falha se algum texto específico contradisser o valor. Com o código anterior: 1 falha; com a correção: 86/86, com 91 fatores recebendo a sugestão neutra em 630 registros. Publicado no Render e verificado com `testar_api_publicada.py`, 30/30 em 16/10/2026 (commit `ff421fc`).

### F-12. Modelo servido pela API diferente do modelo final do pisi3-grupo4

- **Falha:** a API servia o modelo importado em 27/09 (SHA-256 `6aa328bb…`, commit `2d2e0a3` do pisi3-grupo4), enquanto o modelo final consolidado em 29/09 (commit `8d06df3`, SHA-256 `13d946fb…`) é o que gera a validação cruzada e os valores SHAP do artigo. Os dois têm os mesmos hiperparâmetros e as mesmas métricas de teste (93 de 100 cancelamentos, 18 falsos positivos), mas o F1 em validação cruzada difere (0,869 contra 0,870) e as probabilidades diferem em até 0,015, mudando a faixa de 6 dos 3.150 registros. O artigo afirmava que a aplicação executa o mesmo artefato avaliado nos experimentos.
- **Reprodução:** `congelar.py` compara o SHA-256 de `ml/artefatos/modelo.joblib` com o de `pisi3-grupo4/models/modelo_final.joblib`.
- **Correção:** novo pacote gerado por `ml/importar_modelo.py` a partir do commit `8d06df3` (commit `ff421fc`), publicado no Render; artigo atualizado com os números desse modelo.
- **Reteste:** `testar_predicao.py` 86/86 e `testar_api_publicada.py` 30/30 em 16/10/2026 (`docs/evidencias/teste_api_publicada_2026-10-16_1248.md`). O caso de referência "Plano 2, situação da linha 2" passou de 0,935 para 0,94, e o teste publicado confirmou o valor novo. Os sete clientes de demonstração mantêm faixa e fatores.

## Histórico de execuções

Acrescentar uma linha a cada execução relevante. O relatório completo de cada uma fica em `docs/evidencias/`.

| Data | Script | Ambiente | Resultado | Relatório |
|---|---|---|---|---|
| 14/10/2026 | `testar_predicao.py` | local (Windows 11, Python 3.12.10) | 79/79 | saída do terminal |
| 14/10/2026 | `testar_falhas.py` | local (Windows 11, Python 3.12.10) | 12/12 | `docs/evidencias/teste_falhas_2026-10-14_0919.md` |
| 14/10/2026 | `testar_api_publicada.py` | Render, `https://dsi-grupo4.onrender.com` | 30/30 | `docs/evidencias/teste_api_publicada_2026-10-14_0935.md` |
| 14/10/2026 | `testar_api_publicada.py` | Render, commit `b9b5a73` | 30/30 | `docs/evidencias/teste_api_publicada_2026-10-14_1501.md` |
| 14/10/2026 | instalação seguindo o README | clone limpo em `C:\teste-limpo`, venv novo, mesma máquina | API e app de pé após 2 correções (F-09, F-10) | descrito abaixo |
| 16/10/2026 | `testar_predicao.py` | local (Windows 11, Python 3.12.10), commit `ff421fc` | 86/86 | saída do terminal |
| 16/10/2026 | `testar_api_publicada.py` | Render, commit `ff421fc` | 30/30 | `docs/evidencias/teste_api_publicada_2026-10-16_1248.md` |
| 16/10/2026 | gravação do histórico pelo app | app no navegador + Render + regra do Firestore publicada | avaliação da cliente Eduarda Freitas gravada em `clientes/demo-05/avaliacoes`, sem aviso de falha | conferido no console do Firebase |

## Instalação a partir de um clone limpo

Registro da verificação de que o README é suficiente para colocar o sistema de pé a partir de um clone novo.

- **Data:** 14/10/2026.
- **Quem executou e onde:** Lucas de Farias Guerra, em Windows 11 com Python 3.12, num clone novo em `C:\teste-limpo\dsi-grupo4`, com venv e `node_modules` novos. Foi a mesma máquina de desenvolvimento, não outra; a repetição em outra máquina fica a cargo de outro integrante.
- **Passos que funcionaram sem ajuste:** `git clone`; criação do venv; `pip install -r requirements.txt`; cópia de `.env.example` para `.env` na API; `uvicorn main:app --port 8000` com Firebase e modelo carregados; `npm install`.
- **Passos que precisaram de ajuste:** a explicação SHAP ficou indisponível pelo bloqueio do Windows (F-09); o aplicativo não abriu sem o `app/.env`, que o README não mencionava (F-10). Os dois foram corrigidos no README.
- **Resultado de `testar_predicao.py` nessa instalação:** 79/79.
- **Teste de ponta a ponta:** login com `demo.gestor1@example.com`, avaliação da cliente Eduarda Freitas pela API publicada: risco alto, com fatores reclamações registradas (aumenta), frequência de chamadas (reduz) e situação da linha (aumenta).