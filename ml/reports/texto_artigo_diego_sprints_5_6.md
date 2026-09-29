# Texto de Diego para as Seções 7.2 e 6.1

Texto pronto para revisão coletiva e inserção no artigo compartilhado. Os
resultados abaixo vêm dos artefatos executados no repositório PISI3, não do
stub da API. A versão publicada do aplicativo ainda precisa ser validada
antes de usar telas como evidência da PP3.

## 7.2 Classificação supervisionada e atributos influentes

O conjunto Iranian Churn contém 3.150 registros, sendo 15,71% da classe
`Churn=1`. A separação treino/teste agrupou perfis preditores idênticos,
impedindo sua ocorrência nos dois conjuntos. O treino reuniu 2.517 registros
e o teste, 633. A classe `Churn` não participou do agrupamento de perfis para
essa separação; foi usada para estratificar aproximadamente a proporção das
classes. A variável `age_group` foi retirada das entradas do classificador
por ser determinada por `age`. As demais 12 variáveis foram mantidas. Para
`tariff_plan` e `status`, os valores originais 1 e 2 foram codificados como
0 e 1. Escalonamento e balanceamento foram ajustados apenas dentro de cada
partição de treino, evitando que informações da validação ou do teste
influenciassem a preparação dos dados.

Foram comparados SVM, KNN e Random Forest, cada um sem balanceamento, com
SMOTENC e com subamostragem aleatória. O SMOTENC foi usado em lugar do SMOTE
convencional para preservar a natureza das variáveis binárias. A seleção
considerou o F1 médio da classe churn em validação cruzada estratificada por
grupos com cinco partições no conjunto de treino. A acurácia não foi usada
isoladamente: no teste, o classificador que sempre prediz a classe
majoritária alcança 84,20% de acurácia, mas F1 e revocação iguais a zero para
churn.

| Modelo e tratamento | Precisão churn CV | Revocação churn CV | F1 churn CV |
|---|---:|---:|---:|
| Random Forest + SMOTENC | 0,833 | 0,909 | **0,869** |
| Random Forest sem balanceamento | 0,882 | 0,810 | 0,844 |
| Random Forest + subamostragem | 0,613 | 0,944 | 0,742 |
| KNN sem balanceamento | 0,862 | 0,803 | 0,830 |
| KNN + SMOTENC | 0,756 | 0,911 | 0,827 |
| KNN + subamostragem | 0,648 | 0,929 | 0,762 |
| SVM sem balanceamento | 0,873 | 0,757 | 0,810 |
| SVM + SMOTENC | 0,732 | 0,919 | 0,814 |
| SVM + subamostragem | 0,640 | 0,954 | 0,765 |

O Random Forest com SMOTENC apresentou o maior F1 médio na validação e foi
selecionado **antes** da consulta aos resultados do teste. No conjunto de
teste, identificou corretamente 93 dos 100 clientes com churn; sete casos de
churn não foram identificados. Entre os 533 sem churn, 18 foram classificados
indevidamente como churn. A precisão da classe churn foi 0,838, a revocação
0,930 e o F1 0,882. A acurácia foi 0,961, a AUC ROC 0,990 e a precisão média
na curva precisão-revocação 0,943.

| Classe ou média, Random Forest + SMOTENC no teste | Precisão | Revocação | F1 | Suporte |
|---|---:|---:|---:|---:|
| 0, sem churn | 0,987 | 0,966 | 0,976 | 533 |
| 1, churn | 0,838 | 0,930 | 0,882 | 100 |
| Média macro | 0,912 | 0,948 | 0,929 | 633 |
| Média ponderada | 0,963 | 0,961 | 0,961 | 633 |

No treino, o F1 da classe churn foi 0,971, diferença de 0,090 em relação ao
teste. Isso sinaliza possível sobreajuste, ainda que o F1 da validação
cruzada (0,869) e do teste (0,882) sejam próximos. O Random Forest sem
balanceamento teve F1 de teste ligeiramente superior (0,893), com precisão
0,907 e revocação 0,880. A escolha do modelo com SMOTENC permaneceu porque
foi determinada pelo critério de validação previamente definido, e também
porque identificou cinco casos adicionais de churn no teste, ao custo de
mais falsos positivos. Usar o teste para trocar o vencedor após observar
esses números enviesaria a avaliação final.

A influência dos atributos foi examinada com SHAP aplicado ao pipeline
escolhido. A análise global usou 50 registros do treino como referência e
uma amostra de 80 registros do teste. A média dos valores absolutos de SHAP
nessa amostra destacou, nessa ordem, `status` (0,105), `complains` (0,063),
`frequency_of_use` (0,047), `seconds_of_use` (0,033) e
`subscription_length` (0,033). Os valores são contribuições ao **score não
calibrado** do modelo; a ordem global não determina necessariamente os
principais fatores de cada cliente. Para uma avaliação individual, o sinal
do valor SHAP informa se um atributo aumentou ou reduziu o score em relação
à referência do modelo. Esses resultados descrevem o comportamento do
classificador e não demonstram relação causal entre atributo e cancelamento.

O modelo aprende o alvo binário, sem classes de risco baixo, médio e alto. As
três faixas do aplicativo são derivadas posteriormente do score de
`predict_proba`, com cortes operacionais em 0,30 e 0,65. Como a calibração
desse score ainda não foi avaliada, ele não deve ser descrito como uma
probabilidade empírica exata de cancelamento. As faixas auxiliam a leitura
do resultado, mas sua utilidade para priorizar retenção precisaria ser
avaliada em uso real.

## Apoio à Seção 6.1 após validar o aplicativo

O contrato da API entrega uma faixa textual, até três fatores ordenados por
contribuição absoluta e uma sugestão associada a cada fator. Na tela atual,
o rótulo textual acompanha a cor, de modo que a distinção entre riscos não
depende apenas da cor. O score não é exibido ao gestor. A persistência da
avaliação no histórico ainda precisa ser implementada antes de afirmar que
o score foi preservado nesse registro. Para responder à PP3, inserir aqui
uma captura de uma **predição real** após validar o aplicativo com a API,
descrever os fatores enviados e mostrar como as sugestões aparecem na tela.
Isso evidencia que os fatores são apresentados de modo legível; não prova,
sem avaliação com usuários, que gestores sem formação em aprendizado de
máquina escolhem a ação mais adequada ou que a ação reduz o churn.

## Conferência editorial antes de colar no artigo

- O notebook de PISI3 também executou Regressão Logística, embora o plano do
  grupo para o artigo determine SVM, KNN e Random Forest. A tabela acima
  apresenta os três algoritmos combinados no plano de DSI; o grupo precisa
  decidir como relatar com transparência o experimento adicional de PISI3.
- Substituir na Seção 7.2 do artigo as tabelas fictícias com três classes.
  O alvo real é binário; os suportes de teste são 533 e 100.
- Conferir a data, a legenda e a numeração final das figuras com a versão
  compartilhada do artigo. Não usar capturas do stub como resultado do modelo.
- Com a API em execução e um token de conta real, executar
  `ml/validar_integracao_dsi.py --api-url ...` e cronometrar o fluxo no
  celular da demonstração. A verificação local das 633 predições já passou.
- No formulário atual, `calcularAgeGroup(30)` produz grupo 2, enquanto os
  registros do dataset com `age=30` pertencem ao grupo 3. O classificador
  descarta `age_group`, portanto isso não alterou os scores verificados,
  mas o campo salvo fica inconsistente com a base. Combinar a correção com
  Pedro; como `Age` no dataset representa apenas cinco valores de referência,
  não inventar limites etários sem decisão de domínio do grupo.
- O formulário converte alguns campos numéricos vazios em zero; revisar a
  validação com Pedro antes da demonstração para não registrar ausência de
  informação como uso igual a zero.
