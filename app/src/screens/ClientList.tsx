
import React, { useCallback, useRef, useState } from 'react';

import {
  ActivityIndicator,
  Alert,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { listarClientes, removerCliente } from '../services/dbService';
import { analisarRiscoCliente } from '../services/churnService';
import { salvarAvaliacao } from '../services/avaliacaoService';

import type { Cliente, RootStackParamList } from '../types';

type Navegacao = NativeStackNavigationProp<
  RootStackParamList,
  'ClientList'
>;

export default function ClientList() {
  const navigation = useNavigation<Navegacao>();

  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [avaliandoId, setAvaliandoId] = useState<string | null>(null);

  // Bloqueio imediato contra chamadas duplicadas.
  const avaliacaoEmAndamento = useRef(false);

  const carregar = useCallback(async () => {
    setCarregando(true);

    try {
      const registros = await listarClientes();
      setClientes(registros);
    } catch (erro) {
      console.error('Erro ao listar clientes:', erro);

      Alert.alert(
        'Erro',
        'Não foi possível carregar os clientes.'
      );
    } finally {
      setCarregando(false);
    }
  }, []);

  // Atualiza a lista quando o usuário retorna à tela.
  useFocusEffect(
    useCallback(() => {
      void carregar();
    }, [carregar])
  );

  const avaliar = async (cliente: Cliente) => {
    if (!cliente.id || avaliacaoEmAndamento.current) {
      return;
    }

    avaliacaoEmAndamento.current = true;
    setAvaliandoId(cliente.id);

    try {
      // Obtém a entrada utilizada e o resultado real da API.
      const { entrada, resultado } =
        await analisarRiscoCliente(cliente);

      let historicoSalvo = false;

      try {
        await salvarAvaliacao(cliente, entrada, resultado);
        historicoSalvo = true;
      } catch (erro) {
        console.error(
          'Falha ao registrar avaliação:',
          erro
        );
      }

      // O resultado continua disponível mesmo se a gravação falhar.
      navigation.navigate('PredictResult', {
        cliente,
        resultado,
      });

      if (!historicoSalvo) {
        Alert.alert(
          'Avaliação não registrada',
          'A análise foi concluída, mas não foi salva no histórico. Verifique a conexão e tente novamente.'
        );
      }
    } catch (erro) {
      console.error('Erro na avaliação:', erro);

      Alert.alert(
        'Serviço indisponível',
        'Não foi possível calcular o risco. Confira a conexão e tente novamente.'
      );
    } finally {
      avaliacaoEmAndamento.current = false;
      setAvaliandoId(null);
    }
  };

  const editar = (cliente: Cliente) => {
    navigation.navigate('ClientForm', { cliente });
  };

  const abrirHistorico = (cliente: Cliente) => {
    if (!cliente.id) {
      Alert.alert(
        'Erro',
        'Este cliente não possui identificador.'
      );
      return;
    }

    navigation.navigate('ClientHistory', {
      cliente,
    });
  };

  const excluir = (cliente: Cliente) => {
    Alert.alert(
      'Remover cliente',
      `Deseja realmente remover ${cliente.nome}?`,
      [
        {
          text: 'Cancelar',
          style: 'cancel',
        },
        {
          text: 'Remover',
          style: 'destructive',
          onPress: async () => {
            if (!cliente.id) return;

            try {
              await removerCliente(cliente.id);
              await carregar();
            } catch (erro) {
              console.error('Erro ao remover:', erro);

              Alert.alert(
                'Erro',
                'Não foi possível remover o cliente.'
              );
            }
          },
        },
      ]
    );
  };

  const renderItem = ({ item }: { item: Cliente }) => {
    const avaliandoEsteCliente = avaliandoId === item.id;
    const existeAvaliacaoEmAndamento = avaliandoId !== null;

    return (
      <View style={estilos.cartao}>
        <Text style={estilos.nome}>
          {item.nome}
        </Text>

        <Text style={estilos.informacoes}>
          {item.age} anos
          {' · '}
          {item.tariffPlan === 2 ? 'Pós-pago' : 'Pré-pago'}
          {' · '}
          {item.status === false
            ? 'Linha inativa'
            : 'Linha ativa'}
        </Text>

        <TouchableOpacity
          style={[
            estilos.botaoAvaliar,
            existeAvaliacaoEmAndamento &&
              estilos.botaoDesativado,
          ]}
          onPress={() => avaliar(item)}
          disabled={existeAvaliacaoEmAndamento}
          accessibilityRole="button"
        >
          {avaliandoEsteCliente ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={estilos.botaoAvaliarTexto}>
              Avaliar risco de cancelamento
            </Text>
          )}
        </TouchableOpacity>

        <View style={estilos.acoes}>
          <TouchableOpacity
            style={estilos.acao}
            onPress={() => editar(item)}
            accessibilityRole="button"
          >
            <Text style={estilos.acaoTexto}>
              Editar
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={estilos.acao}
            onPress={() => abrirHistorico(item)}
            accessibilityRole="button"
          >
            <Text style={estilos.acaoTexto}>
              Histórico
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={estilos.acao}
            onPress={() => excluir(item)}
            accessibilityRole="button"
          >
            <Text style={estilos.removerTexto}>
              Remover
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  if (carregando && clientes.length === 0) {
    return (
      <View style={estilos.centro}>
        <ActivityIndicator
          size="large"
          color="#007BFF"
        />
        <Text style={estilos.carregandoTexto}>
          Carregando clientes...
        </Text>
      </View>
    );
  }

  return (
    <View style={estilos.container}>
      <FlatList
        data={clientes}
        keyExtractor={(item) => item.id ?? item.nome}
        renderItem={renderItem}
        contentContainerStyle={estilos.lista}
        onRefresh={carregar}
        refreshing={carregando}
        ListEmptyComponent={
          <Text style={estilos.vazio}>
            Nenhum cliente cadastrado.
            {'\n'}
            Use a aba Novo Cliente para começar.
          </Text>
        }
      />
    </View>
  );
}

const estilos = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  centro: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  carregandoTexto: {
    marginTop: 12,
    color: '#666',
  },
  lista: {
    padding: 16,
    paddingBottom: 32,
  },
  cartao: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 4,
  },
  nome: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#222',
    marginBottom: 6,
  },
  informacoes: {
    fontSize: 13,
    color: '#666',
    marginBottom: 16,
  },
  botaoAvaliar: {
    backgroundColor: '#007BFF',
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 8,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  botaoDesativado: {
    backgroundColor: '#9AA5B1',
  },
  botaoAvaliarTexto: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    textAlign: 'center',
  },
  acoes: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 14,
    gap: 8,
  },
  acao: {
    paddingVertical: 8,
    paddingHorizontal: 4,
  },
  acaoTexto: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007BFF',
  },
  removerTexto: {
    fontSize: 14,
    fontWeight: '600',
    color: '#C62828',
  },
  vazio: {
    marginTop: 60,
    textAlign: 'center',
    fontSize: 15,
    color: '#777',
    lineHeight: 24,
  },
});
