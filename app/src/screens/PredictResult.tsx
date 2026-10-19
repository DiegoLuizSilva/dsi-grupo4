
import React from 'react';

import {
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  useRoute,
  type RouteProp,
} from '@react-navigation/native';

import type {
  Fator,
  RootStackParamList,
} from '../types';

type RotaResultado = RouteProp<
  RootStackParamList,
  'PredictResult'
>;

const CORES: Record<string, string> = {
  baixo: '#2E7D32',
  medio: '#ED6C02',
  alto: '#C62828',
};

// Nomes legíveis dos atributos originais da API.
const ROTULOS_ENTRADA: Record<string, string> = {
  call_failure: 'Falhas de chamada',
  complains: 'Reclamação registrada (0 ou 1)',
  subscription_length: 'Tempo de assinatura',
  charge_amount: 'Faixa de cobrança',
  seconds_of_use: 'Tempo total de uso',
  frequency_of_use: 'Quantidade de chamadas',
  frequency_of_sms: 'Quantidade de mensagens',
  distinct_called_numbers: 'Contatos distintos',
  age_group: 'Faixa etária',
  tariff_plan: 'Tipo de plano (1 ou 2)',
  status: 'Situação da linha (1 ou 2)',
  age: 'Idade',
  customer_value: 'Valor do cliente',
};

function formatarData(valor: string): string {
  const data = new Date(valor);

  if (Number.isNaN(data.getTime())) {
    return 'Data indisponível';
  }

  return data.toLocaleString('pt-BR');
}

function CartaoFator({
  fator,
  posicao,
}: {
  fator: Fator;
  posicao: number;
}) {
  const aumenta = fator.impacto === 'aumenta';

  const cor = aumenta ? '#C62828' : '#2E7D32';
  const fundo = aumenta ? '#FDECEA' : '#E8F5E9';

  const peso = Number.isFinite(fator.peso)
    ? fator.peso
    : 0;

  const percentual = Math.max(
    4,
    Math.min(100, Math.round(peso * 100))
  );

  const largura = `${percentual}%` as `${number}%`;

  return (
    <View style={estilos.cartaoFator}>
      <Text style={estilos.fatorNome}>
        {posicao}. {fator.rotulo}
      </Text>

      <View style={[estilos.selo, { backgroundColor: fundo }]}>
        <Text style={[estilos.seloTexto, { color: cor }]}>
          {aumenta ? 'Aumenta o risco' : 'Reduz o risco'}
        </Text>
      </View>

      <View style={estilos.barraFundo}>
        <View
          style={[
            estilos.barra,
            {
              backgroundColor: cor,
              width: largura,
            },
          ]}
        />
      </View>

      <Text style={estilos.acaoTitulo}>
        Ação sugerida
      </Text>

      <Text style={estilos.acaoTexto}>
        {fator.sugestao}
      </Text>
    </View>
  );
}

export default function PredictResult() {
  const route = useRoute<RotaResultado>();

  const {
    cliente,
    resultado,
    historico,
  } = route.params;

  const corFaixa = CORES[resultado.faixa] ?? '#555';

  const nomeExibido = historico?.clienteNome ?? cliente.nome;

  return (
    <ScrollView
      style={estilos.tela}
      contentContainerStyle={estilos.container}
    >
      {historico && (
        <View style={estilos.avisoHistorico}>
          <Text style={estilos.avisoHistoricoTexto}>
            Avaliação anterior
          </Text>

          <Text style={estilos.avisoHistoricoDescricao}>
            Este resultado foi recuperado do histórico.
            O risco não foi recalculado.
          </Text>
        </View>
      )}

      <Text style={estilos.nomeCliente}>
        {nomeExibido}
      </Text>

      <View
        style={[
          estilos.cartaoRisco,
          { borderColor: corFaixa },
        ]}
      >
        <Text
          style={[
            estilos.faixaTexto,
            { color: corFaixa },
          ]}
        >
          {resultado.rotulo_faixa}
        </Text>

        <Text style={estilos.dataAvaliacao}>
          Avaliado em {formatarData(resultado.gerado_em)}
        </Text>
      </View>

      <Text style={estilos.tituloSecao}>
        Por que este resultado?
      </Text>

      <Text style={estilos.ajudaSecao}>
        Confira os fatores que mais contribuíram para
        esta avaliação, apresentados em ordem de importância.
      </Text>

      {resultado.fatores.map((fator, index) => (
        <CartaoFator
          key={`${fator.campo}-${index}`}
          fator={fator}
          posicao={index + 1}
        />
      ))}

      {historico && (
        <View style={estilos.cartaoHistorico}>
          <Text style={estilos.tituloSecao}>
            Dados utilizados nesta avaliação
          </Text>

          <Text style={estilos.ajudaSecao}>
            Estes valores foram preservados no momento
            da avaliação. Alterações posteriores no
            cadastro do cliente não modificam este registro.
          </Text>

          <Text style={estilos.detalhe}>
            Registro: {historico.id ?? 'Sem identificador'}
          </Text>

          <Text style={estilos.detalhe}>
            Salvo em: {formatarData(historico.criadoEm)}
          </Text>

          <View style={estilos.separador} />

          {Object.entries(historico.entrada).map(
            ([campo, valor]) => (
              <View
                key={campo}
                style={estilos.linhaAtributo}
              >
                <Text style={estilos.nomeAtributo}>
                  {ROTULOS_ENTRADA[campo] ?? campo}
                </Text>

                <Text style={estilos.valorAtributo}>
                  {String(valor)}
                </Text>
              </View>
            )
          )}

          <Text style={estilos.observacao}>
            Valores exibidos conforme enviados à API.
            Os campos categóricos mantêm sua codificação
            numérica original.
          </Text>
        </View>
      )}

      <Text style={estilos.rodape}>
        Modelo: {resultado.modelo_versao}
      </Text>
    </ScrollView>
  );
}

const estilos = StyleSheet.create({
  tela: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  container: {
    padding: 20,
    paddingBottom: 48,
  },
  avisoHistorico: {
    backgroundColor: '#E3F2FD',
    padding: 14,
    borderRadius: 10,
    marginBottom: 20,
  },
  avisoHistoricoTexto: {
    color: '#1565C0',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  avisoHistoricoDescricao: {
    color: '#315A80',
    fontSize: 13,
    lineHeight: 19,
  },
  nomeCliente: {
    fontSize: 16,
    fontWeight: '600',
    color: '#555',
    marginBottom: 12,
  },
  cartaoRisco: {
    borderWidth: 2,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    padding: 22,
    alignItems: 'center',
    marginBottom: 28,
  },
  faixaTexto: {
    fontSize: 26,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  dataAvaliacao: {
    fontSize: 12,
    color: '#777',
    marginTop: 10,
    textAlign: 'center',
  },
  tituloSecao: {
    fontSize: 18,
    color: '#222',
    fontWeight: 'bold',
    marginBottom: 8,
  },
  ajudaSecao: {
    fontSize: 13,
    color: '#666',
    lineHeight: 20,
    marginBottom: 16,
  },
  cartaoFator: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 14,
    elevation: 1,
    shadowColor: '#000',
    shadowOpacity: 0.07,
    shadowRadius: 4,
  },
  fatorNome: {
    fontSize: 16,
    color: '#222',
    fontWeight: '600',
    marginBottom: 10,
  },
  selo: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
    marginBottom: 14,
  },
  seloTexto: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  barraFundo: {
    height: 7,
    backgroundColor: '#EAECEF',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 16,
  },
  barra: {
    height: 7,
    borderRadius: 4,
  },
  acaoTitulo: {
    fontSize: 12,
    color: '#007BFF',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  acaoTexto: {
    fontSize: 14,
    color: '#333',
    lineHeight: 21,
  },
  cartaoHistorico: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
  },
  detalhe: {
    fontSize: 13,
    color: '#555',
    marginBottom: 8,
  },
  separador: {
    height: 1,
    backgroundColor: '#EAECEF',
    marginVertical: 14,
  },
  linhaAtributo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottomWidth: 1,
    borderBottomColor: '#EEEEEE',
    paddingVertical: 10,
    gap: 16,
  },
  nomeAtributo: {
    flex: 1,
    fontSize: 13,
    color: '#555',
  },
  valorAtributo: {
    fontSize: 13,
    fontWeight: '600',
    color: '#222',
  },
  observacao: {
    marginTop: 16,
    fontSize: 12,
    color: '#888',
    lineHeight: 18,
  },
  rodape: {
    marginTop: 26,
    fontSize: 12,
    color: '#888',
    textAlign: 'center',
  },
});
