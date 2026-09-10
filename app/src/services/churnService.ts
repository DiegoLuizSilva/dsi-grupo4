import { avaliarRisco } from './api';
import { Cliente, ResultadoPredicao } from '../types';

// Traduz o cliente guardado no Firestore (camelCase) para o contrato da
// API Python (snake_case). Ver api/CONTRATO.md.
export async function analisarRiscoCliente(cliente: Cliente): Promise<ResultadoPredicao> {
  const payload = {
    call_failure: cliente.callFailure,
    complains: cliente.complains ? 1 : 0,
    subscription_length: cliente.subscriptionLength,
    charge_amount: cliente.chargeAmount,
    seconds_of_use: cliente.secondsOfUse,
    frequency_of_use: cliente.frequencyOfUse,
    frequency_of_sms: cliente.frequencyOfSMS,
    distinct_called_numbers: cliente.distinctCalledNumbers,
    age_group: cliente.ageGroup,
    tariff_plan: cliente.tariffPlan,
    status: cliente.status ? 1 : 2,
    age: cliente.age,
    customer_value: cliente.customerValue || 0,
  };

  return (await avaliarRisco(payload)) as ResultadoPredicao;
}