from typing import List, Dict

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
            if transaction.debit_amount != None:
                self.debit_transactions.append(transaction)
            elif transaction.credit_amount != None:
                self.credit_transactions.append(transaction)

    def categorize_transactions(self):
        self.categorized_debit_transactions = categorize_transactions(
            self.debit_transactions)
        self.categorized_credit_transactions = categorize_transactions(
            self.credit_transactions)

    def update_balance(self):
        self.debit_balance = sum(
            [transaction.debit_amount for transaction in self.debit_transactions])
        self.credit_balance = sum(
            [transaction.credit_amount for transaction in self.credit_transactions])
        self.balance = self.credit_balance - self.debit_balance

    def get_transactions_with_category(self, category: str) -> List[Transaction]:
        transactions = []
        if category in self.categorized_credit_transactions:
            transactions += self.categorized_credit_transactions[category]
        if category in self.categorized_debit_transactions:
            transactions += self.categorized_debit_transactions[category]
        return transactions

    def generate_report(self) -> 'Ledger':
        pass

    def __str__(self):
        return '''Debit Balance   : {}
Credit Balance  : {}
--------------  
Balance         : {}'''.format(self.debit_balance,
                               self.credit_balance,
                               self.balance)
