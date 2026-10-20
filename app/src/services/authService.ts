import {
  createUserWithEmailAndPassword,
  deleteUser,
  EmailAuthProvider,
  onAuthStateChanged,
  reauthenticateWithCredential,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  updatePassword,
  updateProfile,
  User,
  verifyBeforeUpdateEmail,
} from 'firebase/auth';

import { auth } from '../database/firebaseConfig';
import { atualizarPerfil, removerPerfil } from './perfilService';

export class AuthError extends Error {
  codigo: string;
  constructor(mensagem: string, codigo: string) {
    super(mensagem);
    this.name = 'AuthError';
    this.codigo = codigo;
  }
}

const MENSAGENS: Record<string, string> = {
  'auth/invalid-email': 'E-mail em formato inválido.',
  'auth/user-disabled': 'Esta conta está desativada.',
  'auth/user-not-found': 'E-mail ou senha incorretos.',
  'auth/wrong-password': 'E-mail ou senha incorretos.',
  'auth/invalid-credential': 'E-mail ou senha incorretos.',
  'auth/invalid-login-credentials': 'E-mail ou senha incorretos.',
  'auth/email-already-in-use': 'Já existe uma conta com este e-mail.',
  'auth/weak-password': 'A senha precisa ter ao menos seis caracteres.',
  'auth/missing-password': 'Informe a senha.',
  'auth/too-many-requests': 'Muitas tentativas seguidas. Aguarde alguns minutos.',
  'auth/network-request-failed': 'Sem conexão com a internet. Verifique a rede e tente de novo.',
  'auth/operation-not-allowed': 'Login por e-mail e senha não está habilitado no projeto.',
  'auth/requires-recent-login': 'Por segurança, saia, entre de novo e repita a operação.',
  'auth/missing-new-email': 'Informe o novo e-mail.',
  'sessao/ausente': 'Sua sessão expirou. Entre novamente.',
};

function traduzirErro(erro: unknown): AuthError {
  const codigo = (erro as { code?: string })?.code ?? 'desconhecido';
  const mensagem = MENSAGENS[codigo] ?? 'Não foi possível concluir a operação. Tente novamente.';
  return new AuthError(mensagem, codigo);
}

/** Cria a conta e grava o nome no perfil do Firebase Auth. */
export async function cadastrarConta(
  email: string,
  senha: string,
  nome: string
): Promise<User> {
  try {
    const cred = await createUserWithEmailAndPassword(auth, email.trim(), senha);

    if (nome.trim()) {
      await updateProfile(cred.user, { displayName: nome.trim() });
    }

    return cred.user;
  } catch (erro) {
    throw traduzirErro(erro);
  }
}

export async function entrar(email: string, senha: string): Promise<User> {
  try {
    const cred = await signInWithEmailAndPassword(auth, email.trim(), senha);
    return cred.user;
  } catch (erro) {
    throw traduzirErro(erro);
  }
}

export async function sair(): Promise<void> {
  try {
    await signOut(auth);
  } catch (erro) {
    throw traduzirErro(erro);
  }
}

export async function recuperarSenha(email: string): Promise<void> {
  try {
    await sendPasswordResetEmail(auth, email.trim());
  } catch (erro) {
    throw traduzirErro(erro);
  }
}

// ---------------------------------------------------------------- minha conta
//
// Alterar senha, e-mail ou excluir a conta são operações sensíveis: o Firebase
// exige que a pessoa tenha entrado há pouco tempo. Em vez de depender disso,
// cada operação pede a senha atual e reautentica antes de agir.

function contaAtual(): User {
  const usuario = auth.currentUser;
  if (!usuario || !usuario.email) {
    throw new AuthError(MENSAGENS['sessao/ausente'], 'sessao/ausente');
  }
  return usuario;
}

async function confirmarSenhaAtual(usuario: User, senhaAtual: string): Promise<void> {
  const credencial = EmailAuthProvider.credential(usuario.email as string, senhaAtual);
  await reauthenticateWithCredential(usuario, credencial);
}

/** Troca o nome no login (displayName) e no perfil do Firestore. */
export async function alterarNome(nome: string): Promise<void> {
  try {
    const usuario = contaAtual();
    await updateProfile(usuario, { displayName: nome.trim() });
    await atualizarPerfil(usuario.uid, { nome: nome.trim() });
  } catch (erro) {
    throw erro instanceof AuthError ? erro : traduzirErro(erro);
  }
}

export async function alterarSenha(senhaAtual: string, novaSenha: string): Promise<void> {
  try {
    const usuario = contaAtual();
    await confirmarSenhaAtual(usuario, senhaAtual);
    await updatePassword(usuario, novaSenha);
  } catch (erro) {
    throw erro instanceof AuthError ? erro : traduzirErro(erro);
  }
}

/**
 * Pede a troca do e-mail. O Firebase envia um link de confirmação para o
 * novo endereço; o e-mail só muda depois do clique, e então a sessão é
 * encerrada e a pessoa entra com o e-mail novo. O perfil no Firestore é
 * atualizado na Home, no primeiro acesso depois da troca.
 */
export async function solicitarTrocaDeEmail(senhaAtual: string, novoEmail: string): Promise<void> {
  try {
    const usuario = contaAtual();
    await confirmarSenhaAtual(usuario, senhaAtual);
    await verifyBeforeUpdateEmail(usuario, novoEmail.trim().toLowerCase());
  } catch (erro) {
    throw erro instanceof AuthError ? erro : traduzirErro(erro);
  }
}

/**
 * Exclui o perfil em "pessoas" e a conta no Firebase Authentication.
 *
 * O perfil sai primeiro porque, depois de excluir a conta, a regra do
 * Firestore não deixaria mais apagá-lo. Clientes e avaliações não são
 * apagados: a carteira é da equipe, e cada avaliação guarda o uid de quem a
 * fez como registro histórico. Ao excluir a conta, a sessão termina e a
 * navegação volta sozinha para o login.
 */
export async function excluirConta(senhaAtual: string): Promise<void> {
  try {
    const usuario = contaAtual();
    await confirmarSenhaAtual(usuario, senhaAtual);
    await removerPerfil(usuario.uid);
    await deleteUser(usuario);
  } catch (erro) {
    throw erro instanceof AuthError ? erro : traduzirErro(erro);
  }
}

/**
 * Observa o estado da sessão. Dispara uma vez ao iniciar, com o usuário
 * restaurado do armazenamento local ou null, e a cada login ou logout.
 * Devolve a função para cancelar a observação.
 */
export function observarSessao(callback: (usuario: User | null) => void): () => void {
  return onAuthStateChanged(auth, callback);
}

/** Identificador da conta autenticada. É a chave que liga o perfil e os dados. */
export function idDaContaAtual(): string | null {
  return auth.currentUser?.uid ?? null;
}