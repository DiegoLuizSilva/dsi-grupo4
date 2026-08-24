// app/App.js
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

// Importando as telas
import ClientList from './src/screens/ClientList';
import ClientForm from './src/screens/ClientForm';
import PredictForm from './src/screens/PredictForm';
import PredictResult from './src/screens/PredictResult';
import ClientHistory from './src/screens/ClientHistory';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="ClientList">
        <Stack.Screen name="ClientList" component={ClientList} options={{ title: 'Clientes' }} />
        <Stack.Screen name="ClientForm" component={ClientForm} options={{ title: 'Cadastro de Cliente' }} />
        <Stack.Screen name="PredictForm" component={PredictForm} options={{ title: 'Análise de Risco' }} />
        <Stack.Screen name="PredictResult" component={PredictResult} options={{ title: 'Resultado' }} />
        <Stack.Screen name="ClientHistory" component={ClientHistory} options={{ title: 'Histórico' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}