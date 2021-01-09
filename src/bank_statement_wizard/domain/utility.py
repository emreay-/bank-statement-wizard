from collections import OrderedDict, defaultdict
from typing import List, Dict, Callable, Optional, Tuple, Any, Union
import csv
import ast
import json
import re

__all__ = ["check_date", "replace_non_alphanumeric", "remove_consecutive_chars", "filter_non_alphanumeric",
           "load_json_file", "load_category_data"]


def check_date(date: str):
    date_regex = "^(0[1-9]|[12][0-9]|3[01])[-](0[1-9]|1[012])[-](19|20)\d\d$"
    return bool(re.match(date_regex, date))


def replace_non_alphanumeric(text: str, replace_with: str = " "):
    return ''.join([char if char.isalnum() else replace_with for char in text])


def remove_consecutive_chars(text: str, char: str):
    return char.join([i for n, i in enumerate(text.split(char)) if i != '' or n == 0])


def filter_non_alphanumeric(text: str):
    filtered = replace_non_alphanumeric(text, replace_with=" ")
    filtered = remove_consecutive_chars(filtered, char=" ")
    return filtered


def load_json_file(path_to_json: str):
    with open(path_to_json, "r") as handle:
        data = json.load(handle)
        return data


def load_category_data(path_to_category_data: str):
    data = load_json_file(path_to_category_data)
    for category, keywords_list in data.items():
        data[category] = [filter_non_alphanumeric(i) for i in keywords_list]
    return data
