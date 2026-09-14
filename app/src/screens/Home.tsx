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
import { useSafeAreaInsets } from 'react-native-safe-area-context';
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

// Usa só o primeiro nome. "Olá, João Pedro da Silva!" quebra a linha do
// cabeçalho em telas estreitas.
function primeiroNome(nome: string): string {
  return nome.trim().split(/\s+/)[0] ?? '';
}

// Iniciais para o avatar do topo. Duas letras no máximo.
function iniciais(nome: string): string {
  const partes = nome.trim().split(/\s+/).filter(Boolean);
  if (partes.length === 0) return 'CG';
  if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase();
  return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
}

export default function Home() {
  const navigation = useNavigation<Navegacao>();
  const insets = useSafeAreaInsets();
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

  return (
    <ScrollView style={estilos.tela} contentContainerStyle={estilos.conteudo}>
      <View style={[estilos.cabecalho, { paddingTop: insets.top + 16 }]}>
        <View style={estilos.barraTopo}>
          <View style={estilos.identidade}>
            <View style={estilos.avatar}>
              <Text style={estilos.avatarTexto}>{iniciais(nomeCompleto)}</Text>
            </View>
            <Text style={estilos.marca}>ChurnGuard</Text>
          </View>

          <Pressable
            style={({ pressed }) => [estilos.botaoSair, pressed && estilos.botaoSairPressionado]}
            onPress={confirmarSaida}
            accessibilityRole="button"
            disabled={saindo}
          >
            {saindo ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={estilos.botaoSairTexto}>Sair ↗</Text>
            )}
          </Pressable>
        </View>

        <Text style={estilos.saudacao}>{nome ? 'Olá, ' + nome + '!' : 'Olá!'}</Text>
        <Text style={estilos.subtitulo}>
          Gerencie seus clientes e acompanhe o risco de cancelamento.
        </Text>
      </View>

      <View style={estilos.corpo}>
        <View style={estilos.linhaSecao}>
          <Text style={estilos.tituloSecao}>Acesso rápido</Text>
          <Text
            style={estilos.verTudo}
            onPress={() => navigation.navigate('Clientes')}
            accessibilityRole="button"
          >
            Ver tudo
          </Text>
        </View>

        <View style={estilos.linhaCartoes}>
          <Pressable
            style={({ pressed }) => [estilos.cartao, pressed && estilos.cartaoPressionado]}
            onPress={() => navigation.navigate('Clientes')}
            accessibilityRole="button"
          >
            <View style={[estilos.icone, estilos.iconeAzul]}>
              <Text style={estilos.iconeTextoAzul}>C</Text>
            </View>
            <Text style={estilos.cartaoTitulo}>Clientes</Text>
            <Text style={estilos.cartaoTexto}>Consulte, edite e avalie clientes.</Text>
            <Text style={estilos.acessarAzul}>Acessar →</Text>
          </Pressable>

          <Pressable
            style={({ pressed }) => [estilos.cartao, pressed && estilos.cartaoPressionado]}
            onPress={() => navigation.navigate('Cadastro')}
            accessibilityRole="button"
          >
            <View style={[estilos.icone, estilos.iconeVerde]}>
              <Text style={estilos.iconeTextoVerde}>+</Text>
            </View>
            <Text style={estilos.cartaoTitulo}>Novo cliente</Text>
            <Text style={estilos.cartaoTexto}>Adicione uma pessoa à sua base.</Text>
            <Text style={estilos.acessarVerde}>Acessar →</Text>
          </Pressable>
        </View>

        <View style={estilos.destaque}>
          <View style={estilos.destaqueIcone}>
            <Text style={estilos.destaqueIconeTexto}>✓</Text>
          </View>
          <View style={estilos.destaqueTextos}>
            <Text style={estilos.destaqueTitulo}>Decisões de retenção mais claras</Text>
            <Text style={estilos.destaqueTexto}>
              Identifique sinais de risco e consulte os fatores de cada avaliação.
            </Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
}

const AZUL = '#2E5496';
const VERDE = '#1E9E5A';

const estilos = StyleSheet.create({
  tela: { flex: 1, backgroundColor: '#fff' },
  conteudo: { paddingBottom: 32 },
  centralizado: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#fff' },

  cabecalho: {
    backgroundColor: AZUL,
    paddingHorizontal: 20,
    paddingBottom: 28,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  barraTopo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  identidade: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  avatar: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.22)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarTexto: { color: '#fff', fontSize: 13, fontWeight: '700' },
  marca: { color: '#fff', fontSize: 17, fontWeight: '700' },
  botaoSair: {
    backgroundColor: 'rgba(255,255,255,0.18)',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 8,
    minWidth: 62,
    alignItems: 'center',
  },
  botaoSairPressionado: { backgroundColor: 'rgba(255,255,255,0.3)' },
  botaoSairTexto: { color: '#fff', fontSize: 13, fontWeight: '600' },
  saudacao: { color: '#fff', fontSize: 26, fontWeight: '700', marginBottom: 6 },
  subtitulo: { color: 'rgba(255,255,255,0.8)', fontSize: 14, lineHeight: 20 },

  corpo: { paddingHorizontal: 16, paddingTop: 22 },
  linhaSecao: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  tituloSecao: { fontSize: 16, fontWeight: '700', color: '#1F2933' },
  verTudo: { fontSize: 14, fontWeight: '600', color: AZUL },

  linhaCartoes: { flexDirection: 'row', gap: 12 },
  cartao: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E4E9F0',
    borderRadius: 14,
    padding: 14,
    backgroundColor: '#fff',
  },
  cartaoPressionado: { backgroundColor: '#F7F9FC' },
  icone: { width: 38, height: 38, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  iconeAzul: { backgroundColor: '#E8EFFB' },
  iconeVerde: { backgroundColor: '#E3F5EA' },
  iconeTextoAzul: { color: AZUL, fontSize: 16, fontWeight: '700' },
  iconeTextoVerde: { color: VERDE, fontSize: 18, fontWeight: '700' },
  cartaoTitulo: { fontSize: 15, fontWeight: '700', color: '#1F2933', marginTop: 12 },
  cartaoTexto: { fontSize: 13, color: '#7B8794', lineHeight: 18, marginTop: 4 },
  acessarAzul: { fontSize: 13, fontWeight: '600', color: AZUL, marginTop: 12 },
  acessarVerde: { fontSize: 13, fontWeight: '600', color: VERDE, marginTop: 12 },

  destaque: {
    flexDirection: 'row',
    gap: 12,
    backgroundColor: '#EDF2FC',
    borderRadius: 14,
    padding: 16,
    marginTop: 18,
  },
  destaqueIcone: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: AZUL,
    alignItems: 'center',
    justifyContent: 'center',
  },
  destaqueIconeTexto: { color: '#fff', fontSize: 16, fontWeight: '700' },
  destaqueTextos: { flex: 1 },
  destaqueTitulo: { fontSize: 14, fontWeight: '700', color: '#1F2933', marginBottom: 4 },
  destaqueTexto: { fontSize: 13, color: '#52606D', lineHeight: 18 },
});