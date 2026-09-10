import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { NavigationContainer } from '@react-navigation/native';

import ClientList from '../screens/ClientList';
import ClientForm from '../screens/ClientForm';
import PredictResult from '../screens/PredictResult';
import { RootStackParamList } from '../types';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator<RootStackParamList>();

// Pilha da aba de clientes: listagem, edição e resultado da análise.
function PilhaClientes() {
  return (
    <Stack.Navigator screenOptions={{ headerTitleAlign: 'center' }}>
      <Stack.Screen name="ClientList" component={ClientList} options={{ title: 'Meus Clientes' }} />
      <Stack.Screen name="ClientForm" component={ClientForm} options={{ title: 'Editar Cliente' }} />
      <Stack.Screen
        name="PredictResult"
        component={PredictResult}
        options={{ title: 'Resultado da Análise' }}
      />
    </Stack.Navigator>
  );
}

// Pilha da aba de cadastro. Usa a mesma tela, sem parâmetro de cliente.
function PilhaCadastro() {
  return (
    <Stack.Navigator screenOptions={{ headerTitleAlign: 'center' }}>
      <Stack.Screen name="ClientForm" component={ClientForm} options={{ title: 'Novo Cliente' }} />
    </Stack.Navigator>
  );
}

export default function Routes() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={{
          tabBarActiveTintColor: '#007BFF',
          tabBarInactiveTintColor: 'gray',
          headerShown: false,
        }}
      >
        <Tab.Screen name="Clientes" component={PilhaClientes} options={{ title: 'Clientes' }} />
        <Tab.Screen name="Cadastro" component={PilhaCadastro} options={{ title: 'Novo Cliente' }} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}