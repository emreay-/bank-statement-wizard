import os
import logging
from typing import List
from copy import deepcopy

from ..domain import Ledger
from ..parsing.support import get_loader, SupportedStatementTypes

__all__ = ["BankStatementWizardModel"]


_logger = logging.getLogger(__name__)


class BankStatementWizardModel:
    def __init__(self):
        self._statements: List[str] = []
        self._ledger: Ledger = Ledger()

    @property
    def has_data(self) -> bool:
        return len(self._statements) > 0

    @property
    def statements(self) -> List[str]:
        return deepcopy(self._statements)

    @property
    def ledger(self) -> Ledger:
        return deepcopy(self._ledger)

    @property
    def number_of_transactions(self) -> int:
        return len(self._ledger)

    def add_statement(self, path: str, statement_type: SupportedStatementTypes = SupportedStatementTypes.default()):
        path = os.path.abspath(path)
        try:
            transactions = get_loader(statement_type.value)(path)
            self._ledger.add_transactions(transactions)
        except Exception as e:
            _logger.error(f"Error while parsing {path}, cannot load transactions: {e}")
        self._statements.append(path)
