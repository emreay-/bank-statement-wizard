from datetime import date
from uuid import uuid5, UUID

from typing import List, Optional, Any, Tuple, Dict
from .date_range import DateRange, DateRangeElement, Inclusivity


__all__ = ["Transaction", "Ledger"]


class Transaction:
    _namespace = UUID("e0505487-55f2-4b8c-9218-6fd03b87138b")

    def __init__(
        self,
        amount: float,
        date: date,
        description: Optional[str] = None,
        info: Optional[Any] = None,
        category: Optional[str] = None,
        included: bool = True
    ):
        self._amount: float = amount
        self._date: date = date
        self._description: Optional[str] = description
        self._info: Optional[str] = info
        self._id: UUID = self._generate_id()

        self.category: str = category
        self.included: bool = included

    @staticmethod
    def fields() -> Tuple[str, ...]:
        return "date", "description", "amount", "info", "category"

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def date(self) -> date:
        return self._date

    @property
    def description(self) -> str:
        return str(self._description)

    @property
    def info(self) -> str:
        return str(self._info)

    @property
    def id(self) -> UUID:
        return self._id

    def dict(self) -> Dict[str, Any]:
        return {f: getattr(self, f) for f in self.fields}

    def __str__(self):
        return f"Date                  : {self.date}" \
               f"Amount                : {self.amount}" \
               f"Desc                  : {self.description}" \
               f"Info                  : {self.info}" \
               f"Transaction Category  : {self.category}"

    def _generate_id(self) -> UUID:
        return uuid5(self._namespace, f"{self.date},{self.description},{self.amount:.2f},{self.info}")


class LedgerState:
    def __init__(self, credit_balance: float = 0, debit_balance: float = 0):
        self.credit_balance = abs(credit_balance)
        self.debit_balance = abs(debit_balance)

    @property
    def balance(self):
        return self.credit_balance - self.debit_balance

    def apply(self, transaction: Transaction) -> "LedgerState":
        _output = LedgerState(self.credit_balance, self.debit_balance)
        if transaction.amount < 0:
            _output.debit_balance += abs(transaction.amount)
        else:
            _output.credit_balance += abs(transaction.amount)
        return _output


class Ledger:
    # https://en.wikipedia.org/wiki/Debits_and_credits#Terminology
    def __init__(self):
        self.transactions: List[Transaction] = []
        self.balance_history: List[Tuple[date, LedgerState]] = []

    @property
    def _latest_state(self) -> LedgerState:
        return self.balance_history[-1][-1]

    @property
    def balance(self):
        return self._latest_state.balance

    @property
    def debit_balance(self):
        return self._latest_state.debit_balance

    @property
    def credit_balance(self):
        return self._latest_state.credit_balance

    @property
    def debit_transactions(self) -> List[Transaction]:  # money spent/withdrawn
        return [t for t in self.transactions if t.amount < 0]

    @property
    def credit_transactions(self) -> List[Transaction]:  # money deposited
        return [t for t in self.transactions if t.amount > 0]

    @property
    def date_range(self) -> DateRange:
        return DateRange(
            start=DateRangeElement(
                date=self.transactions[0].date,
                inclusivity=Inclusivity.closed
            ),
            end=DateRangeElement(
                date=self.transactions[-1].date,
                inclusivity=Inclusivity.closed
            ),
        )

    def add_transaction(self, transaction: Transaction) -> "Ledger":
        self.transactions.append(transaction)
        self.transactions.sort(key=lambda t: t.date)
        self._compute_balance_history()
        return self

    def add_transactions(self, transactions: List[Transaction]) -> "Ledger":
        self.transactions += transactions
        self.transactions.sort(key=lambda t: t.date)
        self._compute_balance_history()
        return self

    def _compute_balance_history(self):
        self.balance_history = []
        state = LedgerState()
        for t in self.transactions:
            state = state.apply(t)
            self.balance_history.append((t.date, state))

    def filtered_balance_history(self) -> List[Tuple[date, LedgerState]]:
        filtered: List[Tuple[date, LedgerState]] = []
        state = LedgerState()
        for t in self.transactions:
            if t.included:
                state = state.apply(t)
                filtered.append((t.date, state))
        return filtered

    def __len__(self) -> int:
        return len(self.transactions)

    def __str__(self):
        return f"Credit Balance   : {self.credit_balance:.2f}\n" \
               f"Debit Balance    : {self.debit_balance:.2f}\n" \
               f"--------------\n" \
               f"Balance          : {self.balance:.2f}"
