from uuid import *
from typing import List
from datetime import date
from bank_statement_wizard.domain import Ledger, Transaction, DateRange, DateRangeElement, Inclusivity


def transactions() -> List[Transaction]:
    return [Transaction(date=date(2018, 1, 1), amount=-100.5),
            Transaction(date=date(2018, 1, 2), amount=-1589.5),
            Transaction(date=date(2018, 1, 3), amount=2500.0),
            Transaction(date=date(2018, 1, 3), amount=37.0)]


def test_ledger():
    expected_balance = 847.0
    expected_debit_balance = 1690.0
    expected_credit_balance = 2537.0
    expected_date_range = DateRange(
        start=DateRangeElement(date=date(2018, 1, 1), inclusivity=Inclusivity.closed),
        end=DateRangeElement(date=date(2018, 1, 3), inclusivity=Inclusivity.closed),
    )

    ledger = Ledger().add_transactions(transactions())

    assert abs(expected_balance - ledger.balance) < 1e-3
    assert abs(expected_debit_balance - ledger.debit_balance) < 1e-3
    assert abs(expected_credit_balance - ledger.credit_balance) < 1e-3
    assert expected_date_range == ledger.date_range


def test_str():
    ledger = Ledger().add_transactions(transactions())
    expected_str = """Credit Balance   : 2537.00
Debit Balance    : 1690.00
--------------
Balance          : 847.00"""

    assert expected_str == str(ledger)


def test_transaction_id():
    assert Transaction(date=date(2018, 1, 1), amount=-100.5).id == uuid5(
        Transaction._namespace, f"2018-01-01,None,-100.50,None"
    )
