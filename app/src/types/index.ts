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

// Registro histórico de uma avaliação, em clientes/{clienteId}/avaliacoes.
export interface Avaliacao {
  id?: string;
  clienteId: string;
  clienteNome: string;
  uid: string;
  criadoEm: Date;
  // Cópia do que foi enviado à API, para que editar o cliente não altere o passado.
  entrada: Record<string, number>;
  // Resposta da API como veio. A probabilidade fica só no registro, não aparece na tela.
  resultado: ResultadoPredicao;
  faixa: 'baixo' | 'medio' | 'alto';
  rotuloFaixa: string;
  modeloVersao: string;
}

// Rotas da pilha de navegação.
export type RootStackParamList = {
  Login: undefined;
  SignUp: undefined;
  ClientList: undefined;
  ClientForm: { cliente?: Cliente } | undefined;
  PredictResult: { cliente: Cliente; resultado: ResultadoPredicao };
  ClientHistory: { cliente: Cliente };
};