from enum import Enum, unique
from datetime import date as _date
from dataclasses import dataclass


__all__ = ["Inclusivity", "DateRangeElement", "DateRange"]


@unique
class Inclusivity(str, Enum):
    open = "()"
    closed = "[]"


@dataclass
class DateRangeElement:
    date: _date
    inclusivity: Inclusivity


@dataclass
class DateRange:
    start: DateRangeElement
    end: DateRangeElement

    def __str__(self) -> str:
        _s = f"{str(self.start.date)}, {str(self.end.date)}"
        _interval_start = Inclusivity.open.value[0] if self.start.inclusivity is \
            Inclusivity.open else Inclusivity.closed.value[0]
        _interval_end = Inclusivity.open.value[-1] if self.start.inclusivity is \
            Inclusivity.open else Inclusivity.closed.value[-1]
        return f"{_interval_start}{_s}{_interval_end}"
