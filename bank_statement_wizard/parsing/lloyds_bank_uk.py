from collections import OrderedDict

from bank_statement_wizard.ledger import Transaction
from bank_statement_wizard.parsing.parsing_utility import get_line_parser_from_ordered_dict
from bank_statement_wizard.parsing.parsing_utility import default_comment_char, default_delimiter


current_account_statement_line_parser = get_line_parser_from_ordered_dict(
    OrderedDict([
        ('transaction_date', to_stripped_string),
        ('transaction_type', to_stripped_string),
        ('sort_code', to_stripped_string),
        ('account_number', to_stripped_string),
        ('transaction_description', to_stripped_string),
        ('debit_amount', optional_str_to_float),
        ('credit_amount', optional_str_to_float),
        ('balance', optional_str_to_float)
    ])
)


current_account_statement_schema = {
    'delimiter': default_delimiter(),
    'is_ignore_line': lambda s: s.startswith(default_comment_char()) or s.startswith('Transaction'),
    'line_parser': current_account_statement_line_parser
}


def current_account_statement_entry_to_transaction(entry: Dict) -> Transaction:
    _amount = entry['credit_amount'] if entry['credit_amount'] is not None else -1.0 * entry['debit_amount']

    return Transaction(
        amount=_amount,
        date=entry['transaction_date'],
        description=entry['transaction_description'],
        additional_info=entry['transaction_type'],
    )


credit_card_statement_line_parser = get_line_parser_from_ordered_dict(
    OrderedDict([
        ('date', to_stripped_string),
        ('date_entered', to_stripped_string),
        ('reference', to_stripped_string),
        ('description', to_stripped_string),
        ('transaction_description', to_stripped_string),
        ('amount', optional_str_to_float)
    ])
)

credit_card_statement_schema = {
    'delimiter': default_delimiter(),
    'is_ignore_line': lambda s: s.startswith(default_comment_char()) or s.startswith('Date'),
    'line_parser': credit_card_statement_line_parser
}


def credit_card_statement_entry_to_transaction(entry: Dict) -> Transaction:
    return Transaction(
        amount=-1.0 * entry['amount'],
        date=entry['date'],
        description=entry['description'],
        additional_info=entry['reference'],
    )