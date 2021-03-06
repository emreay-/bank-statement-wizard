from typing import List, Dict
from collections import OrderedDict

from .parsing_utility import *
from ..domain.ledger import Transaction


def get_current_account_statement_line_parser():
    return get_line_parser_from_ordered_dict(
        OrderedDict([
            ("transaction_date", get_date_parser("%d/%m/%Y")),
            ("transaction_type", to_stripped_string),
            ("sort_code", to_stripped_string),
            ("account_number", to_stripped_string),
            ("transaction_description", to_stripped_string),
            ("debit_amount", optional_str_to_float),
            ("credit_amount", optional_str_to_float),
            ("balance", optional_str_to_float)
        ])
    )


def get_current_account_statement_schema():
    return {
        "delimiter": default_delimiter(),
        "is_ignore_line": lambda s: s.startswith(default_comment_char()) or s.startswith("Transaction"),
        "line_parser": get_current_account_statement_line_parser()
    }


def current_account_statement_entry_to_transaction(entry: Dict) -> Transaction:
    _amount = entry["credit_amount"] if entry["credit_amount"] is not None else - \
        1.0 * entry["debit_amount"]

    return Transaction(
        amount=_amount,
        date=entry["transaction_date"],
        description=entry["transaction_description"],
        info=entry["transaction_type"],
    )


def load_transactions_from_lloyds_bank_uk_current_account_statement(path_to_statement: str) -> List[Transaction]:
    parsed_entries = parse_csv_using_schema(
        path_to_statement, get_current_account_statement_schema())
    return [current_account_statement_entry_to_transaction(i) for i in parsed_entries]


def get_credit_card_statement_line_parser():
    return get_line_parser_from_ordered_dict(
        OrderedDict([
            ("date", get_date_parser("%d/%m/%Y")),
            ("date_entered", to_stripped_string),
            ("reference", to_stripped_string),
            ("description", to_stripped_string),
            ("transaction_description", to_stripped_string),
            ("amount", optional_str_to_float)
        ])
    )


def get_credit_card_statement_schema():
    return {
        "delimiter": default_delimiter(),
        "is_ignore_line": lambda s: s.startswith(default_comment_char()) or s.startswith("Date"),
        "line_parser": get_credit_card_statement_line_parser()
    }


def credit_card_statement_entry_to_transaction(entry: Dict) -> Transaction:
    return Transaction(
        amount=-1.0 * entry["amount"],
        date=entry["date"],
        description=entry["description"],
        info=entry["reference"],
    )


def load_transactions_from_lloyds_bank_uk_credit_card_statement(path_to_statement: str) -> List[Transaction]:
    parsed_entries = parse_csv_using_schema(
        path_to_statement, get_credit_card_statement_schema())
    return [credit_card_statement_entry_to_transaction(i) for i in parsed_entries]
