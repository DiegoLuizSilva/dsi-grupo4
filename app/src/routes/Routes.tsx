import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { NavigationContainer } from '@react-navigation/native';

// Importe as suas telas reais aqui
import ClientList from '../screens/ClientList'; 
import ClientForm from '../screens/ClientForm';

const Tab = createBottomTabNavigator();

export default function Routes() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={{
          tabBarActiveTintColor: '#007BFF',
          tabBarInactiveTintColor: 'gray',
          headerTitleAlign: 'center',
        }}
      >
        <Tab.Screen 
          name="Listagem" 
          component={ClientList} 
          options={{ title: 'Meus Clientes' }}
        />
        <Tab.Screen 
          name="Cadastro" 
          component={ClientForm} 
          options={{ title: 'Novo Cliente' }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}