// Tela "Minha conta": dados e manutenção da conta de quem usa o aplicativo.
//
// Fecha o CRUD da pessoa usuária: o cadastro (C) fica em SignUp, a leitura (R)
// aqui e na Home, a alteração (U) de nome, senha e e-mail e a exclusão (D)
// aqui. É aberta como modal pela Home, sem rota própria.

import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useAuth } from '../contexts/AuthContext';
import {
  alterarNome,
  alterarSenha,
  AuthError,
  excluirConta,
  solicitarTrocaDeEmail,
} from '../services/authService';
import { normalizarEmail } from '../utils/loginValidation';

const PADRAO_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Operacao = 'nome' | 'senha' | 'email' | 'excluir' | null;

type Props = {
  visivel: boolean;
  nomeAtual: string;
  aoFechar: () => void;
};

function mensagemDe(erro: unknown): string {
  return erro instanceof AuthError
    ? erro.message
    : 'Não foi possível concluir a operação. Tente novamente.';
}

export default function MinhaConta({ visivel, nomeAtual, aoFechar }: Props) {
  const insets = useSafeAreaInsets();
  const { usuario } = useAuth();

  const [nome, setNome] = useState(nomeAtual);
  const [senhaAtual, setSenhaAtual] = useState('');
  const [novaSenha, setNovaSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [novoEmail, setNovoEmail] = useState('');
  const [senhaParaEmail, setSenhaParaEmail] = useState('');
  const [senhaParaExcluir, setSenhaParaExcluir] = useState('');
  const [emAndamento, setEmAndamento] = useState<Operacao>(null);

  const ocupado = emAndamento !== null;

  // Reabrir a tela parte sempre dos dados atuais e com os campos de senha vazios.
  const aoAbrir = () => {
    setNome(nomeAtual);
    setSenhaAtual('');
    setNovaSenha('');
    setConfirmarSenha('');
    setNovoEmail('');
    setSenhaParaEmail('');
    setSenhaParaExcluir('');
  };

  async function executar(operacao: Exclude<Operacao, null>, acao: () => Promise<void>) {
    setEmAndamento(operacao);
    try {
      await acao();
    } catch (erro) {
      console.error(erro);
      Alert.alert('Erro', mensagemDe(erro));
    } finally {
      setEmAndamento(null);
    }
  }

  const salvarNome = () => {
    if (!nome.trim()) {
      Alert.alert('Atenção', 'Informe o nome.');
      return;
    }
    executar('nome', async () => {
      await alterarNome(nome);
      Alert.alert('Pronto', 'Nome atualizado.');
    });
  };

  const salvarSenha = () => {
    if (!senhaAtual || !novaSenha) {
      Alert.alert('Atenção', 'Preencha a senha atual e a nova senha.');
      return;
    }
    if (novaSenha.length < 6) {
      Alert.alert('Atenção', 'A nova senha deve ter no mínimo 6 caracteres.');
      return;
    }
    if (novaSenha !== confirmarSenha) {
      Alert.alert('Atenção', 'As senhas não conferem.');
      return;
    }
    executar('senha', async () => {
      await alterarSenha(senhaAtual, novaSenha);
      setSenhaAtual('');
      setNovaSenha('');
      setConfirmarSenha('');
      Alert.alert('Pronto', 'Senha alterada. Use a nova senha no próximo login.');
    });
  };

  const pedirTrocaDeEmail = () => {
    const email = normalizarEmail(novoEmail);
    if (!PADRAO_EMAIL.test(email)) {
      Alert.alert('Atenção', 'Informe um endereço de e-mail válido.');
      return;
    }
    if (email === usuario?.email?.toLowerCase()) {
      Alert.alert('Atenção', 'Este já é o e-mail da sua conta.');
      return;
    }
    if (!senhaParaEmail) {
      Alert.alert('Atenção', 'Informe a senha atual.');
      return;
    }
    executar('email', async () => {
      await solicitarTrocaDeEmail(senhaParaEmail, email);
      setNovoEmail('');
      setSenhaParaEmail('');
      Alert.alert(
        'Confirme no novo e-mail',
        `Enviamos um link para ${email}. A troca só vale depois que você abrir o link. ` +
          'Em seguida, entre no aplicativo com o e-mail novo.',
      );
    });
  };

  const confirmarExclusao = () => {
    if (!senhaParaExcluir) {
      Alert.alert('Atenção', 'Informe a senha atual para excluir a conta.');
      return;
    }
    Alert.alert(
      'Excluir conta',
      'Sua conta e seu perfil serão apagados e você sairá do aplicativo. ' +
        'Os clientes e as avaliações continuam na carteira da equipe. Esta ação não pode ser desfeita.',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Excluir',
          style: 'destructive',
          // Ao excluir, a sessão termina e a navegação volta sozinha ao login.
          onPress: () => executar('excluir', () => excluirConta(senhaParaExcluir)),
        },
      ],
    );
  };

  return (
    <Modal visible={visivel} animationType="slide" onShow={aoAbrir} onRequestClose={aoFechar}>
      <View style={[estilos.topo, { paddingTop: insets.top + 12 }]}>
        <Text style={estilos.titulo}>Minha conta</Text>
        <Pressable onPress={aoFechar} disabled={ocupado} accessibilityRole="button">
          <Text style={estilos.fechar}>Fechar</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={estilos.conteudo} keyboardShouldPersistTaps="handled">
        <Text style={estilos.secao}>Dados da conta</Text>
        <Text style={estilos.rotulo}>E-mail</Text>
        <Text style={estilos.valor}>{usuario?.email ?? '-'}</Text>

        <Text style={estilos.rotulo}>Nome</Text>
        <TextInput
          style={estilos.campo}
          value={nome}
          onChangeText={setNome}
          placeholder="Seu nome"
          editable={!ocupado}
        />
        <Botao
          texto="Salvar nome"
          onPress={salvarNome}
          carregando={emAndamento === 'nome'}
          desabilitado={ocupado}
        />

        <Text style={estilos.secao}>Alterar senha</Text>
        <TextInput
          style={estilos.campo}
          value={senhaAtual}
          onChangeText={setSenhaAtual}
          placeholder="Senha atual"
          secureTextEntry
          editable={!ocupado}
        />
        <TextInput
          style={estilos.campo}
          value={novaSenha}
          onChangeText={setNovaSenha}
          placeholder="Nova senha (mínimo 6 caracteres)"
          secureTextEntry
          editable={!ocupado}
        />
        <TextInput
          style={estilos.campo}
          value={confirmarSenha}
          onChangeText={setConfirmarSenha}
          placeholder="Confirme a nova senha"
          secureTextEntry
          editable={!ocupado}
        />
        <Botao
          texto="Alterar senha"
          onPress={salvarSenha}
          carregando={emAndamento === 'senha'}
          desabilitado={ocupado}
        />

        <Text style={estilos.secao}>Alterar e-mail</Text>
        <TextInput
          style={estilos.campo}
          value={novoEmail}
          onChangeText={setNovoEmail}
          placeholder="Novo e-mail"
          autoCapitalize="none"
          keyboardType="email-address"
          editable={!ocupado}
        />
        <TextInput
          style={estilos.campo}
          value={senhaParaEmail}
          onChangeText={setSenhaParaEmail}
          placeholder="Senha atual"
          secureTextEntry
          editable={!ocupado}
        />
        <Botao
          texto="Enviar link de confirmação"
          onPress={pedirTrocaDeEmail}
          carregando={emAndamento === 'email'}
          desabilitado={ocupado}
        />

        <Text style={[estilos.secao, estilos.perigo]}>Excluir conta</Text>
        <TextInput
          style={estilos.campo}
          value={senhaParaExcluir}
          onChangeText={setSenhaParaExcluir}
          placeholder="Senha atual"
          secureTextEntry
          editable={!ocupado}
        />
        <Botao
          texto="Excluir minha conta"
          onPress={confirmarExclusao}
          carregando={emAndamento === 'excluir'}
          desabilitado={ocupado}
          destrutivo
        />
      </ScrollView>
    </Modal>
  );
}

function Botao({
  texto,
  onPress,
  carregando,
  desabilitado,
  destrutivo,
}: {
  texto: string;
  onPress: () => void;
  carregando: boolean;
  desabilitado: boolean;
  destrutivo?: boolean;
}) {
  return (
    <Pressable
      style={({ pressed }) => [
        estilos.botao,
        destrutivo && estilos.botaoDestrutivo,
        (pressed || desabilitado) && estilos.botaoInativo,
      ]}
      onPress={onPress}
      disabled={desabilitado}
      accessibilityRole="button"
    >
      {carregando ? (
        <ActivityIndicator size="small" color="#fff" />
      ) : (
        <Text style={estilos.botaoTexto}>{texto}</Text>
      )}
    </Pressable>
  );
}

const AZUL = '#2E5496';
const VERMELHO = '#C62828';

const estilos = StyleSheet.create({
  topo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 14,
    backgroundColor: AZUL,
  },
  titulo: { color: '#fff', fontSize: 20, fontWeight: '700' },
  fechar: { color: '#fff', fontSize: 15, fontWeight: '600' },
  conteudo: { padding: 20, paddingBottom: 48 },
  secao: { fontSize: 16, fontWeight: '700', color: '#1F2933', marginTop: 24, marginBottom: 10 },
  perigo: { color: VERMELHO },
  rotulo: { fontSize: 13, color: '#7B8794', marginTop: 8, marginBottom: 4 },
  valor: { fontSize: 15, color: '#1F2933', marginBottom: 4 },
  campo: {
    borderWidth: 1,
    borderColor: '#D9E2EC',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    marginBottom: 10,
    backgroundColor: '#fff',
  },
  botao: {
    backgroundColor: AZUL,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 4,
  },
  botaoDestrutivo: { backgroundColor: VERMELHO },
  botaoInativo: { opacity: 0.6 },
  botaoTexto: { color: '#fff', fontSize: 15, fontWeight: '600' },
});