# Demonstração e recuperação

Como preparar o ambiente publicado para a apresentação, o roteiro da demonstração e o que fazer se algo falhar na hora.

Endereço da API: `https://ENDERECO_RENDER`

## 1. Contas de demonstração

Duas contas, para mostrar que a carteira é compartilhada entre gestores.

| Conta | Uso |
|---|---|
| `demo.gestor1@example.com` | conta principal da demonstração |
| `demo.gestor2@example.com` | segunda conta, para mostrar a carteira compartilhada |

As contas são criadas pela tela **Criar conta** do próprio aplicativo, para que o perfil em `pessoas` seja gerado pelo fluxo normal. O domínio `example.com` é reservado para exemplos e não pertence a ninguém.

**As senhas não ficam neste repositório.** Ficam com o grupo, fora do Git.

## 2. Clientes de demonstração

Gravados por `api/semear_demonstracao.py`, com os dados dos casos de referência do modelo. A faixa de cada um é conhecida de antemão:

| id | Cliente | Faixa esperada | Probabilidade |
|---|---|---|---|
| demo-01 | Ana Beatriz Lima | baixo | 0,00% |
| demo-02 | Bruno Carvalho | baixo | 1,00% |
| demo-03 | Carla Menezes | baixo | 3,00% |
| demo-04 | Daniel Souza | baixo | 2,00% |
| demo-05 | Eduarda Freitas | **alto** | 93,50% |
| demo-06 | Fabio Nascimento | **médio** | 31,88% |
| demo-07 | Gabriela Rocha | **alto** | 75,83% |

A probabilidade não aparece na tela do aplicativo; está aqui só para conferência.

```powershell
cd api
venv\Scripts\activate
python semear_demonstracao.py            # grava ou restaura os sete
python semear_demonstracao.py --limpar   # remove os sete
```

Rodar de novo sobrescreve os mesmos sete documentos. Clientes cadastrados por pessoas não são tocados.

## 3. Antes da apresentação

**Na véspera**

1. `python testar_api_publicada.py --url https://ENDERECO_RENDER --email demo.gestor1@example.com` com todas as verificações passando.
2. `python semear_demonstracao.py` para deixar a carteira no estado inicial.
3. Entrar no aplicativo com as duas contas e conferir que os sete clientes aparecem.

**30 minutos antes**

1. Abrir `https://ENDERECO_RENDER/health` no navegador e esperar a resposta. O plano gratuito desliga o serviço após 15 minutos sem uso, e a primeira chamada leva cerca de um minuto.
2. Conferir no `/health`: `modelo.carregado: true`, `modelo_versao: rf-smotenc-1.0`, `explicacao: local`, `banco.conectado: true`, `autenticacao_exigida: true`, `stub_permitido: false`.
3. Entrar no aplicativo com `demo.gestor1` e deixar na tela de clientes.

**5 minutos antes**

1. Recarregar o `/health` para o serviço não voltar a dormir.
2. Deixar aberta uma aba com o `/health` e outra com o painel do Render.

## 4. Roteiro da demonstração

1. **Entrar** com `demo.gestor1`. Mostrar que sem conta não se chega aos dados.
2. **Clientes**: a carteira com os sete clientes.
3. **Eduarda Freitas** → *Avaliar risco de cancelamento* → risco **alto** e os três fatores que mais pesaram, com a ação de retenção sugerida para cada um.
4. **Fabio Nascimento** → risco **médio**. Comparar os fatores com os da Eduarda.
5. **Ana Beatriz Lima** → risco **baixo**.
6. **Novo Cliente**: cadastrar um cliente na hora e avaliá-lo.
7. **Sair** e entrar com `demo.gestor2`: o cliente cadastrado no passo 6 aparece, porque a carteira é da equipe.

Depois da apresentação, rodar `python semear_demonstracao.py` e remover pelo aplicativo o cliente criado no passo 6.

## 5. Se algo falhar

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Aplicativo mostra *Serviço indisponível* na primeira avaliação | serviço do Render dormindo | abrir o `/health`, esperar a resposta (até 1 minuto) e tentar de novo |
| `/health` mostra `modelo.carregado: false` | última publicação quebrada | Render → serviço → **Events** → na última publicação que funcionou, **Rollback** |
| `/health` mostra `banco.conectado: false` | variável `FIREBASE_CREDENCIAL_JSON` ausente ou alterada | Render → **Environment** → colar de novo o JSON da conta de serviço → **Save Changes** (o serviço reinicia sozinho) |
| Login recusado ou *sessão expirada* | token vencido | sair e entrar de novo no aplicativo |
| Um cliente de demonstração sumiu ou foi alterado | edição durante o ensaio | `python semear_demonstracao.py` |
| `/health` não responde depois de 2 minutos | Render fora do ar | **Plano B** abaixo |
| Sem internet na sala | rede | roteador do celular; se não resolver, **Plano C** |

### Plano B: API na máquina de quem apresenta

Exige `api/serviceAccountKey.json` na máquina, que nunca vai para o Git.

```powershell
# terminal 1
cd C:\dev\dsi-grupo4\api
venv\Scripts\activate
uvicorn main:app --port 8000
```

Em `app/.env`, trocar a linha da API para:

```
EXPO_PUBLIC_API_URL=http://localhost:8000
```

```powershell
# terminal 2: o -c limpa o cache, senão o app continua com o endereço antigo
cd C:\dev\dsi-grupo4\app
npx expo start -c
```

Abrir no navegador (tecla `w`). Conferir `http://localhost:8000/health` antes de demonstrar.

Depois da apresentação, voltar `EXPO_PUBLIC_API_URL` para o endereço do Render.

### Plano C: gravação

Uma gravação de tela do roteiro da seção 4, feita no ensaio com o ambiente publicado funcionando. Fica com quem apresenta, no computador e no celular, para não depender de rede.

## 6. Congelamento da versão (19/10)

A partir do congelamento, só entram correções de falhas que impeçam a demonstração.

1. Conferir que nenhuma credencial está versionada. O primeiro e o terceiro comandos precisam voltar **vazios**; o segundo pode mostrar apenas a linha de exemplo de `api/.env.example`, que tem `...` no lugar da chave:

```powershell
   git ls-files | Select-String -Pattern "serviceAccount|\.env$"
   git grep -n "private_key"
   git log --all --oneline -- api/serviceAccountKey.json
```

2. Rodar as três baterias e registrar em `docs/REGISTRO_DE_TESTES.md`.
3. Marcar a versão nos dois repositórios:

```powershell
   git tag -a v1.0-apresentacao -m "Versao apresentada em DSI e PISI3"
   git push origin v1.0-apresentacao
```

4. Gravar a demonstração (Plano C).
5. Ensaio completo com o grupo, cronometrado.
6. Guardar o comprovante de submissão do artigo.