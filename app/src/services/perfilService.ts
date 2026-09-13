import { doc, getDoc, serverTimestamp, setDoc } from 'firebase/firestore';

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