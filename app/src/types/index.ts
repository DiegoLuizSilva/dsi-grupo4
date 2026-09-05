export interface Cliente {
  id?: string;
  nome: string; 
  cpf: string;
  callFailure: number; 
  complains: boolean; 
  subscriptionLength: number; 
  chargeAmount: number; 
  secondsOfUse: number; 
  frequencyOfUse: number; 
  frequencyOfSMS: number; 
  distinctCalledNumbers: number; 
  status: boolean; 
  age: number; 
  ageGroup: number;    
  tariffPlan: number;  
  customerValue: number; 
  churn: boolean;       
  createdAt?: Date;
}

export interface Avaliacao {
  id?: string;
  clienteId: string;
  dadosPredicao: any; 
  risco: 'ALTO' | 'MEDIO' | 'BAIXO';
  dataAvaliacao: Date;
}