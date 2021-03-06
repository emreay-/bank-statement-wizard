import panwid
from typing import Callable

from ..logging import get_logger
from .model import BankStatementWizardModel

logger = get_logger()

__all__ = ["LedgerTable"]


class LedgerTable(panwid.DataTable):
    def __init__(self, model: BankStatementWizardModel, input_handling: Callable, *args, **kwargs):
        self._model = model
        self._input_handling = input_handling
        super().__init__(*args, **kwargs)

    def keypress(self, size, key):
        if key == "r":
            self.refresh()
        elif key == "enter":
            selected_index = self.selection.data["index"]
            if self._model.ledger.transactions[selected_index].included:
                self._model.ledger.transactions[selected_index].included = False
                self.selection.set_attr("red")
            else:
                self._model.ledger.transactions[selected_index].included = True
                self.selection.clear_attr("red")
        self._input_handling(key)
        super().keypress(size, key)
