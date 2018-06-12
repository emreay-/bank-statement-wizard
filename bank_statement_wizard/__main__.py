import argparse

from .utility import load_json_file, create_named_tuple_with_name_and_fields
from .analysis import SimpleExpenseCategoryMatcher, regex_search_score
from .constants_and_types import accepted_statements
from .ledger import Ledger


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--expense_categories',
                        help='Json file with expense category keywords', required=True)
    parser.add_argument('-s', '--statement',
                        help='Path to statement in csv file', required=True)
    parser.add_argument('-t', '--type',
                        choices=list(accepted_statements.keys()), help='Statement type', required=True)
    args = parser.parse_args()

    return args.expense_categories, args.statement, args.type


def process_statement(
    path_to_expense_categories: str,
    path_to_statement_csv: str,
    statement_type: str
):
    statement_entries = accepted_statements[statement_type].parser(
        path_to_statement_csv
    )
    transactions = accepted_statements[statement_type].converter.process_bulk(
        statement_entries
    )

    expense_categories = load_json_file(path_to_expense_categories)
    matcher = SimpleExpenseCategoryMatcher(expense_categories)
    matcher.process_bulk(transactions)

    ledger = Ledger().run(transactions)
    print(ledger)
    print('')
    [print(i) for i in ledger.get_transactions_with_category('None')]


process_statement(*parse_arguments())
