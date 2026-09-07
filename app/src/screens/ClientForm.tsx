import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert, ScrollView, ActivityIndicator } from 'react-native';
import { criarCliente } from '../services/dbService';

type FormState = {
  nome: string;
  cpf: string;
  age: string;
};
function calcularAgeGroup(idade: number): number {
  if (idade <= 20) return 1;
  if (idade <= 30) return 2;
  if (idade <= 40) return 3;
  if (idade <= 50) return 4;
  return 5; // Qualquer idade acima de 50 anos fica limitada ao teto 5
}

export default function ClientForm() {
  const [formData, setFormData] = useState<FormState>({
    nome: '',
    cpf: '',
    age: ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (name: keyof FormState, value: string) => {
    setFormData(prevState => ({ ...prevState, [name]: value }));
  };

  const handleSalvar = async () => {
    const nomeLimpo = formData.nome.trim();
    const cpfLimpo = formData.cpf.replace(/\D/g, '');
    const idadeNum = parseInt(formData.age, 10);

    if (!nomeLimpo || !cpfLimpo || !formData.age.trim()) {
      Alert.alert('Atenção', 'Preencha todos os campos.');
      return;
    }

    if (isNaN(idadeNum) || idadeNum <= 0 || idadeNum > 120) {
      Alert.alert('Atenção', 'Informe uma idade válida.');
      return;
    }

    if (cpfLimpo.length !== 11) {
      Alert.alert('Atenção', 'O CPF deve conter 11 dígitos.');
      return;
    }

    setLoading(true);

    try {
      await criarCliente({
        nome: nomeLimpo,
        cpf: cpfLimpo,
        age: idadeNum,
        callFailure: 0,
        complains: false,
        subscriptionLength: 0,
        chargeAmount: 0,
        secondsOfUse: 0,
        frequencyOfUse: 0,
        frequencyOfSMS: 0,
        distinctCalledNumbers: 0,
        status: true,
        ageGroup: calcularAgeGroup(idadeNum),
        tariffPlan: 1,
        customerValue: 0,
        churn: false
      });
      
      Alert.alert('Sucesso', 'Cliente cadastrado com sucesso!');
      setFormData({ nome: '', cpf: '', age: '' });
      
    } catch (error) {
      Alert.alert('Erro', 'Ocorreu um problema ao salvar o cliente.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>Novo Cliente</Text>

      <Text style={styles.label}>Nome Completo</Text>
      <TextInput 
        style={styles.input} 
        value={formData.nome} 
        onChangeText={(text) => handleChange('nome', text)} 
        placeholder="Ex: João da Silva"
        autoCapitalize="words"
      />

      <Text style={styles.label}>CPF</Text>
      <TextInput 
        style={styles.input} 
        value={formData.cpf} 
        onChangeText={(text) => handleChange('cpf', text)} 
        keyboardType="numeric" 
        maxLength={14}
        placeholder="Somente números ou com pontuação"
      />

      <Text style={styles.label}>Idade</Text>
      <TextInput 
        style={styles.input} 
        value={formData.age} 
        onChangeText={(text) => handleChange('age', text)} 
        keyboardType="numeric" 
        maxLength={3}
        placeholder="Ex: 25"
      />

      <View style={styles.buttonContainer}>
        {loading ? (
          <ActivityIndicator size="small" color="#007BFF" />
        ) : (
          <Button title="Salvar Cliente" onPress={handleSalvar} color="#007BFF" />
        )}
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
    minHeight: 40,
    justifyContent: 'center',
  }
});