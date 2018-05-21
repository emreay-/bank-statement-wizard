from .utility import load_json_file
from .analysis import SimpleExpenseClassMatcher, regex_search_score

js = load_json_file('/home/vetenskap/classes.json')
print(js)

matcher = SimpleExpenseClassMatcher(js)


class Transaction:

    def __init__(self, description):
        self.description = description


c = matcher(Transaction('kebab king asdf S'))
print(c)
