
/**
 * Perfil do usuário autenticado no aplicativo.
 */
export interface Perfil {
  uid: string;
  nome: string;
  email: string;
  criadoEm?: unknown;
  atualizadoEm?: unknown;
}

/**
 * Atributos utilizados para avaliação de churn.
 * O app usa camelCase; a API recebe snake_case.
 */
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

export interface ResultadoPredicao {
  probabilidade: number;
  faixa: 'baixo' | 'medio' | 'alto';
  rotulo_faixa: string;
  fatores: Fator[];
  modelo_versao: string;
  gerado_em: string;
}

/**
 * Avaliação armazenada no Firestore.
 *
 * O registro mantém os atributos e a resposta original
 * para que futuras edições do cliente não alterem o passado.
 */
export interface Avaliacao {
  id?: string;
  clienteId: string;
  clienteNome: string;
  uid: string;
  criadoEm: Date;
  entrada: Record<string, number>;
  resultado: ResultadoPredicao;
  faixa: 'baixo' | 'medio' | 'alto';
  rotuloFaixa: string;
  modeloVersao: string;
}

/**
 * Rotas utilizadas pela aplicação.
 */
export type RootStackParamList = {
  Login: undefined;
  SignUp: undefined;
  ClientList: undefined;
  ClientForm: { cliente?: Cliente } | undefined;

  ClientHistory: {
    cliente: Cliente;
  };

  PredictResult: {
    cliente: Cliente;
    resultado: ResultadoPredicao;

    // Só existe quando a tela abre uma avaliação anterior.
    historico?: {
      id?: string;
      clienteNome: string;
      criadoEm: string;
      entrada: Record<string, number>;
    };
  };
};
