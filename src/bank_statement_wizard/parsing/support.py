from enum import Enum
from typing import Callable, List

from .lloyds_bank_uk import load_transactions_from_lloyds_bank_uk_credit_card_statement
from .lloyds_bank_uk import load_transactions_from_lloyds_bank_uk_current_account_statement


class SupportedStatementTypes(Enum):
    LloydsBankUKCurrentAccountStatement = "lloyds-debit"
    LloydsBankUKCreditCardStatement = "lloyds-credit"


def statement_types() -> List[str]:
    return [_type.value for _type in SupportedStatementTypes]


def get_loader(statement_type: str) -> Callable:
    if statement_type == SupportedStatementTypes.LloydsBankUKCurrentAccountStatement.value:
        return load_transactions_from_lloyds_bank_uk_current_account_statement
    elif statement_type == SupportedStatementTypes.LloydsBankUKCreditCardStatement.value:
        return load_transactions_from_lloyds_bank_uk_credit_card_statement
    raise ValueError("{} is not a valid statement type".format(statement_type))
