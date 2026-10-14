r"""Cadastra (ou remove) os clientes de demonstracao na carteira.

Para a apresentacao, a carteira precisa ter clientes nas tres faixas de risco,
com resultado conhecido de antemao. Este script grava sete clientes ficticios
na colecao `clientes`, no MESMO formato que o aplicativo grava pelo
`dbService.ts`, usando os dados dos casos de referencia do modelo. Assim quem
apresenta sabe qual faixa cada cliente deve mostrar.

Os documentos tem identificador fixo (`demo-01` a `demo-07`) e o campo
`demonstracao: true`. Rodar de novo sobrescreve os mesmos sete, sem duplicar.
Clientes cadastrados por pessoas nao sao tocados.

USO (PowerShell, dentro de api/ com o venv ativo e o serviceAccountKey.json
no lugar de sempre)
    python semear_demonstracao.py            grava ou restaura os sete
    python semear_demonstracao.py --limpar   remove os sete

Tambem e o procedimento de recuperacao: se alguem apagar ou editar um cliente
de demonstracao durante o ensaio, rodar de novo devolve tudo ao estado inicial.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))

CASOS = RAIZ / "ml" / "artefatos" / "casos_de_referencia.json"
COLECAO = "clientes"

# Nomes ficticios, um por caso de referencia, na mesma ordem do arquivo.
NOMES = [
    "Ana Beatriz Lima",
    "Bruno Carvalho",
    "Carla Menezes",
    "Daniel Souza",
    "Eduarda Freitas",
    "Fabio Nascimento",
    "Gabriela Rocha",
]


def para_o_formato_do_app(entrada: dict, nome: str, agora: datetime) -> dict:
    """Converte a entrada do modelo para o formato de `Cliente` do app.

    Espelha, ao contrario, a conversao de app/src/services/churnService.ts:
        complains: booleano no app, 0/1 na API
        status:    booleano no app (true = ativo), 1/2 na API (1 = ativo)
    """
    return {
        "nome": nome,
        "callFailure": int(entrada["call_failure"]),
        "complains": bool(entrada["complains"]),
        "subscriptionLength": int(entrada["subscription_length"]),
        "chargeAmount": int(entrada["charge_amount"]),
        "secondsOfUse": int(entrada["seconds_of_use"]),
        "frequencyOfUse": int(entrada["frequency_of_use"]),
        "frequencyOfSMS": int(entrada["frequency_of_sms"]),
        "distinctCalledNumbers": int(entrada["distinct_called_numbers"]),
        "status": int(entrada["status"]) == 1,
        "age": int(entrada["age"]),
        "ageGroup": int(entrada["age_group"]),
        "tariffPlan": int(entrada["tariff_plan"]),
        "customerValue": float(entrada["customer_value"]),
        "createdAt": agora,
        "updatedAt": agora,
        "demonstracao": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limpar", action="store_true", help="remove os clientes de demonstracao")
    args = parser.parse_args()

    import db

    try:
        colecao = db.obter_db().collection(COLECAO)
    except db.ErroDePersistencia as erro:
        print(f"Nao consegui acessar o Firestore: {erro}")
        print("Confira se api/serviceAccountKey.json esta no lugar.")
        return 1

    casos = json.loads(CASOS.read_text(encoding="utf-8"))
    if len(casos) > len(NOMES):
        print(f"Ha {len(casos)} casos e so {len(NOMES)} nomes. Acrescente nomes em NOMES.")
        return 1

    ids = [f"demo-{i:02d}" for i in range(1, len(casos) + 1)]

    if args.limpar:
        for ident in ids:
            colecao.document(ident).delete()
        print(f"{len(ids)} clientes de demonstracao removidos.")
        return 0

    agora = datetime.now(timezone.utc)
    print(f"{'id':<8} {'nome':<20} {'faixa esperada':<15} probabilidade")
    for ident, nome, caso in zip(ids, NOMES, casos):
        colecao.document(ident).set(para_o_formato_do_app(caso["entrada"], nome, agora))
        print(f"{ident:<8} {nome:<20} {caso['faixa_esperada']:<15} {caso['probabilidade_esperada']:.2%}")

    print()
    print(f"{len(ids)} clientes gravados em '{COLECAO}'.")
    print("Copie esta tabela para o roteiro da apresentacao.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())