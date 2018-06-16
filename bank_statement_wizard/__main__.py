import argparse

from .utility import load_json_file, create_named_tuple_with_name_and_fields, check_date
from .analysis import SimpleExpenseCategoryMatcher, regex_search_score
from .constants_and_types import accepted_statements
from .ledger import Ledger
from .report_generation import StatementReportGenerator


def date_type(date):
    if not check_date(date):
        raise argparse.ArgumentTypeError(
            '{} is not a valid date, it should be in dd-mm-yyyy format'.format(date))
    return date


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--expense_categories',
                        help='Json file with expense category keywords', required=True)
    parser.add_argument('-s', '--statement',
                        help='Path to statement in csv file', required=True)
    parser.add_argument('-t', '--type',
                        choices=list(accepted_statements.keys()), help='Statement type', required=True)
    parser.add_argument('-d', '--date', help='Statement date in dd-mm-yyyy format',
                        type=date_type, required=True)
    parser.add_argument('-o', '--output', help='Output directory path',
                        required=True)
    args = parser.parse_args()

    return args.expense_categories, args.statement, args.type, args.date, args.output


def process_statement(
    path_to_expense_categories: str,
    path_to_statement_csv: str,
    statement_type: str,
    statement_date: str,
    path_to_output_dir: str
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
    print('\n{}\n\n'.format(ledger))

    StatementReportGenerator()(
        path_to_output_dir=path_to_output_dir,
        statement_type=statement_type,
        statement_date=statement_date,
        ledger=ledger
    )


process_statement(*parse_arguments())
