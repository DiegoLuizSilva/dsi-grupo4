import React, { useCallback, useState } from 'react';
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

import { listarClientes, removerCliente } from '../services/dbService';
import { analisarRiscoCliente } from '../services/churnService';
import { Cliente } from '../types';

export default function ClientList() {
  const navigation = useNavigation<any>();
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [avaliandoId, setAvaliandoId] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      setClientes(await listarClientes());
    } catch (e) {
      console.error(e);
      Alert.alert('Erro', 'Não foi possível carregar a lista de clientes.');
    } finally {
      setCarregando(false);
    }
  }, []);

  // Recarrega sempre que a tela volta ao foco, para refletir edições.
  useFocusEffect(
    useCallback(() => {
      carregar();
    }, [carregar])
  );

  const avaliar = async (cliente: Cliente) => {
    setAvaliandoId(cliente.id ?? null);
    try {
      const resultado = await analisarRiscoCliente(cliente);
      navigation.navigate('PredictResult', { cliente, resultado });
    } catch (erro: any) {
      console.error(erro?.message ?? erro);
      Alert.alert(
        'Serviço indisponível',
        'Não foi possível calcular o risco agora. Verifique se a API está no ar e tente novamente.'
      );
    } finally {
      setAvaliandoId(null);
    }
  };

  const editar = (cliente: Cliente) => navigation.navigate('ClientForm', { cliente });

  const excluir = (cliente: Cliente) => {
    Alert.alert(
      'Remover cliente',
      `Remover ${cliente.nome} da sua lista? Esta ação não pode ser desfeita.`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Remover',
          style: 'destructive',
          onPress: async () => {
            try {
              if (cliente.id) await removerCliente(cliente.id);
              await carregar();
            } catch (e) {
              console.error(e);
              Alert.alert('Erro', 'Não foi possível remover o cliente.');
            }
          },
        },
      ]
    );
  };

  const renderItem = ({ item }: { item: Cliente }) => {
    const avaliando = avaliandoId === item.id;
    return (
      <View style={estilos.cartao}>
        <Text style={estilos.nome}>{item.nome}</Text>
        <Text style={estilos.info}>
          {item.age} anos · {item.tariffPlan === 2 ? 'Pós-pago' : 'Pré-pago'} ·{' '}
          {item.status === false ? 'Linha inativa' : 'Linha ativa'}
        </Text>

        <TouchableOpacity
          style={[estilos.botao, avaliando && estilos.botaoDesativado]}
          onPress={() => avaliar(item)}
          disabled={avaliando}
        >
          {avaliando ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={estilos.botaoTexto}>Avaliar risco de cancelamento</Text>
          )}
        </TouchableOpacity>

        <View style={estilos.linhaSecundaria}>
          <TouchableOpacity style={estilos.secundario} onPress={() => editar(item)}>
            <Text style={estilos.secundarioTexto}>Editar</Text>
          </TouchableOpacity>
          <TouchableOpacity style={estilos.secundario} onPress={() => excluir(item)}>
            <Text style={[estilos.secundarioTexto, estilos.perigo]}>Remover</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  if (carregando && clientes.length === 0) {
    return (
      <View style={estilos.centro}>
        <ActivityIndicator size="large" color="#007BFF" />
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
            Nenhum cliente cadastrado. Use a aba Novo Cliente para começar.
          </Text>
        }
      />
    </View>
  );
}

const estilos = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  lista: { padding: 15, paddingBottom: 24 },
  cartao: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  nome: { fontSize: 18, fontWeight: 'bold', marginBottom: 4 },
  info: { fontSize: 13, color: '#666', marginBottom: 14 },
  botao: {
    backgroundColor: '#007BFF',
    paddingVertical: 11,
    borderRadius: 6,
    alignItems: 'center',
    minHeight: 42,
    justifyContent: 'center',
  },
  botaoDesativado: { backgroundColor: '#9AA5B1' },
  botaoTexto: { color: '#fff', fontWeight: 'bold' },
  linhaSecundaria: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 18,
    marginTop: 10,
  },
  secundario: { paddingVertical: 4 },
  secundarioTexto: { fontSize: 14, color: '#007BFF', fontWeight: '500' },
  perigo: { color: '#C62828' },
  vazio: { textAlign: 'center', marginTop: 60, color: '#888', paddingHorizontal: 30 },
});