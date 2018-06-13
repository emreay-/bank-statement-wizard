import re
from typing import Dict, List, Optional

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

    def __init__(
        self,
        expense_category_data: Dict[ExpenseCategory, List[str]],
        default_expense_category: Optional[str] = 'unidentified'
    ):
        self.expense_category_data = expense_category_data
        self.default_expense_category = default_expense_category

    def __call__(self, expense: Transaction) -> ExpenseCategory:
        category_scores = {category_name: get_match_score_for_category(category_data, expense)
                           for category_name, category_data in self.expense_category_data.items()}

        expense_category = max(category_scores.items(), key=lambda x: x[1])[0]
        matching_score = category_scores[expense_category]

        if matching_score < 1e-3:
            expense_category = self.default_expense_category

        expense.transaction_category = expense_category
        return expense_category

    def process_bulk(self, expenses: List[Transaction]) -> List[ExpenseCategory]:
        return [self(i) for i in expenses]
