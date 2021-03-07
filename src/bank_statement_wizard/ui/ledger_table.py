import panwid
from typing import Callable

from ..logging import get_logger
from ..domain import TransactionId
from .model import BankStatementWizardModel, SelectOperation

logger = get_logger()

__all__ = ["LedgerTable"]


class LedgerTable(panwid.DataTable):
    def __init__(self, model: BankStatementWizardModel, input_handling: Callable, *args, **kwargs):
        self._model = model
        self._input_handling = input_handling
        kwargs.update({"data": self._model.data()})
        super().__init__(*args, **kwargs)

    def keypress(self, size, key):
        if key == "r":
            self.refresh()
        elif key == "enter":
            transaction_id = self.selection.data["id"]
            if self._model.transaction_select_deselect(transaction_id) is SelectOperation.select:
                self.set_row_as_selected(transaction_id)
            else:
                self.set_row_as_unselected(transaction_id)

        self._input_handling(key)
        super().keypress(size, key)

    def set_row_as_selected(self, transaction_id: TransactionId):
        self.get_row(index=self._model.transaction_id_to_table_index[transaction_id]).set_attr(
            "table_row_body highlight"
        )

    def set_row_as_unselected(self, transaction_id: TransactionId):
        self.get_row(index=self._model.transaction_id_to_table_index[transaction_id]).clear_attr(
            "table_row_body highlight"
        )
