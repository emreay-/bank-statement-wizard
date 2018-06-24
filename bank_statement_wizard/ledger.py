from typing import List, Dict, Tuple, Optional

from .utility import Transaction


def categorize_transactions(transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
    categorized_transactions = {}

    for t in transactions:
        if t.transaction_category not in categorized_transactions:
            categorized_transactions[t.transaction_category] = []
        categorized_transactions[t.transaction_category].append(t)

    return categorized_transactions


class Ledger:

    def __init__(self):
        self.debit_transactions = []    # money spent/withdrawn
        self.credit_transactions = []   # money deposited
        self.categorized_debit_transactions = {}
        self.categorized_credit_transactions = {}
        self.debit_balance = 0.0
        self.credit_balance = 0.0
        self.balance = 0.0

    def run(self, transactions: List[Transaction]) -> 'Ledger':
        self.separate_debit_and_credit_transactions(transactions)
        self.categorize_transactions()
        self.update_balance()
        return self

    def separate_debit_and_credit_transactions(self, transactions: List[Transaction]):
        for transaction in transactions:
            if transaction.amount == None:
                continue
            elif transaction.amount <= 0.0:
                self.debit_transactions.append(transaction)
            elif transaction.amount > 0.0:
                self.credit_transactions.append(transaction)

    def categorize_transactions(self):
        self.categorized_debit_transactions = categorize_transactions(
            self.debit_transactions)
        self.categorized_credit_transactions = categorize_transactions(
            self.credit_transactions)

    def update_balance(self):
        self.debit_balance = abs(sum(
            [transaction.amount for transaction in self.debit_transactions]))
        self.credit_balance = abs(sum(
            [transaction.amount for transaction in self.credit_transactions]))
        self.balance = self.credit_balance - self.debit_balance

    def get_transactions_with_category(self, category: str) -> List[Transaction]:
        transactions = []
        if category in self.categorized_credit_transactions:
            transactions += self.categorized_credit_transactions[category]
        if category in self.categorized_debit_transactions:
            transactions += self.categorized_debit_transactions[category]
        return transactions

    def get_expense_stats(self) -> Optional[Dict[str, Tuple[float, float]]]:
        if self.debit_balance > 0.0:
            _stats = {}
            for category, transactions in self.categorized_debit_transactions.items():
                _total = abs(sum([i.amount for i in transactions]))
                _percentage = _total/self.debit_balance
                _stats[category] = (_total, _percentage)
            assert sum([i[1] for i in _stats.values()]) - 1.0 < 1e-3
            return _stats
        return

    def __str__(self):
        return '''Credit Balance   : {:.2f}
Debit Balance    : {:.2f}
--------------  
Balance          : {:.2f}'''.format(self.credit_balance,
                                    self.debit_balance,
                                    self.balance)

    def __iter__(self):
        return iter(self.debit_transactions + self.credit_transactions)

    @property
    def categories(self):
        return list(set([i.transaction_category for i in self]))
