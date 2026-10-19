
import React, { useCallback, useState } from 'react';

import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import {
  useFocusEffect,
  useNavigation,
  useRoute,
} from '@react-navigation/native';

import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { listarAvaliacoes } from '../services/avaliacaoService';

import type {
  Avaliacao,
  RootStackParamList,
} from '../types';

type RotaHistorico = RouteProp<
  RootStackParamList,
  'ClientHistory'
>;

type NavegacaoHistorico = NativeStackNavigationProp<
  RootStackParamList,
  'ClientHistory'
>;

function formatarData(data: Date): string {
  if (!(data instanceof Date) || Number.isNaN(data.getTime())) {
    return 'Data indisponível';
  }

  return data.toLocaleString('pt-BR');
}

const CORES: Record<string, string> = {
  baixo: '#2E7D32',
  medio: '#ED6C02',
  alto: '#C62828',
};

export default function ClientHistory() {
  // Cliente recebido da tela ClientList.
  const route = useRoute<RotaHistorico>();
  const { cliente } = route.params;

  const navigation = useNavigation<NavegacaoHistorico>();

  const [avaliacoes, setAvaliacoes] = useState<Avaliacao[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    const clienteId = cliente.id;

    if (!clienteId) {
      setErro('Cliente sem identificador.');
      setCarregando(false);
      return;
    }

    setCarregando(true);
    setErro(null);

    try {
      const registros = await listarAvaliacoes(clienteId);
      setAvaliacoes(registros);
    } catch (falha) {
      console.error('Erro ao carregar histórico:', falha);
      setErro(
        'Não foi possível consultar o histórico. Verifique sua conexão.'
      );
    } finally {
      setCarregando(false);
    }
  }, [cliente.id]);

  // Atualiza quando a tela recebe o foco.
  useFocusEffect(
    useCallback(() => {
      void carregar();
    }, [carregar])
  );

  /**
   * Abre uma avaliação já registrada.
   * Não realiza outra previsão.
   */
  const abrirDetalhes = (avaliacao: Avaliacao) => {
    navigation.navigate('PredictResult', {
      cliente,
      resultado: avaliacao.resultado,
      historico: {
        id: avaliacao.id,
        clienteNome: avaliacao.clienteNome,
        criadoEm: avaliacao.criadoEm.toISOString(),
        entrada: avaliacao.entrada,
      },
    });
  };

  const renderItem = ({ item }: { item: Avaliacao }) => {
    const cor = CORES[item.faixa] ?? '#555';

    return (
      <TouchableOpacity
        style={estilos.cartao}
        onPress={() => abrirDetalhes(item)}
        accessibilityRole="button"
        accessibilityLabel={`Ver avaliação de ${formatarData(item.criadoEm)}`}
      >
        <View style={estilos.cartaoTopo}>
          <Text style={[estilos.faixa, { color: cor }]}>
            {item.rotuloFaixa}
          </Text>

          <Text style={estilos.data}>
            {formatarData(item.criadoEm)}
          </Text>
        </View>

        <Text style={estilos.modelo}>
          Modelo: {item.modeloVersao}
        </Text>

        <Text style={estilos.identificador}>
          Avaliação: {item.id ?? 'Sem identificador'}
        </Text>

        <Text style={estilos.link}>
          Ver detalhes da avaliação →
        </Text>
      </TouchableOpacity>
    );
  };

  if (carregando && avaliacoes.length === 0 && !erro) {
    return (
      <View style={estilos.centro}>
        <ActivityIndicator
          size="large"
          color="#007BFF"
        />

        <Text style={estilos.mensagem}>
          Carregando histórico...
        </Text>
      </View>
    );
  }

  return (
    <View style={estilos.container}>
      <Text style={estilos.titulo}>
        Histórico de Avaliações
      </Text>

      <Text style={estilos.subtitulo}>
        Cliente: {cliente.nome}
      </Text>

      {erro ? (
        <View style={estilos.centro}>
          <Text style={estilos.erro}>
            {erro}
          </Text>

          <TouchableOpacity
            style={estilos.botaoTentar}
            onPress={carregar}
            accessibilityRole="button"
          >
            <Text style={estilos.botaoTentarTexto}>
              Tentar novamente
            </Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={avaliacoes}
          keyExtractor={(item, index) =>
            item.id ?? `avaliacao-${index}`
          }
          renderItem={renderItem}
          contentContainerStyle={estilos.lista}
          refreshing={carregando}
          onRefresh={carregar}
          ListEmptyComponent={
            <View style={estilos.vazioContainer}>
              <Text style={estilos.vazioTitulo}>
                Nenhuma avaliação encontrada
              </Text>

              <Text style={estilos.vazioTexto}>
                Este cliente ainda não possui avaliações
                registradas no histórico.
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const estilos = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
    paddingTop: 20,
  },
  centro: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  mensagem: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
  },
  titulo: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#222',
    marginHorizontal: 16,
    marginBottom: 6,
  },
  subtitulo: {
    fontSize: 14,
    color: '#666',
    marginHorizontal: 16,
    marginBottom: 16,
  },
  lista: {
    paddingHorizontal: 16,
    paddingBottom: 32,
    flexGrow: 1,
  },
  cartao: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 4,
  },
  cartaoTopo: {
    marginBottom: 10,
  },
  faixa: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 6,
  },
  data: {
    fontSize: 13,
    color: '#555',
  },
  modelo: {
    fontSize: 13,
    color: '#555',
    marginBottom: 4,
  },
  identificador: {
    fontSize: 11,
    color: '#888',
  },
  link: {
    marginTop: 14,
    fontSize: 14,
    fontWeight: '600',
    color: '#007BFF',
  },
  vazioContainer: {
    padding: 24,
    alignItems: 'center',
    marginTop: 40,
  },
  vazioTitulo: {
    fontSize: 17,
    fontWeight: 'bold',
    color: '#444',
    marginBottom: 8,
    textAlign: 'center',
  },
  vazioTexto: {
    fontSize: 14,
    color: '#777',
    lineHeight: 21,
    textAlign: 'center',
  },
  erro: {
    fontSize: 15,
    color: '#C62828',
    textAlign: 'center',
    marginBottom: 18,
  },
  botaoTentar: {
    backgroundColor: '#007BFF',
    borderRadius: 8,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  botaoTentarTexto: {
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
});
