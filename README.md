# ChurnGuard 📉📱

Aplicativo mobile para **previsão de risco de cancelamento (churn)** de clientes de operadoras de telecomunicações, com sugestão de ações de retenção baseadas em Machine Learning.

---

## 📌 Visão geral

O **ChurnGuard** é um aplicativo em **React Native (Expo)** no qual o gestor de uma operadora registra os dados de uso de um cliente — falhas de chamada, frequência de uso, tempo de assinatura, reclamações, tipo de plano e valor do cliente — e recebe:

- Uma **classificação de risco de cancelamento** em três faixas: **Alto**, **Médio** e **Baixo**;
- Os **principais fatores** que contribuem para esse risco;
- **Ações de retenção sugeridas** com base nesses fatores;
- Um **histórico** das avaliações realizadas para cada cliente, permitindo acompanhar sua evolução ao longo do tempo.

O modelo é treinado sobre o **Iranian Churn Dataset** (UCI Machine Learning Repository, 3.150 instâncias e 13 atributos), e o desenvolvimento é acompanhado de um artigo científico produzido no modelo da disciplina.

🔗 Dataset: [Iranian Churn Dataset — UCI](https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset)

> **Nota:** a ideia original do projeto envolvia captação de voz, mas foi descartada por exigir meses de treinamento e ajuste do modelo. O escopo foi redirecionado para retenção de clientes via Machine Learning, resultando no ChurnGuard.

---

## 🏗️ Arquitetura

| Camada | Tecnologia |
|---|---|
| **Frontend** | React Native (Expo) — telas de CRUD, formulário de predição, resultado e histórico |
| **Backend** | API em Python (FastAPI), expondo `/predict` e os endpoints do CRUD |
| **Banco de dados** | Firebase (Cloud Firestore) para o CRUD, armazenamento e histórico do aplicativo em tempo real e API |
| **Machine Learning** | Python — `pandas`, `scikit-learn`, `imbalanced-learn`, `matplotlib`, `seaborn`, `shap` |
| **Versionamento** | Repositório único no GitHub com as pastas `/app`, `/api` e `/ml`, membros devem usar o git pull antes de commitar na main  |

> ⚠️ O modelo `scikit-learn` **não roda dentro do React Native** — por isso a API Python é obrigatória e precisa estar de pé para qualquer demonstração.

### Estrutura de pastas

```
dsi-grupo4/
├── app/     # Aplicativo React Native (Expo)
├── api/     # API Python (Flask/FastAPI) — CRUD + /predict
└── ml/      # Notebooks, dados e modelos de Machine Learning
```

---

## 👥 Equipe e responsabilidades

Cada integrante é responsável por uma frente de trabalho ao longo das 9 semanas do projeto.

| Pessoa | Frente principal | Responsabilidade |
|---|---|---|
| **Lucas Guerra** | Tech Lead / Backend | Repositório, board, API Python, integração app↔API, consolidação do artigo |
| **Artur Rio** | Dados e não-supervisionado | Limpeza, EDA, gráficos, clusterização (KMeans, cotovelo, silhueta) |
| **Diego Luiz** | Supervisionado | Pré-processamento, treino/teste, comparação de algoritmos, balanceamento, SHAP |
| **Pedro Poroca** | Frontend — CRUD | Navegação, listagem, cadastro, edição e exclusão de clientes, persistência |
| **Arthur Schmitz** | Frontend — Predição e UX | Formulário de predição, tela de resultado, histórico, design e formatação do artigo |

---

## 🗓️ Cronograma resumido

| Sprint | Período | Foco |
|---|---|---|
| 1 | 24–30/ago | Fundação: repositório, ambiente, dataset, wireframes, perguntas de pesquisa |
| 2 | 31/ago–06/set | Análise exploratória + esqueleto do app + backend stub |
| 3 | 07–13/set | Clusterização v1, classificação v1, CRUD funcionando, artigo até a Seção 5 |
| 4 | 14–20/set | **ENTREGA 1** (16/set) + refinamento de modelos |
| 5 | 21–27/set | Modelo final, balanceamento, tuning, SHAP e API de predição real |
| 6 | 28/set–04/out | Integração completa app↔API, histórico, fatores de risco e ações de retenção |
| 7 | 05–11/out | Artigo Seções 6 e 7, testes do app, tabelas de resultados |
| 8 | 12–18/out | Polimento, testes com usuários, revisão cruzada, declaração de uso de IA |
| 9 | 19–25/out | Congelamento, revisão final, apresentação e **ENTREGA FINAL** |

---

## ⚙️ Rituais e regras do grupo

- **Planejamento:** segunda-feira, 30 min — cada um confirma as tarefas da semana.
- **Checkpoint:** quinta-feira, 15 min — quem está travado fala e recebe ajuda antes do fim de semana.
- **Fechamento:** domingo — tudo pronto entra na branch principal e é marcado como concluído no board.
- **Definition of Done:** uma tarefa só está pronta quando o código está no GitHub e roda na máquina de outra pessoa, a tela/notebook foi mostrado ao grupo, e o trecho correspondente do artigo foi escrito ou atualizado.
- **Regra do artigo:** nenhuma sprint termina sem escrita — o artigo cresce junto com o código.
- Atrasos são redistribuídos no checkpoint de quinta, nunca na véspera da entrega.

---

## 🧠 Sobre o modelo de Machine Learning

- **Dataset:** Iranian Churn Dataset (UCI) — 3.150 instâncias, 13 atributos, alvo binário (`Churn`: 0 ou 1).
- **Não-supervisionado:** clusterização (KMeans, com método do cotovelo e coeficiente de silhueta) para identificar e caracterizar perfis de clientes. O algoritmo não recebe a coluna `Churn`; o alvo só é cruzado com os grupos depois da formação dos clusters.
- **Supervisionado:** comparação entre SVM, KNN e Random Forest, com balanceamento de classes (SMOTE/undersampling) e tuning de hiperparâmetros.
- **Avaliação:** como 84,29% da base pertence à classe sem cancelamento, a acurácia não é usada isoladamente. A discussão prioriza precisão, revocação e F1-score da classe de cancelamento, além das médias macro e ponderada.
- **Explicabilidade:** uso de **SHAP** para traduzir a saída do modelo final em fatores de risco legíveis por cliente.
- **Faixas de risco:** como o alvo do dataset é binário, os níveis Alto/Médio/Baixo são derivados da probabilidade prevista (`predict_proba`), com pontos de corte definidos e justificados no artigo (ex.: `<0,30` baixo, `0,30–0,65` médio, `>0,65` alto).
- **Independência das análises:** o agrupamento e a classificação são análises complementares sobre o mesmo conjunto de dados, respondendo a perguntas distintas. Os clusters não alimentam os classificadores.

---

## 🚀 Como rodar o projeto

> Instruções detalhadas de instalação serão adicionadas conforme o repositório evolui (Sprint 1).

### Pré-requisitos
- Node.js e Expo CLI (para o app)
- Python 3.x e `pip` (para a API e o ML)
- Expo Go instalado no celular (para testes no dispositivo físico)

### Backend / API
```bash
cd api
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

Documentação interativa em http://localhost:8000/docs.
```
### App (React Native / Expo)
```bash
cd app
npm install
npx expo start
```

### Machine Learning
```bash
cd ml
pip install -r requirements.txt
jupyter notebook
```

---

## 📄 Artigo científico

O projeto é acompanhado de um artigo científico, produzido em paralelo ao desenvolvimento, cobrindo:

- Três perguntas de pesquisa (uma **não-supervisionada**, uma **supervisionada** e uma sobre **camada de aplicação**);
- Metodologia mapeada às etapas do **KDD**;
- Resultados de clusterização e classificação;
- Declaração de uso de IA.

---

## ⚠️ Pontos de atenção

- O alvo do dataset é **binário**, mas o app exibe **três faixas de risco** — os cortes de probabilidade precisam estar documentados e justificados.
- **React Native não executa `scikit-learn`** — a API Python é obrigatória e deve estar hospedada antes da Sprint 6.
- O modelo de artigo da disciplina originalmente menciona "Aplicativo Flutter" — a seção correspondente foi adaptada para **React Native**.

---

