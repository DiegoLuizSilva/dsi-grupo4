import React, { useState } from 'react';
import { View, TextInput, Button, Alert, StyleSheet } from 'react-native';
import { criarCliente } from '../services/dbService'; // Ajuste o caminho se necessário

export default function ClientForm({ navigation }: any) {
  // Substitua pelos estados reais que você já tem no seu formulário
  const [nome, setNome] = useState('');
  const [cpf, setCpf] = useState('');
  const [idade, setIdade] = useState('');

  const handleSalvar = async () => {
    if (!nome || !cpf || !idade) {
      Alert.alert('Aviso', 'Preencha todos os campos obrigatórios.');
      return;
    }

    try {
      // Chama a função do Firebase isolada na camada de serviços
      await criarCliente({
        nome,
        cpf,
        idade: Number(idade),
      });

      Alert.alert('Sucesso', 'Cliente cadastrado no banco!');
      navigation.goBack(); // Retorna para a tela de lista após salvar
    } catch (error) {
      console.error(error);
      Alert.alert('Erro', 'Não foi possível salvar o cliente.');
    }
  };

  return (
    <View style={styles.container}>
      <TextInput placeholder="Nome" value={nome} onChangeText={setNome} />
      <TextInput placeholder="CPF" value={cpf} onChangeText={setCpf} keyboardType="numeric" />
      <TextInput placeholder="Idade" value={idade} onChangeText={setIdade} keyboardType="numeric" />
      
      <Button title="Salvar" onPress={handleSalvar} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, gap: 10 }
});