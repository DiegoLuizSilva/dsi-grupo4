import React from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { NavigationContainer } from '@react-navigation/native';

import ClientList from '../screens/ClientList';
import ClientForm from '../screens/ClientForm';
import PredictResult from '../screens/PredictResult';
import Login from '../screens/Login';
import { useAuth } from '../contexts/AuthContext';
import { RootStackParamList } from '../types';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator<RootStackParamList>();
const Root = createNativeStackNavigator();

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

function AbasAutenticadas() {
  return (
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
  );
}

export default function Routes() {
  const { autenticado, carregando, sair } = useAuth();

  if (carregando) {
    return (
      <View style={estilos.carregando}>
        <ActivityIndicator size="large" color="#2E5496" />
        <Text style={estilos.carregandoTexto}>Verificando sua sessão...</Text>
      </View>
    );
  }

  const encerrar = async () => {
    try {
      await sair();
    } catch (erro) {
      console.error(erro);
      Alert.alert('Erro', 'Não foi possível encerrar a sessão. Tente novamente.');
    }
  };

  return (
    <NavigationContainer>
      <Root.Navigator>
        {autenticado ? (
          <Root.Screen
            name="Aplicativo"
            component={AbasAutenticadas}
            options={{
              title: 'ChurnGuard',
              headerTitleAlign: 'center',
              headerRight: () => (
                <TouchableOpacity onPress={encerrar} accessibilityRole="button">
                  <Text style={estilos.sair}>Sair</Text>
                </TouchableOpacity>
              ),
            }}
          />
        ) : (
          <Root.Screen name="Login" component={Login} options={{ headerShown: false }} />
        )}
      </Root.Navigator>
    </NavigationContainer>
  );
}

const estilos = StyleSheet.create({
  carregando: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F5F7FA',
  },
  carregandoTexto: { color: '#52606D', fontSize: 14, marginTop: 12 },
  sair: { color: '#2E5496', fontSize: 15, fontWeight: '600' },
});
