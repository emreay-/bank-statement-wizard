from typing import List
from bank_statement_wizard.domain.ledger import Ledger, Transaction


def transactions() -> List[Transaction]:
    return [
        Transaction(
            date="2018-01-01",
            amount=-100.5,
        ),
        Transaction(
            date="2018-01-02",
            amount=-1589.5,
        ),
        Transaction(
            date="2018-01-03",
            amount=2500.0
        ),
        Transaction(
            date="2018-01-03",
            amount=37.0
        )
    ]


def test_ledger():
    expected_balance = 847.0
    expected_debit_balance = 1690.0
    expected_credit_balance = 2537.0
    ledger = Ledger().add_transactions(transactions())

    assert abs(expected_balance - ledger.balance) < 1e-3
    assert abs(expected_debit_balance - ledger.debit_balance) < 1e-3
    assert abs(expected_credit_balance - ledger.credit_balance) < 1e-3


def test_str():
    ledger = Ledger().add_transactions(transactions())
    expected_str = """Credit Balance   : 2537.00
Debit Balance    : 1690.00
--------------
Balance          : 847.00"""

    assert expected_str == str(ledger)
