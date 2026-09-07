import { avaliarRisco } from './api';

export async function analisarRiscoCliente(clienteDoFirebase: any) {
  const payload = {
    call_failure: clienteDoFirebase.callFailure,
    complains: clienteDoFirebase.complains ? 1 : 0,
    subscription_length: clienteDoFirebase.subscriptionLength,
    charge_amount: clienteDoFirebase.chargeAmount,
    seconds_of_use: clienteDoFirebase.secondsOfUse,
    frequency_of_use: clienteDoFirebase.frequencyOfUse,
    frequency_of_sms: clienteDoFirebase.frequencyOfSMS,
    distinct_called_numbers: clienteDoFirebase.distinctCalledNumbers,
    age_group: clienteDoFirebase.ageGroup,
    tariff_plan: clienteDoFirebase.tariffPlan,
    status: clienteDoFirebase.status ? 1 : 2,
    age: clienteDoFirebase.age,
    customer_value: clienteDoFirebase.customerValue || 0,
  };

  console.log("PAYLOAD ENVIADO PARA A API:", JSON.stringify(payload, null, 2));

  try {
    const resultado = await avaliarRisco(payload);
    return resultado;
  } catch (erro: any) {
    console.error("ERRO COMPLETO DA REQUISICAO:", erro?.detalhes || erro?.message || erro);
    throw erro;
  }
}
