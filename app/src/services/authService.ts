import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  updateProfile,
  User,
} from 'firebase/auth';

import { auth } from '../database/firebaseConfig';

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
