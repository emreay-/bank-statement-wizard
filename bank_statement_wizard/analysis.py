import re
from typing import Dict, List

from .utility import Transaction

ExpenseClass = str


def regex_search_score(pattern: str, target: str):
    match = re.search(pattern, target)
    if match:
        return float(len(match.group(0))) / float(len(target))
    return 0.


def get_match_score_for_class(
    class_data: List[str],
    expense: Transaction
):
    scores = [regex_search_score(p, expense.description)
              for p in class_data]
    return max(scores)


class SimpleExpenseClassMatcher:

    def __init__(self, expense_class_data: Dict[ExpenseClass, List[str]]):
        self._expense_class_data = expense_class_data

    def __call__(self, expense: Transaction) -> ExpenseClass:
        class_scores = {class_name: get_match_score_for_class(class_data, expense)
                        for class_name, class_data in self._expense_class_data.items()}
        return max(class_scores.items(), key=lambda x: x[1])[0]
