import {
  addDoc,
  collection,
  deleteDoc,
  getDocs,
  orderBy,
  query,
  serverTimestamp,
} from 'firebase/firestore';

import { auth, db } from '../database/firebaseConfig';
import { Avaliacao, Cliente, ResultadoPredicao } from '../types';

// Histórico de avaliações de um cliente: clientes/{clienteId}/avaliacoes.
function colecao(clienteId: string) {
  return collection(db, 'clientes', clienteId, 'avaliacoes');
}

/**
 * Grava uma avaliação já respondida pela API.
 *
 * Lança erro se não conseguir gravar. Quem chama decide a mensagem, e nunca
 * deve dizer que a avaliação foi registrada quando isso não aconteceu.
 */
export async function salvarAvaliacao(
  cliente: Cliente,
  entrada: Record<string, number>,
  resultado: ResultadoPredicao
): Promise<string> {
  const uid = auth.currentUser?.uid;
  if (!uid || !cliente.id) {
    throw new Error('Sessão ou cliente ausente ao gravar a avaliação.');
  }

  const ref = await addDoc(colecao(cliente.id), {
    clienteId: cliente.id,
    clienteNome: cliente.nome,
    uid,
    criadoEm: serverTimestamp(),
    entrada,
    resultado,
    faixa: resultado.faixa,
    rotuloFaixa: resultado.rotulo_faixa,
    modeloVersao: resultado.modelo_versao,
  });
  return ref.id;
}

/** Avaliações do cliente, da mais recente para a mais antiga. */
export async function listarAvaliacoes(clienteId: string): Promise<Avaliacao[]> {
  const snapshot = await getDocs(query(colecao(clienteId), orderBy('criadoEm', 'desc')));
  return snapshot.docs.map((d) => {
    const dados = d.data();
    return {
      id: d.id,
      ...dados,
      criadoEm: dados.criadoEm?.toDate?.() ?? new Date(),
    } as Avaliacao;
  });
}

/** Usado ao excluir um cliente, para não deixar avaliações órfãs. */
export async function removerAvaliacoesDoCliente(clienteId: string): Promise<void> {
  const snapshot = await getDocs(colecao(clienteId));
  await Promise.all(snapshot.docs.map((d) => deleteDoc(d.ref)));
}