from typing import List


from .utility import Transaction


class Ledger:

    def __init__(self):
        self.debit_transactions = []    # money spent/withdrawn
        self.credit_transactions = []   # money deposited
        self.debit_balance = 0.0
        self.credit_balance = 0.0
        self.balance = 0.0

    def run(self, transactions: List[Transaction]) -> 'Ledger':
        self.separate_debit_and_credit_transactions(transactions)
        self.update_balance()
        return self

    def separate_debit_and_credit_transactions(self, transactions: List[Transaction]):
        for transaction in transactions:
            if transaction.debit_amount != None:
                self.debit_transactions.append(transaction)
            elif transaction.credit_amount != None:
                self.credit_transactions.append(transaction)

    def update_balance(self):
        self.debit_balance = sum(
            [transaction.debit_amount for transaction in self.debit_transactions])
        self.credit_balance = sum(
            [transaction.credit_amount for transaction in self.credit_transactions])
        self.balance = self.credit_balance - self.debit_balance

    def __str__(self):
        return '''Debit Balance   : {}
Credit Balance  : {}
--------------  
Balance         : {}'''.format(self.debit_balance,
                               self.credit_balance,
                               self.balance)
