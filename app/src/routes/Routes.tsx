
import React from 'react';
import {
  ActivityIndicator,
  Alert,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { NavigationContainer } from '@react-navigation/native';
import { Feather } from '@expo/vector-icons';

import Home from '../screens/Home';
import ClientList from '../screens/ClientList';
import ClientForm from '../screens/ClientForm';
import ClientHistory from '../screens/ClientHistory';
import PredictResult from '../screens/PredictResult';
import Login from '../screens/Login';
import SignUp from '../screens/SignUp';

import { useAuth } from '../contexts/AuthContext';
import type { RootStackParamList } from '../types';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator<RootStackParamList>();
const Root = createNativeStackNavigator();

// Pilha da aba de clientes:
// listagem, edição, histórico e resultado da análise.
function PilhaClientes() {
  return (
    <Stack.Navigator
      screenOptions={{ headerTitleAlign: 'center' }}
    >
      <Stack.Screen
        name="ClientList"
        component={ClientList}
        options={{ title: 'Meus Clientes' }}
      />

      <Stack.Screen
        name="ClientForm"
        component={ClientForm}
        options={{ title: 'Editar Cliente' }}
      />

      {/* Histórico de avaliações do cliente */}
      <Stack.Screen
        name="ClientHistory"
        component={ClientHistory}
        options={{ title: 'Histórico de Avaliações' }}
      />

      {/* Resultado de uma avaliação nova ou antiga */}
      <Stack.Screen
        name="PredictResult"
        component={PredictResult}
        options={{ title: 'Resultado da Análise' }}
      />
    </Stack.Navigator>
  );
}

// Pilha da aba de cadastro.
// Usa a mesma tela, sem parâmetro de cliente.
function PilhaCadastro() {
  return (
    <Stack.Navigator
      screenOptions={{ headerTitleAlign: 'center' }}
    >
      <Stack.Screen
        name="ClientForm"
        component={ClientForm}
        options={{ title: 'Novo Cliente' }}
      />
    </Stack.Navigator>
  );
}

// Ícone de cada aba, na cor que a barra repassa
// (ativa ou inativa).
function iconeDaAba(
  nome: React.ComponentProps<typeof Feather>['name']
) {
  return ({
    color,
    size,
  }: {
    color: string;
    size: number;
  }) => (
    <Feather
      name={nome}
      size={size}
      color={color}
    />
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
      <Tab.Screen
        name="Home"
        component={Home}
        options={{
          title: 'Início',
          tabBarIcon: iconeDaAba('home'),
        }}
      />

      <Tab.Screen
        name="Clientes"
        component={PilhaClientes}
        options={{
          title: 'Clientes',
          tabBarIcon: iconeDaAba('users'),
        }}
      />

      <Tab.Screen
        name="Cadastro"
        component={PilhaCadastro}
        options={{
          title: 'Novo Cliente',
          tabBarIcon: iconeDaAba('user-plus'),
        }}
      />
    </Tab.Navigator>
  );
}

export default function Routes() {
  const { autenticado, carregando, sair } = useAuth();

  if (carregando) {
    return (
      <View style={estilos.carregando}>
        <ActivityIndicator
          size="large"
          color="#2E5496"
        />

        <Text style={estilos.carregandoTexto}>
          Verificando sua sessão...
        </Text>
      </View>
    );
  }

  const encerrar = async () => {
    try {
      await sair();
    } catch (erro) {
      console.error(erro);

      Alert.alert(
        'Erro',
        'Não foi possível encerrar a sessão. Tente novamente.'
      );
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
                <TouchableOpacity
                  onPress={encerrar}
                  accessibilityRole="button"
                >
                  <Text style={estilos.sair}>
                    Sair
                  </Text>
                </TouchableOpacity>
              ),
            }}
          />
        ) : (
          <>
            <Root.Screen
              name="Login"
              component={Login}
              options={{ headerShown: false }}
            />

            <Root.Screen
              name="SignUp"
              component={SignUp}
              options={{ headerShown: false }}
            />
          </>
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

  carregandoTexto: {
    color: '#52606D',
    fontSize: 14,
    marginTop: 12,
  },

  sair: {
    color: '#2E5496',
    fontSize: 15,
    fontWeight: '600',
  },
});
