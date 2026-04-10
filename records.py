"""Normalize and validate rows used by spending analysis."""

from __future__ import annotations  # Enables forward references for type hints

import math  # Import math for finite number validation (NaN/Infinity checks)
from collections.abc import Mapping, Sequence  # Import abstract base classes for container type hinting
from datetime import date  # Import date object for temporal data handling
from typing import Any  # Import Any for flexible dictionary value hinting

from parsing import parse_amount, parse_date  # Import custom project utilities for string-to-data conversion
from schemas import CategorizedRecord  # Import the TypedDict definition for validated records


def normalize_analysis_record(raw: Mapping[str, Any]) -> CategorizedRecord:
    """Build a :class:`CategorizedRecord` and reject unusable rows."""
    if "date" not in raw:  # Check if the 'date' key exists in the input mapping
        raise ValueError("missing required field 'date'")  # Raise error if date is missing
    d_raw = raw["date"]  # Retrieve the raw date value
    if isinstance(d_raw, date):  # Check if the value is already a datetime.date object
        parsed_date: date = d_raw  # Use the object directly if already parsed
    else:
        parsed_date = parse_date(str(d_raw))  # Convert to string and use custom parser for raw text

    if "amount" not in raw:  # Check if the 'amount' key exists in the input mapping
        raise ValueError("missing required field 'amount'")  # Raise error if amount is missing
    amt_raw = raw["amount"]  # Retrieve the raw amount value
    if type(amt_raw) is bool:  # Explicitly check for booleans as they behave like 0/1 in math
        raise ValueError("invalid amount type")  # Reject booleans to prevent logical errors
    try:
        if isinstance(amt_raw, (int, float)):  # If already a numeric type
            amount = float(amt_raw)  # Ensure it is represented as a float
        else:
            amount = parse_amount(str(amt_raw))  # Use custom parser to handle currency symbols/commas
    except (TypeError, ValueError) as exc:  # Catch parsing or type conversion failures
        raise ValueError(f"invalid amount {amt_raw!r}") from exc  # Wrap and re-raise with context
    if math.isnan(amount) or math.isinf(amount):  # Ensure the number is a valid, real-world value
        raise ValueError("amount must be a finite number")  # Reject NaN or Infinity

    merchant = str(raw.get("merchant", "")).strip()  # Get merchant, default to empty, and trim whitespace
    category = str(raw.get("category", "Unknown")).strip() or "Unknown"  # Get category, fallback to 'Unknown' if empty
    sub_raw = raw.get("subcategory", category)  # Attempt to get subcategory, fallback to parent category name
    subcategory = str(sub_raw).strip() or category  # Clean subcategory string or use parent category as final fallback

    if type(amount) is bool:  # Secondary safety check to ensure amount didn't become a boolean
        raise TypeError("amount must be numeric, not bool")  # Raise type error for boolean values
    if not isinstance(amount, (int, float)):  # Final validation that amount is a standard number type
        raise TypeError("amount must be int or float after normalization")  # Ensure numeric integrity

    rec: CategorizedRecord = {  # Construct the strictly-typed dictionary
        "date": parsed_date,  # Assign the validated date object
        "merchant": merchant,  # Assign the cleaned merchant string
        "amount": float(amount),  # Store the final amount as a float
        "category": category,  # Assign the primary category
        "subcategory": subcategory,  # Assign the subcategory
    }
    return rec  # Return the cleaned and validated record


def coerce_analysis_records(records: Sequence[Mapping[str, Any]]) -> list[CategorizedRecord]:
    """Validate each mapping; raises :class:`ValueError` with index on first bad row."""
    out: list[CategorizedRecord] = []  # Initialize an empty list to hold validated records
    for index, row in enumerate(records):  # Iterate through the input sequence with a counter
        try:
            out.append(normalize_analysis_record(row))  # Attempt to normalize and add the record to output
        except ValueError as exc:  # Catch validation errors from the normalization function
            raise ValueError(f"Invalid record at index {index}: {exc}") from exc  # Provide the row index for debugging
    return out  # Return the list of all successfully coerced records