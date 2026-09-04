import { getFirestore, collection, addDoc, getDocs, query, where, orderBy } from 'firebase/firestore'; 
import { app } from '../database/firebaseConfig';
import { Cliente } from '../types';

export const criarCliente = async (cliente: Omit<Cliente, 'id' | 'createdAt'>) => {
  try {
    const db = getFirestore(app);
    const clientesRef = collection(db, 'clientes'); 
    
    const docRef = await addDoc(clientesRef, {
      ...cliente,
      createdAt: new Date()
    });
    
    console.log("Sucesso! Cliente salvo com ID: ", docRef.id);
    return docRef.id;
  } catch (error) {
    console.error("Erro ao criar cliente: ", error);
    throw error;
  }
};

export const listarClientes = async (termoBusca?: string) => {
  try {
    const db = getFirestore(app);
    const clientesRef = collection(db, 'clientes');
    let q;

    if (termoBusca) {
      q = query(
        clientesRef,
        where('nome', '>=', termoBusca),
        where('nome', '<=', termoBusca + '\uf8ff')
      );
    } else {
      q = query(clientesRef, orderBy('nome'));
    }

    const querySnapshot = await getDocs(q);
    const clientes: Cliente[] = [];

    querySnapshot.forEach((doc) => {
      clientes.push({ id: doc.id, ...doc.data() } as Cliente);
    });

    return clientes;
  } catch (error) {
    console.error("Erro ao listar clientes: ", error);
    throw error;
  }
};