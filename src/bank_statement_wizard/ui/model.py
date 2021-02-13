import os
import logging
from typing import List, Dict
from copy import deepcopy

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
