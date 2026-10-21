# Pacote final da entrega

Versão congelada em 21/10/2026 12:44 para a apresentação de 21/10/2026. A partir daqui só entram correções de falhas que impeçam a demonstração; qualquer correção repete os testes afetados e atualiza este arquivo.

## Revisões

| Peça | Revisão |
|---|---|
| App e API (dsi-grupo4) | `22c2a42` — docs(testes): relatorio do teste da API publicada em 21/10 |
| Análises e modelo (pisi3-grupo4) | `c8b4ec4` — fix(painel-perfis): binarios sem padronizacao, proporcoes da 7.1 e legendas por selecao |
| API publicada | commit `be5a7e5` em https://dsi-grupo4.onrender.com |
| Modelo | `rf-smotenc-1.0`, `ml/artefatos/modelo.joblib` |
| SHA-256 do modelo | `13d946fbcaa29a9027b33702a1ec41f244c22ec5c12b2004f8c81481382e4d7d` |
| Artigo | Artigo - Grupo 4.pdf |

A tag `v1.0-apresentacao` marca a versão entregue no dsi-grupo4. O pisi3-grupo4 segue com o painel até o congelamento de 23/10; a revisão acima é a que forneceu o modelo.

## Verificações no congelamento

| Verificação | Resultado |
|---|---|
| `testar_predicao.py` | 86 verificacoes passaram, 0 falharam |
| `testar_falhas.py` | 12 de 12 verificacoes passaram. |
| `testar_api_publicada.py` | 30 de 30, teste_api_publicada_2026-10-21_1233.md |
| Credenciais versionadas | nenhuma: `.env`, `serviceAccountKey.json` e chave privada conferidos nos dois repositórios e no histórico |
| Modelo da API igual ao do pisi3-grupo4 | sim, mesmo SHA-256 |
