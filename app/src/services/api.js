// Cliente HTTP da API do ChurnGuard.
//
// Este arquivo e a unica porta de entrada do app para a API. Nenhuma tela
// deve chamar fetch diretamente: se o endereco ou o contrato mudarem,
// so este arquivo e alterado.
//
// Contrato completo em api/CONTRATO.md

import { Platform } from 'react-native';

// No emulador Android o localhost do computador e 10.0.2.2.
// No celular fisico com Expo Go, troque por IP da sua maquina na rede,
// por exemplo 'http://192.168.0.15:8000'. Descubra com ipconfig ou ifconfig.

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

const TIMEOUT_MS = 8000;

class ApiError extends Error {
  constructor(mensagem, status, detalhes = null) {
    super(mensagem);
    this.name = 'ApiError';
    this.status = status;
    this.detalhes = detalhes;
  }
}

async function requisitar(caminho, opcoes = {}) {
  const controlador = new AbortController();
  const timer = setTimeout(() => controlador.abort(), TIMEOUT_MS);

  try {
    const resposta = await fetch(`${BASE_URL}${caminho}`, {
      ...opcoes,
      signal: controlador.signal,
      headers: { 'Content-Type': 'application/json', ...(opcoes.headers || {}) },
    });

    if (resposta.status === 204) return null;

    const corpo = await resposta.json().catch(() => null);

    if (!resposta.ok) {
      // Exibe os detalhes brutos retornados pelo Pydantic/FastAPI no terminal do Expo
      console.log('RESPOSTA DE ERRO DA API (STATUS ' + resposta.status + '):', JSON.stringify(corpo, null, 2));

      let mensagemErro = 'Erro na comunicacao com o servidor';

      if (corpo && corpo.detail) {
        if (typeof corpo.detail === 'string') {
          mensagemErro = corpo.detail;
        } else if (Array.isArray(corpo.detail)) {
          // Converte a lista de campos invalidos do Pydantic em texto legivel
          mensagemErro = corpo.detail
            .map((item) => `${item.loc ? item.loc.join('.') : 'campo'}: ${item.msg}`)
            .join(' | ');
        }
      }

      throw new ApiError(mensagemErro, resposta.status, corpo?.detail);
    }

    return corpo;
  } catch (erro) {
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

export async function verificarServico() {
  try {
    await requisitar('/health');
    return true;
  } catch {
    return false;
  }
}

// --------------------------------------------------------------- PREDICAO

// dados deve conter os 13 campos listados no CONTRATO.md
export function avaliarRisco(dados) {
  return requisitar('/predict', {
    method: 'POST',
    body: JSON.stringify(dados),
  });
}

// --------------------------------------------------------------- CLIENTES

export function listarClientes() {
  return requisitar('/clientes');
}

export function obterCliente(id) {
  return requisitar(`/clientes/${id}`);
}

export function criarCliente(dados) {
  return requisitar('/clientes', { method: 'POST', body: JSON.stringify(dados) });
}

export function atualizarCliente(id, dados) {
  return requisitar(`/clientes/${id}`, { method: 'PUT', body: JSON.stringify(dados) });
}

export function removerCliente(id) {
  return requisitar(`/clientes/${id}`, { method: 'DELETE' });
}

export { ApiError, BASE_URL };