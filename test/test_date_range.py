from datetime import date
from bank_statement_wizard.domain import DateRange, DateRangeElement, Inclusivity


def test_date_range_str():
    start_date = date(1999, 5, 5)
    end_date = date(2019, 5, 5)

    assert f"[{str(start_date)}, {str(end_date)}]" == str(DateRange(
        start=DateRangeElement(date=start_date, inclusivity=Inclusivity.closed),
        end=DateRangeElement(date=end_date, inclusivity=Inclusivity.closed)
    ))

    assert f"[{str(start_date)}, {str(end_date)})" == str(DateRange(
        start=DateRangeElement(date=start_date, inclusivity=Inclusivity.closed),
        end=DateRangeElement(date=end_date, inclusivity=Inclusivity.open)
    ))

    assert f"({str(start_date)}, {str(end_date)})" == str(DateRange(
        start=DateRangeElement(date=start_date, inclusivity=Inclusivity.open),
        end=DateRangeElement(date=end_date, inclusivity=Inclusivity.open)
    ))

    assert f"({str(start_date)}, {str(end_date)}]" == str(DateRange(
        start=DateRangeElement(date=start_date, inclusivity=Inclusivity.open),
        end=DateRangeElement(date=end_date, inclusivity=Inclusivity.closed)
    ))
