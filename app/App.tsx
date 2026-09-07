import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Routes from './src/routes/Routes'; // ajuste o caminho relativo se routes estiver na raiz

export default function App() {
  return (
    <SafeAreaProvider>
      <StatusBar style="auto" />
      <Routes />
    </SafeAreaProvider>
  );
}