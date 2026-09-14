import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { NavigationProp, useNavigation } from '@react-navigation/native';

import { AuthError, entrar, recuperarSenha } from '../services/authService';
import { RootStackParamList } from '../types';
import { normalizarEmail, validarLogin } from '../utils/loginValidation';

export default function Login() {
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [recuperando, setRecuperando] = useState(false);
  const [mostrarSenha, setMostrarSenha] = useState(false);

  const autenticar = async () => {
    const erroValidacao = validarLogin({ email, senha });
    if (erroValidacao) {
      setErro(erroValidacao);
      return;
    }

    setErro(null);
    setEnviando(true);
    try {
      await entrar(normalizarEmail(email), senha);
      // O observador da sessão troca as rotas automaticamente após o login.
    } catch (erroLogin) {
      setErro(
        erroLogin instanceof AuthError
          ? erroLogin.message
          : 'Não foi possível entrar. Tente novamente.'
      );
    } finally {
      setEnviando(false);
    }
  };

  const solicitarRecuperacao = async () => {
    const emailNormalizado = normalizarEmail(email);
    const erroEmail = validarLogin({ email: emailNormalizado, senha: 'senha-temporaria' });

    if (erroEmail) {
      setErro(
        emailNormalizado
          ? 'Informe um endereço de e-mail válido para recuperar a senha.'
          : 'Informe seu e-mail para recuperar a senha.'
      );
      return;
    }

    setErro(null);
    setRecuperando(true);
    try {
      await recuperarSenha(emailNormalizado);
      Alert.alert(
        'E-mail enviado',
        'Se existir uma conta com esse e-mail, você receberá as instruções para redefinir a senha.'
      );
    } catch (erroRecuperacao) {
      setErro(
        erroRecuperacao instanceof AuthError
          ? erroRecuperacao.message
          : 'Não foi possível enviar o e-mail de recuperação.'
      );
    } finally {
      setRecuperando(false);
    }
  };

  const abrirCadastro = () => {
    const cadastroDisponivel = navigation.getState().routeNames.includes('SignUp');
    if (cadastroDisponivel) {
      navigation.navigate('SignUp');
      return;
    }

    Alert.alert(
      'Cadastro em integração',
      'A tela de Cadastro de Pessoa será disponibilizada assim que a parte responsável for integrada.'
    );
  };

  const limparErro = () => {
    if (erro) setErro(null);
  };

  const processando = enviando || recuperando;

  return (
    <KeyboardAvoidingView
      style={estilos.tela}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={estilos.container}
        keyboardShouldPersistTaps="handled"
      >
        <View style={estilos.marcaContainer}>
          <View style={estilos.logo}>
            <Text style={estilos.logoTexto}>CG</Text>
          </View>
          <Text style={estilos.marca}>ChurnGuard</Text>
        </View>

        <View style={estilos.cabecalho}>
          <Text style={estilos.titulo}>Entre na sua conta</Text>
          <Text style={estilos.subtitulo}>
            Acesse o painel para acompanhar seus clientes.
          </Text>
        </View>

        <View style={estilos.formulario}>
          <Text style={estilos.rotulo}>E-mail</Text>
          <View style={[estilos.entradaContainer, erro && estilos.entradaComErro]}>
            <Text style={estilos.iconeEntrada}>@</Text>
            <TextInput
              style={estilos.entrada}
              value={email}
              onChangeText={(valor) => {
                setEmail(valor);
                limparErro();
              }}
              placeholder="nome@exemplo.com"
              placeholderTextColor="#616E7C"
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              autoComplete="email"
              textContentType="emailAddress"
              editable={!processando}
              returnKeyType="next"
              accessibilityLabel="E-mail"
            />
          </View>

          <Text style={estilos.rotuloSenha}>Senha</Text>
          <View style={[estilos.entradaContainer, erro && estilos.entradaComErro]}>
            <Text style={estilos.iconeSenha}>●</Text>
            <TextInput
              style={estilos.entrada}
              value={senha}
              onChangeText={(valor) => {
                setSenha(valor);
                limparErro();
              }}
              placeholder="••••••••"
              placeholderTextColor="#616E7C"
              secureTextEntry={!mostrarSenha}
              autoCapitalize="none"
              autoCorrect={false}
              autoComplete="current-password"
              textContentType="password"
              editable={!processando}
              returnKeyType="done"
              onSubmitEditing={autenticar}
              accessibilityLabel="Senha"
            />
            <TouchableOpacity
              onPress={() => setMostrarSenha((valorAtual) => !valorAtual)}
              disabled={processando}
              accessibilityRole="button"
              accessibilityLabel={mostrarSenha ? 'Ocultar senha' : 'Exibir senha'}
            >
              <Text style={estilos.exibirSenha}>{mostrarSenha ? 'Ocultar' : 'Exibir'}</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={estilos.recuperarSenha}
            onPress={solicitarRecuperacao}
            disabled={processando}
            accessibilityRole="button"
          >
            <Text style={estilos.recuperarSenhaTexto}>
              {recuperando ? 'Enviando...' : 'Esqueci minha senha'}
            </Text>
          </TouchableOpacity>

          {erro ? (
            <Text style={estilos.erro} accessibilityRole="alert">
              {erro}
            </Text>
          ) : null}

          <TouchableOpacity
            style={[estilos.botao, processando && estilos.botaoDesativado]}
            onPress={autenticar}
            disabled={processando}
            accessibilityRole="button"
            accessibilityLabel="Entrar na conta"
          >
            {enviando ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={estilos.botaoTexto}>Entrar</Text>
            )}
          </TouchableOpacity>
        </View>

        <View style={estilos.rodapeCadastro}>
          <Text style={estilos.rodapeTexto}>Ainda não tem conta?</Text>
          <TouchableOpacity onPress={abrirCadastro} accessibilityRole="button">
            <Text style={estilos.cadastroTexto}>Cadastre-se</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const estilos = StyleSheet.create({
  tela: { flex: 1, backgroundColor: '#F5F7FA' },
  container: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 34,
  },
  marcaContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  logo: {
    width: 46,
    height: 46,
    borderRadius: 14,
    backgroundColor: '#2E5496',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  logoTexto: { color: '#fff', fontSize: 16, fontWeight: '700' },
  marca: { color: '#2E5496', fontSize: 22, fontWeight: '700' },
  cabecalho: { alignItems: 'center', marginBottom: 24 },
  titulo: {
    color: '#1F2933',
    fontSize: 28,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitulo: {
    color: '#616E7C',
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
    maxWidth: 310,
  },
  formulario: {
    width: '100%',
    maxWidth: 342,
    backgroundColor: '#fff',
    borderRadius: 18,
    padding: 20,
    elevation: 3,
    shadowColor: '#0E1B2D',
    shadowOpacity: 0.08,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 6 },
  },
  rotulo: { color: '#1F2933', fontSize: 13, fontWeight: '600', marginBottom: 8 },
  rotuloSenha: {
    color: '#1F2933',
    fontSize: 13,
    fontWeight: '600',
    marginTop: 18,
    marginBottom: 8,
  },
  entradaContainer: {
    minHeight: 54,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#CBD2D9',
    borderRadius: 12,
    backgroundColor: '#fff',
    paddingHorizontal: 14,
  },
  entradaComErro: { borderColor: '#C62828' },
  iconeEntrada: { color: '#2E5496', fontSize: 16, fontWeight: '700', marginRight: 10 },
  iconeSenha: { color: '#2E5496', fontSize: 13, marginRight: 11 },
  entrada: {
    flex: 1,
    color: '#1F2933',
    fontSize: 14,
    paddingVertical: 14,
  },
  exibirSenha: { color: '#616E7C', fontSize: 13, fontWeight: '500', paddingVertical: 10 },
  recuperarSenha: { alignSelf: 'flex-end', paddingVertical: 16 },
  recuperarSenhaTexto: { color: '#2E5496', fontSize: 13, fontWeight: '600' },
  erro: { color: '#C62828', fontSize: 13, lineHeight: 19, marginBottom: 14 },
  botao: {
    minHeight: 52,
    borderRadius: 12,
    backgroundColor: '#0A7BFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  botaoDesativado: { backgroundColor: '#829AB1' },
  botaoTexto: { color: '#fff', fontSize: 15, fontWeight: '700' },
  rodapeCadastro: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 26,
  },
  rodapeTexto: { color: '#616E7C', fontSize: 13 },
  cadastroTexto: { color: '#2E5496', fontSize: 13, fontWeight: '600', marginLeft: 5 },
});
