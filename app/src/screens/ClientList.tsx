import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity, Alert } from 'react-native';
import { listarClientes } from '../services/dbService';
import { analisarRiscoCliente } from '../services/churnService';

export default function ClientList() {
  const [clientes, setClientes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Carrega os dados assim que a tela abre
  useEffect(() => {
    carregarClientes();
  }, []);

  const carregarClientes = async () => {
    setLoading(true);
    try {
      const dados = await listarClientes();
      setClientes(dados);
    } catch (error) {
      Alert.alert('Erro', 'Não foi possível carregar a lista de clientes.');
    } finally {
      setLoading(false);
    }
  };

  const handleAvaliarRisco = async (cliente: any) => {
    try {
      Alert.alert('Aguarde', 'Calculando risco na API Python...');
      const resultado = await analisarRiscoCliente(cliente);
      Alert.alert(
        'Resultado', 
        `Risco: ${resultado.rotulo_faixa}\nProbabilidade: ${(resultado.probabilidade * 100).toFixed(1)}%`
      );
    } catch (error: any) {
      console.error("Erro capturado na tela:", error?.message || error);

      Alert.alert('Erro', 'A API FastAPI precisa estar rodando para avaliar o risco.');
    }
  };

  const renderItem = ({ item }: { item: any }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.nome}</Text>
      <Text style={styles.info}>CPF: {item.cpf}  |  Idade: {item.age}</Text>
      
      <TouchableOpacity 
        style={styles.button} 
        onPress={() => handleAvaliarRisco(item)}
      >
        <Text style={styles.buttonText}>Avaliar Risco de Churn</Text>
      </TouchableOpacity>
    </View>
  );

  if (loading && clientes.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#007BFF" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Clientes Cadastrados</Text>
      
      <FlatList
        data={clientes}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        // Adiciona a funcionalidade de "puxar para recarregar"
        onRefresh={carregarClientes}
        refreshing={loading}
        ListEmptyComponent={<Text style={styles.empty}>Nenhum cliente cadastrado.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    textAlign: 'center',
    marginVertical: 20,
  },
  list: {
    paddingHorizontal: 15,
    paddingBottom: 20,
  },
  card: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    elevation: 2, // Sombra no Android
    shadowColor: '#000', // Sombra no iOS
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  name: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  info: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
  },
  button: {
    backgroundColor: '#007BFF',
    padding: 10,
    borderRadius: 5,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  empty: {
    textAlign: 'center',
    marginTop: 50,
    color: '#888',
  }
});