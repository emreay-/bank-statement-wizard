import os
import logging
from uuid import UUID
from copy import deepcopy
from datetime import date
from enum import Enum, unique
from typing import List, Dict, Tuple, Set, Union, Callable, Optional, Any

from ..domain import Ledger, Transaction, TransactionId
from ..logging import get_logger
from ..parsing.support import get_loader, SupportedStatementTypes

__all__ = ["BankStatementWizardModel", "SelectOperation"]


logger = get_logger()


@unique
class SelectOperation(str, Enum):
    select = "select"
    deselect = "deselect"


class BankStatementWizardModel:
    def __init__(self):
        self._statements: List[str] = []
        self.ledger: Ledger = Ledger()

        self.all_transaction_ids: Set[TransactionId] = set()
        self.selected_transaction_ids: Set[TransactionId] = set()
        self.operated_transaction_ids: Set[TransactionId] = set()
        self.transaction_id_to_table_index: Dict[TransactionId, int] = {}

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
            logger.error(f"Error while parsing {path}, cannot load transactions: {e}")

        self._statements.append(path)
        self._initialize_transaction_id_sets()

    def data(self, is_filtered: Optional[Callable[[Transaction], bool]] = None) -> List[Dict]:
        _data = []
        ledger = self.ledger if is_filtered is None else self.ledger.filtered(is_filtered=is_filtered)
        for i, t in enumerate(ledger.transactions, 1):
            transaction_data = t.dict()
            transaction_data.update({"#": i})
            _data.append(transaction_data)
        return _data

    def data_table_filter(self, is_filtered: Optional[Callable[[Transaction], bool]] = None
                          ) -> List[Callable[[Dict[str, Any]], bool]]:
        ledger = self.ledger if is_filtered is None else self.ledger.filtered(is_filtered=is_filtered)
        filtered_ids = [t.id for t in ledger.transactions]
        return [lambda x: x["id"] in filtered_ids]

    def data_table_filter_for_operated_transactions(self) -> List[Callable[[Dict[str, Any]], bool]]:
        t = self.data_table_filter(is_filtered=lambda t: t.id not in self.operated_transaction_ids)
        return t

    def transaction_select_deselect(self, transaction_id: TransactionId) -> SelectOperation:
        if transaction_id in self.selected_transaction_ids:
            self.selected_transaction_ids.remove(transaction_id)
            return SelectOperation.deselect
        else:
            self.selected_transaction_ids.add(transaction_id)
            return SelectOperation.select

    def _is_transaction_not_in_operated_set(self, t: Transaction) -> bool:
        return t.id not in self.operated_transaction_ids

    def balance_data(self) -> Tuple[List[date], List[float]]:
        _date, _balance = [], []
        for state in self.ledger.filtered(is_filtered=self._is_transaction_not_in_operated_set).balance_history:
            _date.append(state.date)
            _balance.append(state.balance)
        return _date, _balance

    def _initialize_transaction_id_sets(self):
        for i, t in enumerate(self.ledger.transactions):
            self.all_transaction_ids.add(t.id)
            self.transaction_id_to_table_index[t.id] = i
        self.operated_transaction_ids = deepcopy(self.all_transaction_ids)

    def set_selected_transactions_as_filtered(self):
        self.operated_transaction_ids = self.operated_transaction_ids.difference(self.selected_transaction_ids)

    def set_unselected_transactions_as_filtered(self):
        unselected_transaction_ids = self.all_transaction_ids.difference(self.selected_transaction_ids)
        self.operated_transaction_ids = self.operated_transaction_ids.difference(unselected_transaction_ids)

    def clear_selections(self):
        self.selected_transaction_ids = set()

    def clear_filters(self):
        self.operated_transaction_ids = deepcopy(self.all_transaction_ids)

    def clear(self):
        self.clear_filters()
        self.clear_selections()
