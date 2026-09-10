import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { RouteProp, useRoute } from '@react-navigation/native';

import { Fator, RootStackParamList } from '../types';

// Cor por faixa. O rótulo textual é sempre exibido junto, para que a
// distinção não dependa apenas de cor (RNF08).
const CORES: Record<string, string> = {
  baixo: '#2E7D32',
  medio: '#ED6C02',
  alto: '#C62828',
};

type Rota = RouteProp<RootStackParamList, 'PredictResult'>;

function formatarData(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('pt-BR');
}

function CartaoFator({ fator, posicao }: { fator: Fator; posicao: number }) {
  const aumenta = fator.impacto === 'aumenta';
  return (
    <View style={estilos.fator}>
      <View style={estilos.fatorTopo}>
        <Text style={estilos.fatorRotulo}>
          {posicao}. {fator.rotulo}
        </Text>
        <View style={[estilos.selo, { backgroundColor: aumenta ? '#FDECEA' : '#E8F5E9' }]}>
          <Text style={[estilos.seloTexto, { color: aumenta ? '#C62828' : '#2E7D32' }]}>
            {aumenta ? 'aumenta o risco' : 'reduz o risco'}
          </Text>
        </View>
      </View>

      <View style={estilos.barraFundo}>
        <View
          style={[
            estilos.barra,
            {
              width: `${Math.max(4, Math.min(100, fator.peso * 100))}%`,
              backgroundColor: aumenta ? '#C62828' : '#2E7D32',
            },
          ]}
        />
      </View>

      <Text style={estilos.acaoTitulo}>Ação sugerida</Text>
      <Text style={estilos.acaoTexto}>{fator.sugestao}</Text>
    </View>
  );
}

export default function PredictResult() {
  const route = useRoute<Rota>();
  const { cliente, resultado } = route.params;

  const cor = CORES[resultado.faixa] ?? '#555';

  return (
    <ScrollView contentContainerStyle={estilos.container}>
      <Text style={estilos.cliente}>{cliente.nome}</Text>

      <View style={[estilos.faixa, { borderColor: cor }]}>
        <Text style={[estilos.faixaTexto, { color: cor }]}>{resultado.rotulo_faixa}</Text>
        <Text style={estilos.faixaData}>Avaliado em {formatarData(resultado.gerado_em)}</Text>
      </View>

      <Text style={estilos.secao}>Por que este resultado</Text>
      <Text style={estilos.secaoAjuda}>
        Atributos que mais pesaram nesta avaliação, do maior para o menor.
      </Text>

      {resultado.fatores.map((f, i) => (
        <CartaoFator key={f.campo} fator={f} posicao={i + 1} />
      ))}

      <Text style={estilos.rodape}>Modelo: {resultado.modelo_versao}</Text>
    </ScrollView>
  );
}

const estilos = StyleSheet.create({
  container: { padding: 20, paddingBottom: 48, backgroundColor: '#f5f5f5', flexGrow: 1 },
  cliente: { fontSize: 15, color: '#666', marginBottom: 10 },
  faixa: {
    borderWidth: 2,
    borderRadius: 12,
    paddingVertical: 22,
    paddingHorizontal: 16,
    alignItems: 'center',
    backgroundColor: '#fff',
    marginBottom: 28,
  },
  faixaTexto: { fontSize: 26, fontWeight: 'bold' },
  faixaData: { fontSize: 12, color: '#888', marginTop: 8 },
  secao: { fontSize: 17, fontWeight: 'bold', marginBottom: 4 },
  secaoAjuda: { fontSize: 13, color: '#777', marginBottom: 16 },
  fator: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    marginBottom: 14,
    elevation: 1,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 3,
  },
  fatorTopo: { marginBottom: 10 },
  fatorRotulo: { fontSize: 16, fontWeight: '600', marginBottom: 8 },
  selo: { alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  seloTexto: { fontSize: 12, fontWeight: 'bold' },
  barraFundo: {
    height: 6,
    backgroundColor: '#EAECEF',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 14,
  },
  barra: { height: 6, borderRadius: 3 },
  acaoTitulo: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#007BFF',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  acaoTexto: { fontSize: 14, lineHeight: 20, color: '#333' },
  rodape: { fontSize: 11, color: '#aaa', textAlign: 'center', marginTop: 12 },
});