import os
import logging
from copy import deepcopy
from datetime import date
from typing import List, Dict, Tuple

from ..domain import Ledger
from ..parsing.support import get_loader, SupportedStatementTypes

__all__ = ["BankStatementWizardModel"]


_logger = logging.getLogger(__name__)


class BankStatementWizardModel:
    def __init__(self):
        self._statements: List[str] = []
        self.ledger: Ledger = Ledger()

    @property
    def has_data(self) -> bool:
        return len(self._statements) > 0

    @property
    def statements(self) -> List[str]:
        return deepcopy(self._statements)

    @property
    def number_of_transactions(self) -> int:
        return len(self.ledger)

    def add_statement(self, path: str, statement_type: SupportedStatementTypes = SupportedStatementTypes.default()):
        path = os.path.abspath(path)
        try:
            transactions = get_loader(statement_type.value)(path)
            self.ledger.add_transactions(transactions)
        except Exception as e:
            _logger.error(f"Error while parsing {path}, cannot load transactions: {e}")
        self._statements.append(path)

    @property
    def data(self) -> List[Dict]:
        _data = []
        for i, t in enumerate(self.ledger.transactions, 1):
            transaction_data = t.dict()
            transaction_data.update({"#": i})
            _data.append(transaction_data)
        return _data

    def get_transactions_based_on_selection(self, is_selected: bool) -> List[Dict]:
        _data = []
        for i, t in enumerate(self.ledger.transactions, 1):
            if is_selected == t.included:
                transaction_data = t.dict()
                transaction_data.update({"#": i})
                _data.append(transaction_data)
        return _data

    @property
    def balance_data(self) -> Tuple[List[date], List[float]]:
        _date, _balance = [], []
        for (_d, _state) in self.ledger.filtered_balance_history():
            _date.append(_d)
            _balance.append(_state.balance)
        return _date, _balance
