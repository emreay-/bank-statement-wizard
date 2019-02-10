from collections import OrderedDict
from typing import Dict, Callable, TextIO, Any, List, Optional


def get_line_parser_from_ordered_dict(field_name_to_column_parser: OrderedDict):
    
    def _line_parser(line_tokens: List[str]) -> Dict[str, Any]:
        out = {}
        for token, (field_name, column_parser) in zip(line_tokens, field_name_to_column_parser.items()):
            out[field_name] = column_parser(token)
        return out

    return _line_parser


def parse_csv_using_schema(path_to_file: str, schema: Dict, output_data_type: str = 'list'):
    data = [] if output_data_type is 'list' else {}

    with open(path_to_file, 'r') as handle_to_file:
        for line in load_lines(handle_to_file):
            if schema['is_ignore_line'](line):
                continue

            tokens = line.strip().split(schema['delimiter'])
            if len(tokens) == 0:
                continue

            parsed_line = schema['line_parser'](tokens)
            if output_data_type is 'list':
                data.append(parsed_line)
            else:
                [data.get(key, []).append(value) for key, value in parsed_line]
    return data


def load_lines(file_handle: TextIO):
    for line in file_handle:
        yield line


def optional_str_to_float(data: Optional[str]):
    if data is not None and len(data) > 0:
        return float(data)
    return None


def to_stripped_string(data: str):
    return data.strip()


def default_comment_char():
    return '#'


def default_delimiter():
    return ','
