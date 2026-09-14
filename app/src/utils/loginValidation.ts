const PADRAO_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type CredenciaisLogin = {
  email: string;
  senha: string;
};

export function normalizarEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function validarLogin({ email, senha }: CredenciaisLogin): string | null {
  const emailNormalizado = normalizarEmail(email);

  if (!emailNormalizado || !senha) {
    return 'Preencha o e-mail e a senha.';
  }

  if (!PADRAO_EMAIL.test(emailNormalizado)) {
    return 'Informe um endereço de e-mail válido.';
  }

  return null;
}
