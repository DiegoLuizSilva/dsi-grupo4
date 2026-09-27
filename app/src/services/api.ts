// Cliente HTTP da API do ChurnGuard.
//
// Este arquivo e a unica porta de entrada do app para a API. Nenhuma tela
// deve chamar fetch diretamente: se o endereco ou o contrato mudarem,
// so este arquivo e alterado.
//
// Contrato completo em api/CONTRATO.md

import { Platform } from 'react-native';

import { auth } from '../database/firebaseConfig';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

const TIMEOUT_MS = 8000;

// A API verifica o token de identidade do Firebase em toda rota de dados e de
// predicao. Sem este cabecalho, a resposta e 401.
//
// `getIdToken()` devolve o token em cache e o renova sozinho quando esta perto
// de expirar, entao pode ser chamado a cada requisicao sem custo de rede.
async function cabecalhoDeAutenticacao(): Promise<Record<string, string>> {
  const usuario = auth.currentUser;
  if (!usuario) return {};

  try {
    const token = await usuario.getIdToken();
    return { Authorization: `Bearer ${token}` };
  } catch (erro) {
    console.log('Falha ao obter o token de identidade:', erro);
    return {};
  }
}

export class ApiError extends Error {
  status: number;
  detalhes: any;

  constructor(mensagem: string, status: number, detalhes: any = null) {
    super(mensagem);
    this.name = 'ApiError';
    this.status = status;
    this.detalhes = detalhes;
  }
}

async function requisitar(caminho: string, opcoes: RequestInit = {}): Promise<any> {
  const controlador = new AbortController();
  const timer = setTimeout(() => controlador.abort(), TIMEOUT_MS);

  try {
    const autenticacao = await cabecalhoDeAutenticacao();

    const resposta = await fetch(`${BASE_URL}${caminho}`, {
      ...opcoes,
      signal: controlador.signal,
      headers: {
        'Content-Type': 'application/json',
        ...autenticacao,
        ...(opcoes.headers || {}),
      },
    });

    if (resposta.status === 204) return null;

    const corpo = await resposta.json().catch(() => null);

    if (!resposta.ok) {
      console.log('RESPOSTA DE ERRO DA API (STATUS ' + resposta.status + '):', JSON.stringify(corpo, null, 2));

      let mensagemErro = 'Erro na comunicacao com o servidor';

      // 401 e sempre sessao: expirada, ausente ou de outro projeto Firebase.
      // A mensagem tecnica da API nao ajuda quem esta usando o aplicativo.
      if (resposta.status === 401) {
        throw new ApiError(
          'Sua sessao expirou. Entre novamente para continuar.',
          401,
          corpo?.detail,
        );
      }

      if (resposta.status === 503) {
        throw new ApiError(
          'O servico de analise esta temporariamente indisponivel. Tente em alguns instantes.',
          503,
          corpo?.detail,
        );
      }

      if (corpo && corpo.detail) {
        if (typeof corpo.detail === 'string') {
          mensagemErro = corpo.detail;
        } else if (Array.isArray(corpo.detail)) {
          mensagemErro = corpo.detail
            .map((item: any) => `${item.loc ? item.loc.join('.') : 'campo'}: ${item.msg}`)
            .join(' | ');
        }
      }

      throw new ApiError(mensagemErro, resposta.status, corpo?.detail);
    }

    return corpo;
  } catch (erro: any) {
    if (erro.name === 'AbortError') {
      throw new ApiError('O servidor demorou para responder. Verifique a conexao.', 0);
    }
    if (erro instanceof ApiError) throw erro;
    throw new ApiError('Nao foi possivel alcancar o servidor de analise.', 0);
  } finally {
    clearTimeout(timer);
  }
}

// ------------------------------------------------------------------ SAUDE

export async function verificarServico(): Promise<boolean> {
  try {
    await requisitar('/health');
    return true;
  } catch {
    return false;
  }
}

// --------------------------------------------------------------- PREDICAO

export function avaliarRisco(dados: Record<string, any>) {
  return requisitar('/predict', {
    method: 'POST',
    body: JSON.stringify(dados),
  });
}

// --------------------------------------------------------------- CLIENTES

export function listarClientes() {
  return requisitar('/clientes');
}

export function obterCliente(id: string | number) {
  return requisitar(`/clientes/${id}`);
}

export function criarCliente(dados: Record<string, any>) {
  return requisitar('/clientes', { method: 'POST', body: JSON.stringify(dados) });
}

export function atualizarCliente(id: string | number, dados: Record<string, any>) {
  return requisitar(`/clientes/${id}`, { method: 'PUT', body: JSON.stringify(dados) });
}

export function removerCliente(id: string | number) {
  return requisitar(`/clientes/${id}`, { method: 'DELETE' });
}

export { BASE_URL };