import unittest

from .testing_utility import UnitTestBase
from .context import bank_statement_wizard
from bank_statement_wizard.ledger import Ledger
from bank_statement_wizard.utility import Transaction


class LedgerTests(UnitTestBase):

    @classmethod
    def setUpClass(cls):
        cls.__transactions = [
            Transaction(
                date='2018-01-01',
                amount=-100.5,
            ),
            Transaction(
                date='2018-01-02',
                amount=-1589.5,
            ),
            Transaction(
                date='2018-01-03',
                amount=2500.0
            ),
            Transaction(
                date='2018-01-03',
                amount=37.0
            )
        ]

    def setUp(self):
        self.__ledger = Ledger()

    def test_debit_balance(self):
        expected_debit_balance = 1690.0
        self.__ledger.run(self.__transactions)
        self.assertAlmostEqual(expected_debit_balance,
                               self.__ledger.debit_balance, places=3)

    def test_credit_balance(self):
        expected_credit_balance = 2537.0
        self.__ledger.run(self.__transactions)
        self.assertAlmostEqual(expected_credit_balance,
                               self.__ledger.credit_balance, places=3)

    def test_balance(self):
        expected_balance = 847.0
        self.__ledger.run(self.__transactions)
        self.assertAlmostEqual(
            expected_balance, self.__ledger.balance, places=3)

    def test_str(self):
        expected_str = '''Credit Balance   : 2537.00
Debit Balance    : 1690.00
--------------  
Balance          : 847.00'''
        self.__ledger.run(self.__transactions)
        self.assertEqual(expected_str, str(self.__ledger))


if __name__ == '__main__':
    unittest.main()
