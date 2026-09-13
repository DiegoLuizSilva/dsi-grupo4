/**
 * Perfil da pessoa que USA o aplicativo, guardado na coleção "pessoas"
 * do Firestore com o uid do Firebase Authentication como identificador.
 *
 * Não confundir com Cliente, que é o assinante avaliado pelo modelo e
 * não possui conta nem login.
 */
export interface Perfil {
  uid: string;
  nome: string;
  email: string;
  criadoEm?: unknown;
  atualizadoEm?: unknown;
}
// Atributos de uso que alimentam o modelo. Correspondem às colunas do
// Iranian Churn Dataset. Nomes em camelCase; a tradução para snake_case
// da API acontece em services/churnService.ts.
export interface DadosDeUso {
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
}

export interface Cliente extends DadosDeUso {
  id?: string;
  nome: string;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface Fator {
  campo: string;
  rotulo: string;
  impacto: 'aumenta' | 'reduz';
  peso: number;
  sugestao: string;
}

// Resposta do POST /predict. Ver api/CONTRATO.md.
export interface ResultadoPredicao {
  probabilidade: number;
  faixa: 'baixo' | 'medio' | 'alto';
  rotulo_faixa: string;
  fatores: Fator[];
  modelo_versao: string;
  gerado_em: string;
}

// Registro histórico de uma avaliação já realizada. Usado a partir da Sprint 4.
export interface Avaliacao {
  id?: string;
  clienteId: string;
  clienteNome: string;
  faixa: 'baixo' | 'medio' | 'alto';
  rotuloFaixa: string;
  // Guardada para registro e para o artigo. Não é exibida na tela (RNF06).
  probabilidade: number;
  fatores: Fator[];
  modeloVersao: string;
  dataAvaliacao: Date;
}

// Rotas da pilha de navegação.
export type RootStackParamList = {
  Login: undefined;
  SignUp: undefined;
  ClientList: undefined;
  ClientForm: { cliente?: Cliente } | undefined;
  PredictForm: { cliente: Cliente };
  PredictResult: { cliente: Cliente; resultado: ResultadoPredicao };
  ClientHistory: { cliente: Cliente };
};