import React, { useState } from 'react';
import { ActivityIndicator, Alert, Button, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';

import { CampoNumero, CampoOpcao, CampoTexto } from '../components/CampoFormulario';
import { atualizarCliente, criarCliente } from '../services/dbService';
import { Cliente, RootStackParamList } from '../types';

// Faixa etária do Iranian Churn Dataset: valores válidos de 1 a 5.
function calcularAgeGroup(idade: number): number {
  if (idade <= 20) return 1;
  if (idade <= 30) return 2;
  if (idade <= 40) return 3;
  if (idade <= 50) return 4;
  return 5;
}

type CampoNumerico =
  | 'age'
  | 'subscriptionLength'
  | 'chargeAmount'
  | 'secondsOfUse'
  | 'frequencyOfUse'
  | 'frequencyOfSMS'
  | 'distinctCalledNumbers'
  | 'callFailure'
  | 'customerValue';

type FormState = Record<CampoNumerico, string> & {
  nome: string;
  complains: boolean;
  status: boolean;
  tariffPlan: number;
};

const VAZIO: FormState = {
  nome: '',
  age: '',
  subscriptionLength: '',
  chargeAmount: '',
  secondsOfUse: '',
  frequencyOfUse: '',
  frequencyOfSMS: '',
  distinctCalledNumbers: '',
  callFailure: '',
  customerValue: '',
  complains: false,
  status: true,
  tariffPlan: 1,
};

function deCliente(c: Cliente): FormState {
  return {
    nome: c.nome ?? '',
    age: String(c.age ?? ''),
    subscriptionLength: String(c.subscriptionLength ?? ''),
    chargeAmount: String(c.chargeAmount ?? ''),
    secondsOfUse: String(c.secondsOfUse ?? ''),
    frequencyOfUse: String(c.frequencyOfUse ?? ''),
    frequencyOfSMS: String(c.frequencyOfSMS ?? ''),
    distinctCalledNumbers: String(c.distinctCalledNumbers ?? ''),
    callFailure: String(c.callFailure ?? ''),
    customerValue: String(c.customerValue ?? ''),
    complains: !!c.complains,
    status: c.status !== false,
    tariffPlan: c.tariffPlan ?? 1,
  };
}

export default function ClientForm() {
  const navigation = useNavigation<any>();
  const rota = useRoute<RouteProp<RootStackParamList, 'ClientForm'>>();
  const clienteEmEdicao = rota.params?.cliente;
  const editando = !!clienteEmEdicao?.id;

  const [form, setForm] = useState<FormState>(
    clienteEmEdicao ? deCliente(clienteEmEdicao) : VAZIO
  );
  const [salvando, setSalvando] = useState(false);

  const mudar = (campo: keyof FormState, valor: string | boolean | number) =>
    setForm((atual) => ({ ...atual, [campo]: valor }));

  const numero = (v: string) => {
    const n = Number(String(v).replace(',', '.'));
    return Number.isFinite(n) ? n : NaN;
  };

  const validar = (): string | null => {
    if (!form.nome.trim()) return 'Informe o nome do cliente.';

    const idade = numero(form.age);
    if (!Number.isInteger(idade) || idade <= 0 || idade > 120) {
      return 'Informe uma idade válida, entre 1 e 120.';
    }

    const cobranca = numero(form.chargeAmount);
    if (!Number.isInteger(cobranca) || cobranca < 0 || cobranca > 9) {
      return 'A faixa de cobrança deve ser um número inteiro de 0 a 9.';
    }

    const inteiros: [CampoNumerico, string][] = [
      ['subscriptionLength', 'Tempo de assinatura'],
      ['secondsOfUse', 'Tempo total de uso'],
      ['frequencyOfUse', 'Quantidade de chamadas'],
      ['frequencyOfSMS', 'Quantidade de mensagens'],
      ['distinctCalledNumbers', 'Contatos distintos'],
      ['callFailure', 'Falhas de chamada'],
    ];

    for (const [campo, rotulo] of inteiros) {
      const v = numero(form[campo]);
      if (!Number.isInteger(v) || v < 0) {
        return rotulo + ' deve ser um número inteiro maior ou igual a zero.';
      }
    }

    const valor = numero(form.customerValue);
    if (!Number.isFinite(valor) || valor < 0) {
      return 'O valor do cliente deve ser um número maior ou igual a zero.';
    }

    return null;
  };

  const salvar = async () => {
    const erro = validar();
    if (erro) {
      Alert.alert('Atenção', erro);
      return;
    }

    const idade = numero(form.age);

    const dados: Omit<Cliente, 'id' | 'createdAt' | 'updatedAt'> = {
      nome: form.nome.trim(),
      age: idade,
      ageGroup: calcularAgeGroup(idade),
      subscriptionLength: numero(form.subscriptionLength),
      chargeAmount: numero(form.chargeAmount),
      secondsOfUse: numero(form.secondsOfUse),
      frequencyOfUse: numero(form.frequencyOfUse),
      frequencyOfSMS: numero(form.frequencyOfSMS),
      distinctCalledNumbers: numero(form.distinctCalledNumbers),
      callFailure: numero(form.callFailure),
      customerValue: numero(form.customerValue),
      complains: form.complains,
      status: form.status,
      tariffPlan: form.tariffPlan,
    };

    setSalvando(true);
    try {
      if (editando && clienteEmEdicao?.id) {
        await atualizarCliente(clienteEmEdicao.id, dados);
        Alert.alert('Pronto', 'Cliente atualizado.');
        navigation.goBack();
      } else {
        await criarCliente(dados);
        Alert.alert('Pronto', 'Cliente cadastrado.');
        setForm(VAZIO);
      }
    } catch (e) {
      console.error(e);
      Alert.alert('Erro', 'Não foi possível salvar o cliente.');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={estilos.container} keyboardShouldPersistTaps="handled">
      <Text style={estilos.secao}>Identificação</Text>

      <CampoTexto
        rotulo="Nome"
        valor={form.nome}
        onChange={(v) => mudar('nome', v)}
        placeholder="Ex: João da Silva"
      />
      <CampoNumero rotulo="Idade" valor={form.age} onChange={(v) => mudar('age', v)} />

      <Text style={estilos.secao}>Plano</Text>

      <CampoOpcao
        rotulo="Tipo de plano"
        opcoes={[
          { texto: 'Pré-pago', valor: 1 },
          { texto: 'Pós-pago', valor: 2 },
        ]}
        valor={form.tariffPlan}
        onChange={(v) => mudar('tariffPlan', v)}
      />

      <CampoOpcao
        rotulo="Situação da linha"
        ajuda="Linhas suspensas ou inativas pesam no risco"
        opcoes={[
          { texto: 'Ativa', valor: true },
          { texto: 'Inativa', valor: false },
        ]}
        valor={form.status}
        onChange={(v) => mudar('status', v)}
      />

      <CampoNumero
        rotulo="Faixa de cobrança"
        ajuda="Número inteiro de 0 a 9, sendo 0 a menor faixa"
        valor={form.chargeAmount}
        onChange={(v) => mudar('chargeAmount', v)}
      />
      <CampoNumero
        rotulo="Tempo de assinatura"
        ajuda="Em meses"
        valor={form.subscriptionLength}
        onChange={(v) => mudar('subscriptionLength', v)}
      />
      <CampoNumero
        rotulo="Valor do cliente"
        ajuda="Valor calculado pela operadora"
        valor={form.customerValue}
        onChange={(v) => mudar('customerValue', v)}
        decimal
      />

      <Text style={estilos.secao}>Comportamento de uso</Text>

      <CampoNumero
        rotulo="Tempo total de uso"
        ajuda="Em segundos de chamada"
        valor={form.secondsOfUse}
        onChange={(v) => mudar('secondsOfUse', v)}
      />
      <CampoNumero
        rotulo="Quantidade de chamadas"
        valor={form.frequencyOfUse}
        onChange={(v) => mudar('frequencyOfUse', v)}
      />
      <CampoNumero
        rotulo="Quantidade de mensagens"
        valor={form.frequencyOfSMS}
        onChange={(v) => mudar('frequencyOfSMS', v)}
      />
      <CampoNumero
        rotulo="Contatos distintos acionados"
        ajuda="Números diferentes para os quais o cliente ligou"
        valor={form.distinctCalledNumbers}
        onChange={(v) => mudar('distinctCalledNumbers', v)}
      />

      <Text style={estilos.secao}>Atendimento</Text>

      <CampoNumero
        rotulo="Falhas de chamada"
        valor={form.callFailure}
        onChange={(v) => mudar('callFailure', v)}
      />

      <CampoOpcao
        rotulo="Reclamação registrada"
        ajuda="O cliente abriu reclamação no período?"
        opcoes={[
          { texto: 'Não', valor: false },
          { texto: 'Sim', valor: true },
        ]}
        valor={form.complains}
        onChange={(v) => mudar('complains', v)}
      />

      <View style={estilos.areaBotao}>
        {salvando ? (
          <ActivityIndicator size="small" color="#2E5496" />
        ) : (
          <Button
            title={editando ? 'Salvar alterações' : 'Cadastrar cliente'}
            onPress={salvar}
            color="#2E5496"
          />
        )}
      </View>
    </ScrollView>
  );
}

const estilos = StyleSheet.create({
  container: { padding: 20, paddingBottom: 48, backgroundColor: '#fff', flexGrow: 1 },
  secao: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#2E5496',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 18,
    marginBottom: 10,
  },
  areaBotao: { marginTop: 24, minHeight: 44, justifyContent: 'center' },
});