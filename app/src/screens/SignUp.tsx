import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator, Alert } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { cadastrarConta } from '../services/authService';

export default function SignUp({ navigation }: any) {
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [mostrarConfirmarSenha, setMostrarConfirmarSenha] = useState(false);
  const [loading, setLoading] = useState(false);

  const senhasConferem = senha.length > 0 && senha === confirmarSenha;

  const handleCadastro = async () => {
    if (!nome || !email || !senha) {
      Alert.alert('Atenção', 'Preencha todos os campos obrigatórios.');
      return;
    }
    if (senha.length < 6) {
      Alert.alert('Atenção', 'A senha deve ter no mínimo 6 caracteres.');
      return;
    }
    if (!senhasConferem) {
      Alert.alert('Atenção', 'As senhas não conferem.');
      return;
    }

    setLoading(true);
    try {
      // Chama a função exata criada pela sua equipe
      await cadastrarConta(email, senha, nome);
      
      Alert.alert('Sucesso', 'Conta criada com sucesso!');
      
      // Aqui você navega de volta para o login ou para a tela principal
      // navigation.navigate('Login'); 
      
    } catch (error: any) {
      // O error.message já vai vir traduzido em português graças ao AuthError do authService.ts!
      Alert.alert('Erro no cadastro', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Feather name="chevron-left" size={24} color="#1D4ED8" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>ChurnGuard</Text>
      </View>

      <Text style={styles.title}>Crie sua conta</Text>
      <Text style={styles.subtitle}>Cadastre seus dados para acessar o painel.</Text>

      <View style={styles.card}>
        {/* Nome */}
        <Text style={styles.label}>Nome completo</Text>
        <View style={styles.inputContainer}>
          <Text style={styles.iconText}>A</Text>
          <TextInput 
            style={styles.input} 
            placeholder="Como você quer ser chamado" 
            value={nome}
            onChangeText={setNome}
          />
        </View>

        {/* E-mail */}
        <Text style={styles.label}>E-mail</Text>
        <View style={styles.inputContainer}>
          <Text style={styles.iconText}>@</Text>
          <TextInput 
            style={styles.input} 
            placeholder="nome@exemplo.com" 
            keyboardType="email-address"
            autoCapitalize="none"
            value={email}
            onChangeText={setEmail}
          />
        </View>

        {/* Senha */}
        <Text style={styles.label}>Senha</Text>
        <View style={styles.inputContainer}>
          <Feather name="circle" size={12} color="#1D4ED8" style={styles.iconStyle} />
          <TextInput 
            style={styles.input} 
            placeholder="Mínimo de 6 caracteres" 
            secureTextEntry={!mostrarSenha}
            value={senha}
            onChangeText={setSenha}
          />
          <TouchableOpacity onPress={() => setMostrarSenha(!mostrarSenha)}>
            <Text style={styles.actionText}>{mostrarSenha ? "Ocultar" : "Exibir"}</Text>
          </TouchableOpacity>
        </View>

        {/* Confirmar Senha */}
        <Text style={styles.label}>Confirmar senha</Text>
        <View style={styles.inputContainer}>
          <Feather name="circle" size={12} color="#1D4ED8" style={styles.iconStyle} />
          <TextInput 
            style={styles.input} 
            placeholder="Digite a senha novamente" 
            secureTextEntry={!mostrarConfirmarSenha}
            value={confirmarSenha}
            onChangeText={setConfirmarSenha}
          />
          <TouchableOpacity onPress={() => setMostrarConfirmarSenha(!mostrarConfirmarSenha)}>
            <Text style={styles.actionText}>{mostrarConfirmarSenha ? "Ocultar" : "Exibir"}</Text>
          </TouchableOpacity>
        </View>

        {/* Validação Visual de Senha */}
        <View style={styles.validationContainer}>
          <Feather 
            name="check" 
            size={14} 
            color={senhasConferem ? "#10B981" : "#D1D5DB"} 
          />
          <Text style={[styles.validationText, senhasConferem && styles.validationTextSuccess]}>
            As senhas devem ser iguais.
          </Text>
        </View>

        {/* Botão de Cadastro */}
        <TouchableOpacity 
          style={styles.primaryButton} 
          onPress={handleCadastro}
          disabled={loading}
        >
          {loading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.primaryButtonText}>Criar conta</Text>}
        </TouchableOpacity>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>Já possui uma conta? </Text>
        {/* Assumindo que a tela de login se chama 'Login' ou 'SignIn' no seu navegador */}
        <TouchableOpacity onPress={() => navigation.navigate('Login')}>
          <Text style={styles.footerLink}>Entrar</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAFA',
    padding: 24,
    justifyContent: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1E3A8A',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 32,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
    marginTop: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    paddingHorizontal: 12,
    height: 52,
  },
  iconText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1D4ED8',
    marginRight: 12,
    width: 20,
    textAlign: 'center',
  },
  iconStyle: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    fontSize: 15,
    color: '#111827',
  },
  actionText: {
    color: '#6B7280',
    fontSize: 14,
    fontWeight: '500',
  },
  validationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 24,
  },
  validationText: {
    marginLeft: 8,
    fontSize: 13,
    color: '#9CA3AF',
  },
  validationTextSuccess: {
    color: '#10B981', 
  },
  primaryButton: {
    backgroundColor: '#1D4ED8', 
    height: 52,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  footerText: {
    color: '#6B7280',
    fontSize: 14,
  },
  footerLink: {
    color: '#1D4ED8',
    fontSize: 14,
    fontWeight: 'bold',
  }
});