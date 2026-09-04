export interface Cliente {
  id?: string;
  nome: string;
  cpf: string;
  idade: number;
  createdAt: Date;
}

export interface Avaliacao {
  id?: string;
  clienteId: string;
  dadosPredicao: any; 
  risco: 'ALTO' | 'MEDIO' | 'BAIXO';
  dataAvaliacao: Date;
}