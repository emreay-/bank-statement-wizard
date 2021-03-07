from dataclasses import dataclass


__all__ = ["SortInfo"]


@dataclass
class SortInfo:
    field_name: str
    is_reverse: bool
