from typing import List, Dict, Tuple, Optional, Any

__all__ = ["Transaction", "Ledger"]


# def categorize_transactions(transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
#     categorized_transactions = {}

#     for t in transactions:
#         if t.transaction_category not in categorized_transactions:
#             categorized_transactions[t.transaction_category] = []
#         categorized_transactions[t.transaction_category].append(t)

#     return categorized_transactionsq


class Transaction:
    def __init__(
        self,
        amount: float,
        date: Optional[str] = None,
        description: Optional[str] = None,
        additional_info: Optional[Any] = None,
        category: Optional[str] = None
    ):
        self.amount = amount
        self.date = date
        self.description = description
        self.additional_info = additional_info
        self.category = category

    def __str__(self):
        return f"Date                  : {self.date}" \
               f"Amount                : {self.amount}" \
               f"Desc                  : {self.description}" \
               f"Additional Info       : {self.additional_info}" \
               f"Transaction Category  : {self.category}"


class Ledger:
    # https://en.wikipedia.org/wiki/Debits_and_credits#Terminology
    def __init__(self):
        self._debit_transactions = []    # money spent/withdrawn
        self._credit_transactions = []   # money deposited
        self._debit_balance = 0.0
        self._credit_balance = 0.0
        self._balance = 0.0

    @property
    def balance(self):
        return self._balance

    @property
    def debit_balance(self):
        return self._debit_balance

    @property
    def credit_balance(self):
        return self._credit_balance

    @property
    def debit_transactions(self):
        return self._debit_transactions

    @property
    def credit_transactions(self):
        return self._credit_transactions

    @property
    def transactions(self):
        return sorted(self._debit_transactions + self._credit_transactions, key=lambda x: x.date)

    def add_transaction(self, transaction: Transaction) -> "Ledger":
        if transaction.amount < 0.0:
            self._debit_transactions.append(transaction)
            self._debit_balance += abs(transaction.amount)
        else:
            self._credit_transactions.append(transaction)
            self._credit_balance += abs(transaction.amount)

        self._balance = self._credit_balance - self._debit_balance
        return self

    def add_transactions(self, transactions: List[Transaction]) -> "Ledger":
        for t in transactions:
            self.add_transaction(t)
        return self

    def __str__(self):
        return f"Credit Balance   : {self.credit_balance:.2f}\n" \
               f"Debit Balance    : {self.debit_balance:.2f}\n" \
               f"--------------\n" \
               f"Balance          : {self.balance:.2f}"
