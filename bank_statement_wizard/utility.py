from collections import namedtuple, OrderedDict, defaultdict
from typing import List, Dict, Callable, Optional, Tuple, Any, Union
import csv
import ast
import json
import re


def check_date(date: str):
    date_regex = '^(0[1-9]|[12][0-9]|3[01])[-](0[1-9]|1[012])[-](19|20)\d\d$'
    return bool(re.match(date_regex, date))


def replace_non_alphanumeric(text: str, replace_with: str = ' '):
    return ''.join([char if char.isalnum() else replace_with for char in text])


def remove_consecutive_chars(text: str, char: str):
    return char.join([i for n, i in enumerate(text.split(char)) if i != '' or n == 0])


def filter_non_alphanumeric(text: str):
    filtered = replace_non_alphanumeric(text, replace_with=' ')
    filtered = remove_consecutive_chars(filtered, char=' ')
    return filtered


def create_named_tuple_with_name_and_fields(name: str, fields: List[str]):
    new_tuple_type = namedtuple(typename=name, field_names=fields)
    new_tuple_type.__new__.__defaults__ = (
        None, ) * len(new_tuple_type._fields)
    return new_tuple_type


def load_json_file(path_to_json: str):
    with open(path_to_json, 'r') as handle:
        data = json.load(handle)
        return data


def load_category_data(path_to_category_data: str):
    data = load_json_file(path_to_category_data)
    for category, keywords_list in data.items():
        data[category] = [filter_non_alphanumeric(i) for i in keywords_list]
    return data


def parse_csv_to_list(
    path_to_csv: str,
    fields: List[str],
    header: bool = True,
    converter: Optional[Callable] = dict
) -> List:

    with open(path_to_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fields)
        if header:
            next(reader)
        return [converter(r) for r in reader]


class CsvParser:

    def __init__(
        self,
        fields: List[str],
        converter: Optional[Callable] = dict
    ):

        self._fields = fields
        self._converter = converter

    def __call__(
        self,
        path_to_csv: str,
        header: bool = True
    ) -> List:

        return parse_csv_to_list(
            path_to_csv=path_to_csv,
            fields=self._fields,
            header=header,
            converter=self._converter
        )


def convert_fields(data: List[str]) -> List:
    converted = []
    for i in data:
        try:
            converted.append(ast.literal_eval(i))
        except Exception:
            converted.append(i.lower())
    return converted


def create_new_entry_type_and_csv_parser(
    type_name: str,
    csv_fields: List[str]
) -> Tuple[namedtuple, Callable]:

    new_entry_type = create_named_tuple_with_name_and_fields(
        name=type_name, fields=csv_fields
    )

    def _converter(csv_line: OrderedDict):
        return new_entry_type(
            *convert_fields(
                data=[value for key, value in csv_line.items()
                      ][:len(csv_fields)],
            )
        )

    csv_parser = CsvParser(fields=csv_fields, converter=_converter)

    return new_entry_type, csv_parser


class Transaction:

    def __init__(
        self,
        date: Optional[str] = None,
        amount: Optional[float] = None,
        description: Optional[str] = None,
        other: Optional[Any] = None,
        transaction_category: Optional[str] = None
    ):
        self._date = date
        self._amount = float(amount) if amount != None else None
        self._description = description
        self._other = other
        self._transaction_category = transaction_category

    @property
    def date(self):
        return self._date

    @property
    def amount(self):
        return self._amount

    @property
    def description(self):
        return self._description

    @property
    def other(self):
        return self._other

    @property
    def transaction_category(self):
        return self._transaction_category

    @transaction_category.setter
    def transaction_category(self, value):
        self._transaction_category = value

    def __str__(self):
        return '''Date                  : {}
Amount                : {}
Desc                  : {}
Other                 : {}
Transaction Category  : {}\n'''.format(self.date,
                                       self.amount,
                                       self.description,
                                       self.other,
                                       self.transaction_category)


class StatementEntryToTransactionConverter:

    def __init__(
        self,
        matching_entry_fields_in_order: List[Union[str, List[str]]],
        field_name_to_process_function: Optional[Dict[str, Callable]] = None
    ):
        assert len(self.transaction_fields) == len(
            matching_entry_fields_in_order)

        self._matching_entry_fields = {
            innate_field: matching_fields for innate_field, matching_fields in
            zip(self.transaction_fields, matching_entry_fields_in_order)
        }
        self.field_name_to_process_function = field_name_to_process_function if \
            field_name_to_process_function != None else {}

    def __call__(self, statement_entry) -> Transaction:
        _values = defaultdict(lambda: None)
        for innate_field, matching_fields in self._matching_entry_fields.items():
            if type(matching_fields) == str:
                _values[innate_field] = self._get_field_value(
                    statement_entry, matching_fields)
            else:
                for field in matching_fields:
                    _value = self._get_field_value(statement_entry, field)
                    if _value != None:
                        _values[innate_field] = _value
                        break

        return Transaction(_values['date'], _values['amount'], _values['description'], _values['other'])

    def _get_field_value(self, statement_entry, field):
        if self._is_valid_field(field):
            _value = getattr(statement_entry, field)
            if self._is_valid_field_value(_value):
                if field in self.field_name_to_process_function:
                    _value = self.field_name_to_process_function[field](_value)
                return _value
        return None

    @staticmethod
    def _is_valid_field(field: str):
        return field != ''

    @staticmethod
    def _is_valid_field_value(value):
        return value != '' and value != None

    def process_bulk(self, statement_entries: List) -> List[Transaction]:
        return [self(i) for i in statement_entries]

    @property
    def transaction_fields(self):
        return ['date', 'amount', 'description', 'other']
