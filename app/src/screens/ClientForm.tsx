import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert, ScrollView } from 'react-native';
import { criarCliente } from '../services/dbService';

export default function ClientForm() {
  // O estado controla apenas o que o usuário realmente digita
  const [formData, setFormData] = useState({
    nome: '',
    cpf: '',
    age: ''
  });

  const handleChange = (name: string, value: string) => {
    setFormData(prevState => ({ ...prevState, [name]: value }));
  };

  const handleSalvar = async () => {
    if (!formData.nome || !formData.cpf || !formData.age) {
      Alert.alert('Atenção', 'Preencha todos os campos.');
      return;
    }

    try {
      // Monta o objeto completo misturando os dados da tela com os valores invisíveis padrão
      await criarCliente({
        nome: formData.nome,
        cpf: formData.cpf,
        age: Number(formData.age),
        // Campos invisíveis preenchidos automaticamente com defaults
        callFailure: 0,
        complains: false,
        subscriptionLength: 0,
        chargeAmount: 0,
        secondsOfUse: 0,
        frequencyOfUse: 0,
        frequencyOfSMS: 0,
        distinctCalledNumbers: 0,
        status: true, // Assume true como "ativo" no cadastro
        ageGroup: Math.floor(Number(formData.age) / 10), // Calcula o grupo de idade automaticamente
        tariffPlan: 1, // Plano base
        customerValue: 0,
        churn: false
      });
      
      Alert.alert('Sucesso', 'Cliente cadastrado com sucesso!');
      setFormData({ nome: '', cpf: '', age: '' });
      
    } catch (error) {
      Alert.alert('Erro', 'Ocorreu um problema ao salvar o cliente.');
      console.error(error);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Novo Cliente</Text>

      <Text style={styles.label}>Nome Completo</Text>
      <TextInput 
        style={styles.input} 
        value={formData.nome} 
        onChangeText={(text) => handleChange('nome', text)} 
      />

      <Text style={styles.label}>CPF</Text>
      <TextInput 
        style={styles.input} 
        value={formData.cpf} 
        onChangeText={(text) => handleChange('cpf', text)} 
        keyboardType="numeric" 
      />

      <Text style={styles.label}>Idade</Text>
      <TextInput 
        style={styles.input} 
        value={formData.age} 
        onChangeText={(text) => handleChange('age', text)} 
        keyboardType="numeric" 
      />

      <View style={styles.buttonContainer}>
        <Button title="Salvar Cliente" onPress={handleSalvar} color="#007BFF" />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: '#fff',
    flexGrow: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  label: {
    fontSize: 16,
    marginBottom: 5,
    fontWeight: '500',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    marginBottom: 15,
    fontSize: 16,
  },
  buttonContainer: {
    marginTop: 10,
  }
});