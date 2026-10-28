"""Recurring schedules: which dates does a rule fall on?

Monthly-style schedules always count from the start date, so a rule that
starts on Jan 31 lands on Feb 28 (or 29) and then back on Mar 31, without
drifting to the 28th forever.
"""

import calendar
from collections.abc import Iterator
from datetime import date, timedelta

FREQUENCIES = ("once", "weekly", "biweekly", "semimonthly", "monthly", "quarterly", "yearly")

_DAY_STEPS = {"weekly": 7, "biweekly": 14}
_MONTH_STEPS = {"monthly": 1, "quarterly": 3, "yearly": 12}


def clamp_day(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def add_months(start: date, months: int, day: int | None = None) -> date:
    index = start.year * 12 + (start.month - 1) + months
    return clamp_day(index // 12, index % 12 + 1, day or start.day)


def occurrences(
    frequency: str,
    start: date,
    window_start: date,
    window_end: date,
    *,
    end: date | None = None,
    second_day: int | None = None,
) -> Iterator[date]:
    """Yield the rule's dates that fall within [window_start, window_end]."""
    if frequency not in FREQUENCIES:
        raise ValueError(f"unknown frequency: {frequency}")
    last = min(window_end, end) if end else window_end
    if last < start or last < window_start:
        return

    if frequency == "once":
        if window_start <= start <= last:
            yield start
        return

    if frequency in _DAY_STEPS:
        step = _DAY_STEPS[frequency]
        current = start
        if window_start > start:
            skipped = (window_start - start).days // step
            current = start + timedelta(days=skipped * step)
        while current <= last:
            if current >= window_start:
                yield current
            current += timedelta(days=step)
        return

    if frequency == "semimonthly":
        days = sorted({start.day, second_day or 15})
        month = 0
        while True:
            first_of_month = add_months(start.replace(day=1), month, 1)
            if first_of_month > last:
                return
            for day in days:
                current = clamp_day(first_of_month.year, first_of_month.month, day)
                if start <= current <= last and current >= window_start:
                    yield current
            month += 1

    step = _MONTH_STEPS[frequency]
    n = 0
    while True:
        current = add_months(start, n * step)
        if current > last:
            return
        if current >= window_start:
            yield current
        n += 1
