from collections import namedtuple, OrderedDict
from typing import List, Dict, Callable, Optional, Tuple
import csv
import ast


def create_named_tuple_with_name_and_fields(name: str, fields: List[str]):
    new_tuple_type = namedtuple(typename=name, field_names=fields)
    new_tuple_type.__new__.__defaults__ = (
        None, ) * len(new_tuple_type._fields)
    return new_tuple_type


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


def convert_to_literal(data: List[str]) -> List:
    converted = []
    for i in data:
        try:
            converted.append(ast.literal_eval(i))
        except Exception:
            converted.append(i)
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
            *convert_to_literal(
                data=[value for key, value in csv_line.items()
                      ][:len(csv_fields)],
            )
        )

    csv_parser = CsvParser(fields=csv_fields, converter=_converter)

    return new_entry_type, csv_parser
