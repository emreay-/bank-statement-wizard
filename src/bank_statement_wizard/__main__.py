import argparse

from bank_statement_wizard.domain.ledger import Ledger
from bank_statement_wizard.domain.utility import load_category_data, check_date
from bank_statement_wizard.domain.analysis import SimpleExpenseCategoryMatcher, \
    group_transactions_using_category, get_expense_stats_for_transaction_groups
from bank_statement_wizard.report_generation import StatementReportGenerator
from bank_statement_wizard.parsing.support import get_loader, statement_types


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
                        choices=statement_types(), help='Statement type', required=True)
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
    ledger = Ledger()
    for transaction in get_loader(statement_type)(path_to_statement_csv):
        if transaction.amount < 0.0:
            ledger.add_debit_transaction(transaction)
        else:
            ledger.add_credit_transaction(transaction)

    expense_categories = load_category_data(path_to_expense_categories)
    matcher = SimpleExpenseCategoryMatcher(expense_categories)
    matcher.match_bulk(ledger.transactions)

    print('\n{}\n'.format(ledger))

    if ledger.debit_balance > 0.0:
        grouped_debit_transactions = group_transactions_using_category(
            ledger.debit_transactions)
        expense_stats = get_expense_stats_for_transaction_groups(
            grouped_debit_transactions, ledger.debit_balance)
    else:
        expense_stats = None

    StatementReportGenerator()(
        path_to_output_dir=path_to_output_dir,
        statement_type=statement_type,
        statement_date=statement_date,
        ledger=ledger,
        expense_stats=expense_stats
    )


process_statement(*parse_arguments())
