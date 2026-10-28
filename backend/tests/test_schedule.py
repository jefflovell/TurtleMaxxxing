from datetime import date

import pytest

from turtlemaxxxing.budget.schedule import occurrences


def dates(*args, **kwargs):
    return [d.isoformat() for d in occurrences(*args, **kwargs)]


def test_once():
    assert dates("once", date(2026, 11, 5), date(2026, 11, 1), date(2026, 11, 30)) == ["2026-11-05"]
    assert dates("once", date(2026, 10, 5), date(2026, 11, 1), date(2026, 11, 30)) == []


def test_biweekly_from_a_later_window():
    got = dates("biweekly", date(2026, 10, 2), date(2026, 11, 1), date(2026, 11, 30))
    assert got == ["2026-11-13", "2026-11-27"]


def test_weekly():
    got = dates("weekly", date(2026, 11, 2), date(2026, 11, 1), date(2026, 11, 20))
    assert got == ["2026-11-02", "2026-11-09", "2026-11-16"]


def test_monthly_end_of_month_does_not_drift():
    got = dates("monthly", date(2026, 1, 31), date(2026, 1, 1), date(2026, 4, 30))
    assert got == ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30"]


def test_leap_year():
    assert dates("yearly", date(2028, 2, 29), date(2029, 1, 1), date(2029, 12, 31)) == ["2029-02-28"]


def test_quarterly():
    got = dates("quarterly", date(2026, 1, 15), date(2026, 1, 1), date(2026, 12, 31))
    assert got == ["2026-01-15", "2026-04-15", "2026-07-15", "2026-10-15"]


def test_semimonthly():
    got = dates("semimonthly", date(2026, 11, 1), date(2026, 11, 1), date(2026, 12, 31), second_day=15)
    assert got == ["2026-11-01", "2026-11-15", "2026-12-01", "2026-12-15"]


def test_semimonthly_second_day_clamps_to_month_end():
    got = dates("semimonthly", date(2027, 2, 15), date(2027, 2, 1), date(2027, 2, 28), second_day=31)
    assert got == ["2027-02-15", "2027-02-28"]


def test_end_date_is_inclusive():
    got = dates("monthly", date(2026, 1, 10), date(2026, 1, 1), date(2026, 12, 31), end=date(2026, 3, 10))
    assert got == ["2026-01-10", "2026-02-10", "2026-03-10"]


def test_unknown_frequency():
    with pytest.raises(ValueError):
        list(occurrences("fortnightly-ish", date(2026, 1, 1), date(2026, 1, 1), date(2026, 2, 1)))
