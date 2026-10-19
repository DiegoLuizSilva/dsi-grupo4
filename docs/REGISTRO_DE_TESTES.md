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

### F-13. CSV original alterado pelo Git no Windows

- **Falha:** `src/validar_inferencia.py` (pisi3-grupo4) recusava a execução com "O CSV não corresponde ao usado no treinamento". O Git do Windows, com `core.autocrlf` ativo, trocou as quebras de linha de `data/raw/iranian_churn.csv` de LF para CRLF ao baixar o repositório. O conteúdo era o mesmo, mas o SHA-256 passou de `72a4a660…` para `90d5fb6b…`.
- **Reprodução:** clonar o pisi3-grupo4 no Windows e rodar `python -m src.validar_inferencia --dsi-root ..\dsi-grupo4`.
- **Correção:** `.gitattributes` com `data/raw/*.csv -text` no pisi3-grupo4, que impede a conversão, e nova cópia do CSV sem conversão (`git -c core.autocrlf=false checkout`).
- **Reteste:** SHA-256 do CSV igual a `72a4a660…` e `validar_inferencia` sem divergência em 16/10/2026.

### F-14. Modelo final retreinado por engano no pisi3-grupo4

- **Falha:** o commit `1bf7c2b` do pisi3-grupo4 (16/10), feito para a página de visão geral do painel, levou junto uma nova execução de todo o pipeline em Python 3.14.7. O modelo final passou a ter SHA-256 `215c4759…` no lugar de `13d946fb…`, o F1 de churn em validação cruzada caiu de 0,870 para 0,869 e predições, valores SHAP, figuras e notebooks 03 a 06 foram sobrescritos. O artigo, a API publicada e o README continuavam descrevendo o modelo `13d946fb…`.
- **Reprodução:** comparar `models/modelo_final.joblib` com `ml/artefatos/modelo.joblib`, como faz `congelar.py`, ou rodar `python -m src.validar_inferencia --dsi-root ..\dsi-grupo4`.
- **Correção:** os 34 artefatos gerados pelo pipeline (modelos, tabelas, figuras e notebooks 03 a 06) voltaram à versão do commit `740f8bb`; o código da página e as demais mudanças do commit foram mantidos. O pipeline não deve ser reexecutado fora de Python 3.12 (ver F-05), e o painel só lê os resultados, sem retreinar.
- **Reteste:** SHA-256 do modelo de volta a `13d946fb…`, `cv_f1` 0,8699 e as cinco páginas já existentes do painel abrindo sem erro com os números do artigo, em 18/10/2026.

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
| 16/10/2026 | `src/validar_inferencia.py --dsi-root` (pisi3-grupo4) | local (Windows 11, Python 3.12), pisi3-grupo4 `740f8bb` × dsi-grupo4 `c44b4e99` | sem divergência: modelo `13d946fbcaa2`, 633 escores do teste com erro máximo 1,1e-16; atributos, exclusão de age_group e ordem do SHAP iguais | saída do terminal |
| 19/10/2026 | tempo de avaliação pelo app no celular | Samsung Galaxy S23, Android atualizado, Expo Go, Wi-Fi doméstico, Render, commit `201cdd7` | serviço dormindo: falha em cerca de 6 a 7 s; serviço acordado: cerca de 2 s em mais de 5 avaliações, todas gravadas no histórico | descrito abaixo |
| 19/10/2026 | faixas, fatores, pesos e sugestões no app | mesmo aparelho e rede, Render, commit `201cdd7` | os sete clientes de demonstração mostraram faixa, fatores, sentido, barras e sugestões iguais aos calculados pela rota `/predict` local | descrito abaixo |
| 19/10/2026 | `ml/validar_integracao_dsi.py --api-url` | local (Ubuntu, `api/venv`, Python 3.12.3) contra o Render, commit `7b17176`, conta autenticada do grupo | modelo `13d946fb…`; 633 escores do teste reproduzidos (desvio máximo 1,1e-16); 5 casos de referência iguais no artefato e na API publicada; maior duração HTTP 1,161 s | descrito abaixo |

## Tempo de avaliação no aplicativo

Medição do tempo completo de uma avaliação no celular, pedida na Sprint 6 com limite de 3 segundos.

- **Data e quem executou:** 19/10/2026, Diego Luiz.
- **Aparelho e rede:** Samsung Galaxy S23 com a versão mais recente do Android disponível para o aparelho, app rodando no Expo Go (modo de desenvolvimento, um pouco mais lento que um build), Wi-Fi doméstico, API publicada no Render, commit `201cdd7`.
- **O que foi medido:** do toque em *Avaliar risco de cancelamento* até a tela de resultado com faixa e fatores. Inclui a chamada a `/predict` (modelo e SHAP) e a gravação no histórico, que acontece antes da troca de tela. Os tempos foram estimados por quem testou, sem gravação de tela.
- **Serviço dormindo:** a primeira avaliação, depois de mais de 15 minutos sem uso, terminou em cerca de 6 a 7 s com o aviso *Serviço indisponível* (mensagem do cliente HTTP: "Nao foi possivel alcancar o servidor de analise"). Logo depois, o `/health` respondeu com `modelo.carregado: true`, `modelo_versao: rf-smotenc-1.0`, `explicacao: local`, `banco.conectado: true`, `autenticacao_exigida: true` e `stub_permitido: false`. O aviso *Cannot connect to Expo CLI* que apareceu junto é do Expo Go, sobre a conexão com o servidor de desenvolvimento, e não da API.
- **Serviço acordado:** mais de 5 clientes avaliados em sequência, cada um em cerca de 2 s, dentro do limite de 3 s. Houve resultados de risco baixo (a maioria), médio e alto. Nenhuma avaliação mostrou *Avaliação não registrada*.
- **Limitação conhecida:** com o plano gratuito, o Render desliga o serviço após 15 minutos sem uso, e a primeira chamada depois disso falha no app antes de o serviço terminar de acordar. O aviso não confirma uma avaliação falsa, e uma nova tentativa com o serviço acordado funciona. A mitigação para a demonstração já está em `docs/RECUPERACAO_E_DEMONSTRACAO.md`: abrir o `/health` 30 minutos antes e de novo 5 minutos antes.

## Faixas, fatores e sugestões no aplicativo

Conferência pedida na Sprint 7: a regra das faixas nos limites de 0,30 e 0,65 e a consistência de fatores, pesos e sugestões no app.

- **Limites das faixas:** cobertos de forma automática pela seção "Faixas de risco nos limites" de `testar_predicao.py` (0,2999 baixo; 0,30 médio; 0,65 médio; 0,6501 alto) e pelo caso 1624 de `ml/validar_integracao_dsi.py` (escore 0,650, faixa média). O app não exibe o escore, então os limites não aparecem na tela.
- **No app (19/10/2026, Diego Luiz, Samsung Galaxy S23, Expo Go, Render, commit `201cdd7`):** os sete clientes de demonstração foram avaliados e comparados com o resultado esperado, obtido passando os mesmos casos de `ml/artefatos/casos_de_referencia.json` pela rota `/predict` local, com o mesmo código e o mesmo modelo publicados. Para cada cliente conferiu-se a faixa (texto e cor), os três fatores na ordem, o sentido (aumenta ou reduz) e a cor da barra, o tamanho relativo das barras e se a sugestão combina com o sentido.
- **Resultado:** os sete conferiram: Ana Beatriz Lima, Bruno Carvalho, Carla Menezes e Daniel Souza em risco baixo; Fabio Nascimento em risco médio (escore 0,319, o mais próximo do corte de 0,30); Eduarda Freitas e Gabriela Rocha em risco alto. Nenhuma avaliação mostrou *Avaliação não registrada*. Fatores que aumentam o risco em clientes de risco baixo (Carla, Daniel) são esperados: cada fator mostra o próprio sentido, e a faixa resulta da soma das contribuições.

## Conferência final dos casos de referência na API publicada

Conferência pedida na Sprint 9: comparar os casos de referência do modelo com as respostas da API publicada e registrar a versão verificada.

- **Data e quem executou:** 19/10/2026, Diego Luiz, com `api/venv/bin/python ml/validar_integracao_dsi.py --api-url https://dsi-grupo4.onrender.com`, autenticado com uma conta do grupo (token do Firebase na variável `CHURNGUARD_ID_TOKEN`, sem gravar nada na carteira).
- **Versão verificada:** dsi-grupo4 no commit `7b17176`, modelo `rf-smotenc-1.0` com SHA-256 `13d946fb…` (conferido pelo script antes da comparação), serviço do Render acordado pelo `/health` antes da execução.
- **Artefato:** os 633 escores do conjunto de teste do pisi3-grupo4 reproduzidos com desvio máximo de 1,1e-16.
- **Casos de referência (`ml/reports/casos_shap_referencia.json`):** os cinco casos deram a mesma classe positiva, escore, faixa e fatores no artefato local e na API publicada:

| row_id | Escore | Faixa | Fatores |
|---|---:|---|---|
| 110 | 0,0950 | baixo | status, call_failure, complains |
| 516 | 0,2863 | baixo | status, age, call_failure |
| 399 | 0,5150 | medio | subscription_length, complains, status |
| 1624 | 0,6500 | medio | complains, customer_value, status |
| 72 | 0,9000 | alto | complains, status, call_failure |

- **Tempo:** maior duração local 0,028 s com TreeSHAP; maior duração HTTP na API publicada 1,161 s. O tempo completo no celular está na seção "Tempo de avaliação no aplicativo".

## Instalação a partir de um clone limpo

Registro da verificação de que o README é suficiente para colocar o sistema de pé a partir de um clone novo.

- **Data:** 14/10/2026.
- **Quem executou e onde:** Lucas de Farias Guerra, em Windows 11 com Python 3.12, num clone novo em `C:\teste-limpo\dsi-grupo4`, com venv e `node_modules` novos. Foi a mesma máquina de desenvolvimento, não outra; a repetição em outra máquina fica a cargo de outro integrante.
- **Passos que funcionaram sem ajuste:** `git clone`; criação do venv; `pip install -r requirements.txt`; cópia de `.env.example` para `.env` na API; `uvicorn main:app --port 8000` com Firebase e modelo carregados; `npm install`.
- **Passos que precisaram de ajuste:** a explicação SHAP ficou indisponível pelo bloqueio do Windows (F-09); o aplicativo não abriu sem o `app/.env`, que o README não mencionava (F-10). Os dois foram corrigidos no README.
- **Resultado de `testar_predicao.py` nessa instalação:** 79/79.
- **Teste de ponta a ponta:** login com `demo.gestor1@example.com`, avaliação da cliente Eduarda Freitas pela API publicada: risco alto, com fatores reclamações registradas (aumenta), frequência de chamadas (reduz) e situação da linha (aumenta).