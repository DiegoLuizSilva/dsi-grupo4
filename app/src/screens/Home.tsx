import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';

import { useAuth } from '../contexts/AuthContext';
import { obterPerfil } from '../services/perfilService';
import { Perfil } from '../types';

// Abas registradas em AbasAutenticadas. Declarado aqui porque só a Home
// precisa navegar entre abas.
type AbasParamList = {
  Home: undefined;
  Clientes: undefined;
  Cadastro: undefined;
};

type Navegacao = BottomTabNavigationProp<AbasParamList, 'Home'>;

function saudacaoDoHorario(): string {
  const hora = new Date().getHours();
  if (hora < 12) return 'Bom dia';
  if (hora < 18) return 'Boa tarde';
  return 'Boa noite';
}

// Usa só o primeiro nome. "Bom dia, João Pedro da Silva" fica longo demais
// para o cabeçalho em telas estreitas.
function primeiroNome(nome: string): string {
  return nome.trim().split(/\s+/)[0] ?? '';
}

export default function Home() {
  const navigation = useNavigation<Navegacao>();
  const { usuario, sair } = useAuth();
  const [perfil, setPerfil] = useState<Perfil | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [saindo, setSaindo] = useState(false);

  useEffect(() => {
    let ativo = true;

    async function carregar() {
      if (!usuario) {
        if (ativo) setCarregando(false);
        return;
      }

      try {
        const encontrado = await obterPerfil(usuario.uid);
        if (ativo) setPerfil(encontrado);
      } catch (erro) {
        // A saudação cai para o displayName do Auth. Falha ao ler o perfil
        // não deve impedir o uso do aplicativo.
        console.error(erro);
      } finally {
        if (ativo) setCarregando(false);
      }
    }

    carregar();
    return () => {
      ativo = false;
    };
  }, [usuario]);

  const confirmarSaida = () => {
    Alert.alert('Sair da conta', 'Deseja encerrar a sessão?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Sair',
        style: 'destructive',
        onPress: async () => {
          setSaindo(true);
          try {
            await sair();
          } catch (erro) {
            console.error(erro);
            Alert.alert('Erro', 'Não foi possível encerrar a sessão. Tente novamente.');
            setSaindo(false);
          }
        },
      },
    ]);
  };

  if (carregando) {
    return (
      <View style={estilos.centralizado}>
        <ActivityIndicator size="large" color="#2E5496" />
      </View>
    );
  }

  // Ordem de preferência: perfil no Firestore, displayName do Auth, nada.
  const nomeCompleto = perfil?.nome || usuario?.displayName || '';
  const nome = nomeCompleto ? primeiroNome(nomeCompleto) : '';
  const email = perfil?.email || usuario?.email || '';

  return (
    <ScrollView contentContainerStyle={estilos.container}>
      <View style={estilos.cabecalho}>
        <Text style={estilos.saudacao}>
          {nome ? saudacaoDoHorario() + ', ' + nome : saudacaoDoHorario()}
        </Text>
        {email ? <Text style={estilos.email}>{email}</Text> : null}
      </View>

      <Pressable
        style={({ pressed }) => [estilos.cartao, pressed && estilos.cartaoPressionado]}
        onPress={() => navigation.navigate('Clientes')}
        accessibilityRole="button"
      >
        <Text style={estilos.cartaoTitulo}>Clientes</Text>
        <Text style={estilos.cartaoTexto}>
          Consulte a carteira cadastrada, avalie o risco de cancelamento e acompanhe o histórico.
        </Text>
        <Text style={estilos.link}>Ver tudo</Text>
      </Pressable>

      <Pressable
        style={({ pressed }) => [estilos.cartao, pressed && estilos.cartaoPressionado]}
        onPress={() => navigation.navigate('Cadastro')}
        accessibilityRole="button"
      >
        <Text style={estilos.cartaoTitulo}>Novo cliente</Text>
        <Text style={estilos.cartaoTexto}>
          Registre os dados de um cliente para permitir a avaliação de risco.
        </Text>
      </Pressable>

      <View style={estilos.areaSair}>
        {saindo ? (
          <ActivityIndicator size="small" color="#C0392B" />
        ) : (
          <Text style={estilos.sair} onPress={confirmarSaida} accessibilityRole="button">
            Sair
          </Text>
        )}
      </View>
    </ScrollView>
  );
}

const estilos = StyleSheet.create({
  container: { padding: 20, paddingBottom: 40, backgroundColor: '#fff', flexGrow: 1 },
  centralizado: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#fff' },
  cabecalho: { marginBottom: 24 },
  saudacao: { fontSize: 24, fontWeight: 'bold', color: '#1F2933' },
  email: { fontSize: 13, color: '#7B8794', marginTop: 4 },
  cartao: {
    borderWidth: 1,
    borderColor: '#D9E2EC',
    borderRadius: 10,
    padding: 16,
    marginBottom: 14,
    backgroundColor: '#F8FAFC',
  },
  cartaoPressionado: { backgroundColor: '#EEF2F7' },
  cartaoTitulo: { fontSize: 17, fontWeight: '600', color: '#1F2933', marginBottom: 6 },
  cartaoTexto: { fontSize: 14, color: '#52606D', lineHeight: 20 },
  link: { fontSize: 14, color: '#2E5496', fontWeight: '600', marginTop: 12 },
  areaSair: { marginTop: 20, alignItems: 'center', minHeight: 32, justifyContent: 'center' },
  sair: { fontSize: 15, color: '#C0392B', fontWeight: '600' },
});