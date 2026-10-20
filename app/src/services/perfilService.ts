import { deleteDoc, doc, getDoc, serverTimestamp, setDoc } from 'firebase/firestore';

import { db } from '../database/firebaseConfig';
import { Perfil } from '../types';

export const COLECAO_PESSOAS = 'pessoas';

/**
 * Cria ou atualiza o perfil da pessoa usuária.
 *
 * Chamar logo após cadastrarConta(), passando o uid devolvido pelo
 * serviço de autenticação. Usa merge para não apagar campos que venham
 * a ser acrescentados depois.
 */
export async function salvarPerfil(
  uid: string,
  dados: { nome: string; email: string }
): Promise<void> {
  await setDoc(
    doc(db, COLECAO_PESSOAS, uid),
    {
      uid,
      nome: dados.nome.trim(),
      email: dados.email.trim().toLowerCase(),
      atualizadoEm: serverTimestamp(),
      criadoEm: serverTimestamp(),
    },
    { merge: true }
  );
}

/**
 * Lê o perfil da pessoa usuária.
 *
 * Devolve null quando o documento ainda não existe. Isso é possível quando
 * a conta foi criada mas a gravação do perfil falhou; a tela que chamar
 * deve tratar esse caso em vez de assumir que o perfil sempre existe.
 */
export async function obterPerfil(uid: string): Promise<Perfil | null> {
  const snapshot = await getDoc(doc(db, COLECAO_PESSOAS, uid));
  if (!snapshot.exists()) return null;
  return snapshot.data() as Perfil;
}

/**
 * Altera nome ou e-mail do perfil sem mexer em `criadoEm`.
 *
 * Usa merge com o uid para funcionar também quando o perfil não chegou a ser
 * gravado no cadastro (falha parcial): nesse caso ele é criado agora. As
 * regras do Firestore só permitem que a própria pessoa grave o seu perfil.
 */
export async function atualizarPerfil(
  uid: string,
  dados: { nome?: string; email?: string }
): Promise<void> {
  const campos: Record<string, unknown> = { uid, atualizadoEm: serverTimestamp() };
  if (dados.nome !== undefined) campos.nome = dados.nome.trim();
  if (dados.email !== undefined) campos.email = dados.email.trim().toLowerCase();
  await setDoc(doc(db, COLECAO_PESSOAS, uid), campos, { merge: true });
}

/** Apaga o perfil. Usado só na exclusão da conta. */
export async function removerPerfil(uid: string): Promise<void> {
  await deleteDoc(doc(db, COLECAO_PESSOAS, uid));
}