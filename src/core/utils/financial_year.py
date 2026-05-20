from __future__ import annotations

import datetime


def get_fy_start(date: datetime.date) -> datetime.date:
    """Returns the start date of the financial year (April 1st) for a given date."""
    if date.month >= 4:
        return datetime.date(date.year, 4, 1)
    return datetime.date(date.year - 1, 4, 1)


def get_fy_end(date: datetime.date) -> datetime.date:
    """Returns the end date of the financial year (March 31st) for a given date."""
    if date.month >= 4:
        return datetime.date(date.year + 1, 3, 31)
    return datetime.date(date.year, 3, 31)


def get_quarter_start(date: datetime.date) -> datetime.date:
    """Returns the start date of the current quarter (Standard RO quarters: AMJ, JAS, OND, JFM)."""
    if 4 <= date.month <= 6:
        return datetime.date(date.year, 4, 1)
    elif 7 <= date.month <= 9:
        return datetime.date(date.year, 7, 1)
    elif 10 <= date.month <= 12:
        return datetime.date(date.year, 10, 1)
    else:
        return datetime.date(date.year, 1, 1)


def get_next_month_end(date: datetime.date) -> datetime.date:
    """Returns the last day of the next calendar month."""
    year = date.year
    month = date.month + 1
    if month > 12:
        month = 1
        year += 1
    
    # Get first day of month after next_month
    next_next_month = month + 1
    next_next_year = year
    if next_next_month > 12:
        next_next_month = 1
        next_next_year += 1
    
    first_of_next_next = datetime.date(next_next_year, next_next_month, 1)
    return first_of_next_next - datetime.timedelta(days=1)
