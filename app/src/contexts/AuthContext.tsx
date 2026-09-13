/**
 * Estado da sessão disponível para todo o aplicativo.
 *
 * Enquanto `carregando` for verdadeiro, o Firebase ainda está restaurando a
 * sessão gravada no dispositivo. A navegação não deve decidir entre telas
 * públicas e autenticadas antes disso, sob pena de piscar a tela de login
 * para quem já estava logado.
 */

import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { User } from 'firebase/auth';

import { observarSessao, sair as sairDoServico } from '../services/authService';

type AuthContextValor = {
  usuario: User | null;
  carregando: boolean;
  autenticado: boolean;
  sair: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValor | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [usuario, setUsuario] = useState<User | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    const cancelar = observarSessao((u) => {
      setUsuario(u);
      setCarregando(false);
    });
    return cancelar;
  }, []);

  const valor = useMemo<AuthContextValor>(
    () => ({
      usuario,
      carregando,
      autenticado: !!usuario,
      sair: sairDoServico,
    }),
    [usuario, carregando]
  );

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValor {
  const contexto = useContext(AuthContext);
  if (!contexto) {
    throw new Error('useAuth precisa ser usado dentro de AuthProvider.');
  }
  return contexto;
}