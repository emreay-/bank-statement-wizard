import re
from typing import Dict, List

from .utility import Transaction

ExpenseCategory = str


def regex_search_score(pattern: str, target: str):
    match = re.search(pattern, target)
    if match:
        return float(len(match.group(0))) / float(len(target))
    return 0.


def get_match_score_for_category(
    category_data: List[str],
    expense: Transaction
):
    scores = [regex_search_score(p, expense.description)
              for p in category_data]
    return max(scores)


class SimpleExpenseCategoryMatcher:

    def __init__(self, expense_class_data: Dict[ExpenseCategory, List[str]]):
        self._expense_category_data = expense_class_data

    def __call__(self, expense: Transaction) -> ExpenseCategory:
        category_scores = {category_name: get_match_score_for_category(category_data, expense)
                           for category_name, category_data in self._expense_category_data.items()}
        expense_class = max(category_scores.items(), key=lambda x: x[1])[0]
        expense.transaction_category = expense_class
        return expense_class

    def process_bulk(self, expenses: List[Transaction]) -> List[ExpenseCategory]:
        return [self(i) for i in expenses]
