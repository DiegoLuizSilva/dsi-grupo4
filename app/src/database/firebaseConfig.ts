import AsyncStorage from '@react-native-async-storage/async-storage';
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
// getReactNativePersistence existe no bundle React Native do Firebase, mas não
// aparece nos tipos públicos de 'firebase/auth'. O import abaixo funciona em
// tempo de execução; o comentário evita o erro de tipagem.
// @ts-ignore
import { getReactNativePersistence, initializeAuth } from 'firebase/auth';

// A configuração do Firebase para web não é secreta: ela é embutida no bundle
// do aplicativo. A chave fica em variável de ambiente apenas para facilitar a
// troca de projeto entre ambientes, não como medida de segurança. O controle
// de acesso real é feito pelas regras do Firestore, no console do Firebase.
const firebaseConfig = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY,
  authDomain: 'chunguard.firebaseapp.com',
  projectId: 'chunguard',
  storageBucket: 'chunguard.firebasestorage.app',
  messagingSenderId: '71201998072',
  appId: '1:71201998072:web:06471cbb000705d370670d',
};

if (!firebaseConfig.apiKey) {
  throw new Error(
    'EXPO_PUBLIC_FIREBASE_API_KEY não definida. ' +
      'Copie app/.env.example para app/.env e preencha a chave antes de rodar o app.'
  );
}

export const app = initializeApp(firebaseConfig);

// Instância única do Firestore.
export const db = getFirestore(app);

// initializeAuth com AsyncStorage mantém a sessão após fechar o aplicativo.
// getAuth() sozinho guardaria a sessão apenas em memória no React Native.
export const auth = initializeAuth(app, {
  persistence: getReactNativePersistence(AsyncStorage),
});