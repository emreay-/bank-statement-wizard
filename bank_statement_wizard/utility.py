from collections import namedtuple, OrderedDict
from typing import List, Dict, Callable, Optional, Tuple, Any
import csv
import ast
import json


def create_named_tuple_with_name_and_fields(name: str, fields: List[str]):
    new_tuple_type = namedtuple(typename=name, field_names=fields)
    new_tuple_type.__new__.__defaults__ = (
        None, ) * len(new_tuple_type._fields)
    return new_tuple_type


def load_json_file(path_to_json: str):
    with open(path_to_json, 'r') as handle:
        data = json.load(handle)
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
        debit_amount: Optional[float] = None,
        credit_amount: Optional[float] = None,
        description: Optional[str] = None,
        other: Optional[Any] = None,
        transaction_category: Optional[str] = None
    ):
        self.date = date
        self.debit_amount = abs(
            float(debit_amount)) if debit_amount != None else None
        self.credit_amount = abs(
            float(credit_amount)) if credit_amount != None else None
        self.description = description
        self.other = other
        self.transaction_category = transaction_category

    @property
    def amount(self):
        if self.debit_amount != None and self.credit_amount == None:
            return (-1.0) * self.debit_amount
        elif self.debit_amount == None and self.credit_amount != None:
            return self.credit_amount

    def __str__(self):
        return '''Date                  : {}
Debit Amount          : {}
Credit Amount         : {}
Desc                  : {}
Other                 : {}
Transaction Category  : {}\n'''.format(self.date,
                                       self.debit_amount,
                                       self.credit_amount,
                                       self.description,
                                       self.other,
                                       self.transaction_category)


class StatementEntryToTransactionConverter:

    def __init__(self, matching_entry_fields_in_order: List[str]):
        self._matching_entry_fields_in_order = matching_entry_fields_in_order

    def __call__(self, statement_entry) -> Transaction:
        return Transaction(
            *[getattr(statement_entry, i) if
              (i != '' != getattr(statement_entry, i)) else None
              for i in self._matching_entry_fields_in_order]
        )

    def process_bulk(self, statement_entries: List) -> List[Transaction]:
        return [self(i) for i in statement_entries]
