import re
from typing import Dict, List, Optional, Tuple

from bank_statement_wizard.ledger import Transaction
from bank_statement_wizard.utility import filter_non_alphanumeric

ExpenseCategory = str


def regex_search_score(pattern: str, target: str) -> float:
    target = filter_non_alphanumeric(target)
    match = re.search(pattern, target, re.IGNORECASE)
    if match:
        return float(len(match.group(0))) / float(len(target))
    return 0.0


def get_match_score_for_category(
    category_data: List[str],
    expense: Transaction
):
    scores = [regex_search_score(p, expense.description)
              for p in category_data]
    return max(scores)


class SimpleExpenseCategoryMatcher:

    def __init__(
        self,
        expense_category_data: Dict[ExpenseCategory, List[str]],
        default_expense_category: Optional[str] = 'unidentified'
    ):
        self.expense_category_data = expense_category_data
        self.default_expense_category = default_expense_category

    def match_category_to_expense(self, expense: Transaction) -> ExpenseCategory:
        category_scores = {category_name: get_match_score_for_category(category_data, expense)
                           for category_name, category_data in self.expense_category_data.items()}
        expense_category = max(category_scores.items(), key=lambda x: x[1])[0]
        matching_score = category_scores[expense_category]

        if matching_score < 1e-3:
            expense_category = self.default_expense_category

        expense.category = expense_category
        return expense_category

    def match_bulk(self, expenses: List[Transaction]) -> List[ExpenseCategory]:
        return [self.match_category_to_expense(i) for i in expenses]


def group_transactions_using_category(transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
    groups = {}
    for _transaction in transactions:
        if _transaction.category:
            if _transaction.category not in groups:
                groups[_transaction.category] = []
            groups[_transaction.category].append(_transaction)
    return groups


def get_expense_stats_for_transaction_groups(
        grouped_transactions: Dict[str, List[Transaction]], balance: float) -> Optional[Dict[str, Tuple[float, float]]]:
    _stats = {}
    for category, transactions in grouped_transactions.items():
        _total = abs(sum([i.amount for i in transactions]))
        _percentage = _total / balance
        _stats[category] = (_total, _percentage)
    assert sum([i[1] for i in _stats.values()]) - 1.0 < 1e-3
    return _stats
