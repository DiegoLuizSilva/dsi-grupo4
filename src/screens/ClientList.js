// src/screens/ClientList.js
import React from 'react';
import { View, Text, StyleSheet, Button } from 'react-native';

export default function ClientList({ navigation }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Lista de Clientes</Text>
      {/* Exemplo de como navegar para outra tela */}
      <Button 
        title="Adicionar Novo Cliente" 
        onPress={() => navigation.navigate('ClientForm')} 
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 20, fontWeight: 'bold', marginBottom: 20 },
});