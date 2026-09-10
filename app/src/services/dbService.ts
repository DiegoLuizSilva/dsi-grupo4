import {
  collection,
  addDoc,
  getDocs,
  getDoc,
  doc,
  updateDoc,
  deleteDoc,
  query,
  orderBy,
} from 'firebase/firestore';

import { db } from '../database/firebaseConfig';
import { Cliente } from '../types';

const COLECAO = 'clientes';

export const criarCliente = async (cliente: Omit<Cliente, 'id' | 'createdAt' | 'updatedAt'>) => {
  const ref = await addDoc(collection(db, COLECAO), {
    ...cliente,
    createdAt: new Date(),
    updatedAt: new Date(),
  });
  return ref.id;
};

export const listarClientes = async (): Promise<Cliente[]> => {
  const q = query(collection(db, COLECAO), orderBy('nome'));
  const snapshot = await getDocs(q);
  return snapshot.docs.map((d) => ({ id: d.id, ...d.data() }) as Cliente);
};

export const obterCliente = async (id: string): Promise<Cliente | null> => {
  const snapshot = await getDoc(doc(db, COLECAO, id));
  if (!snapshot.exists()) return null;
  return { id: snapshot.id, ...snapshot.data() } as Cliente;
};

export const atualizarCliente = async (
  id: string,
  dados: Partial<Omit<Cliente, 'id' | 'createdAt'>>
) => {
  await updateDoc(doc(db, COLECAO, id), { ...dados, updatedAt: new Date() });
};

export const removerCliente = async (id: string) => {
  await deleteDoc(doc(db, COLECAO, id));
};