"""Scored column detection for categorized transaction CSV exports."""

from __future__ import annotations  # Enables future type hinting features for earlier Python versions

import re  # Import regular expressions for pattern matching
from collections.abc import Callable  # Import Callable for type hinting function arguments

from textutil import clean_text  # Import text normalization utility from the project


def _header_tokens(norm: str) -> set[str]:
    """Extracts alphanumeric words from a string as a set of unique tokens."""
    return set(re.findall(r"[a-z0-9]+", norm))  # Find all alphanumeric sequences and return as a set


def _score_date(norm: str, tokens: set[str]) -> float:
    """Calculates a confidence score for whether a column represents a date."""
    for phrase in (  # Check for high-confidence specific multi-word phrases
        "transaction date",
        "posting date",
        "posted date",
        "post date",
        "trans date",
        "value date",
        "book date",
    ):
        if phrase in norm:  # If a specific date phrase is found in the normalized string
            return 14.0  # Assign a near-maximum score
    if norm in {"date", "dt"}:  # Check for exact matches for 'date' or its abbreviation
        return 13.0  # Assign high score for direct match
    if "date" in tokens:  # Check if the individual word 'date' exists in the token set
        return 9.0  # Assign moderate score for keyword presence
    return 0.0  # Return zero if no date indicators are found


def _score_merchant(norm: str, tokens: set[str]) -> float:
    """Calculates a confidence score for whether a column represents a merchant or payee."""
    if norm in {"payee", "merchant", "vendor", "memo", "description", "narration"}:  # Exact matches for core merchant terms
        return 14.0  # Assign maximum score for exact identifier match
    for word in ("payee", "merchant", "vendor", "description", "memo", "narration", "counterparty"):  # Check for term presence
        if word in norm:  # If the word appears as part of the header string
            return 11.0  # Assign high-moderate score
    hits = tokens & {"payee", "merchant", "vendor", "memo", "description", "narration"}  # Find intersection of tokens and keywords
    if hits:  # If any keywords are present in the tokenized set
        return 10.0  # Assign moderate score
    if tokens == {"name"} or (tokens <= {"name", "merchant"} and "name" in tokens):  # Check for generic 'name' variants
        return 7.0  # Assign lower score for generic 'name' match
    return 0.0  # Return zero if no merchant indicators are found


def _score_amount(norm: str, tokens: set[str]) -> float:
    """Calculates a confidence score for whether a column represents a transaction amount."""
    if norm in {"amount", "amt", "debit", "credit"}:  # Exact matches for financial value columns
        return 14.0  # Assign maximum score
    if "amount" in tokens:  # Keyword check within the token set
        return 12.0  # Assign high score
    if tokens <= {"debit", "credit", "amount"} and (tokens & {"debit", "credit"}):  # Specific logic for debit/credit splits
        return 10.0  # Assign moderate score
    if norm == "total amount" or ("total" in tokens and "amount" in tokens):  # Check for 'total' combined with 'amount'
        return 11.0  # Assign moderate-high score
    if norm == "total" or tokens == {"total"}:  # Check for just the word 'total'
        return 5.0  # Assign low score as 'total' can be ambiguous
    return 0.0  # Return zero if no amount indicators are found


def _score_subcategory(norm: str, tokens: set[str]) -> float:
    """Calculates a confidence score for whether a column represents a specific subcategory."""
    compact = re.sub(r"[\s_-]+", "", norm)  # Remove spaces, underscores, and hyphens to check for concatenated variants
    if re.fullmatch(r"subcategory|subcat", compact) or "subcategory" in compact:  # Check for explicit subcategory strings
        return 15.0  # Assign highest score (priority over general category)
    if "sub" in tokens and "category" in tokens:  # Check for 'sub' and 'category' appearing separately
        return 13.0  # Assign high score
    if "sub" in tokens and "cat" in tokens:  # Check for 'sub' and abbreviated 'cat'
        return 10.0  # Assign moderate score
    for phrase in (  # Check for descriptive subcategory synonyms
        "child category",
        "detail category",
        "line category",
        "secondary category",
        "sub category",
    ):
        if phrase in norm:  # If specific synonym found in the string
            return 12.0  # Assign moderate-high score
    return 0.0  # Return zero if no subcategory indicators are found


def _score_category(norm: str, tokens: set[str]) -> float:
    """Calculates a confidence score for whether a column represents a primary category."""
    if _score_subcategory(norm, tokens) >= 10.0:  # If it looks like a subcategory, don't claim it as primary category
        return 0.0  # Yield priority to the subcategory logic
    for exact in (  # Check for explicit primary category names
        "category",
        "expense category",
        "transaction category",
        "main category",
        "parent category",
        "top category",
        "primary category",
    ):
        if norm == exact:  # Exact match check
            return 14.0  # Assign maximum score
    for phrase in ("expense type", "transaction type", "classification"):  # Check for categorical synonyms
        if phrase in norm:  # String containment check
            return 12.0  # Assign high score
    if "category" in tokens:  # Generic keyword check in tokens
        return 10.0  # Assign moderate score
    if norm == "type" or tokens == {"type"}:  # Check for simple 'type' column
        return 8.0  # Assign lower score
    if "class" in tokens and "sub" not in tokens:  # Check for classification keywords (avoiding sub-class)
        return 6.0  # Assign low score
    return 0.0  # Return zero if no category indicators are found


def _pick_column(
    headers_norm: list[str],
    taken: set[int],
    scorer: Callable[[str, set[str]], float],
    *,
    min_score: float,
) -> int | None:
    """Selects the best available column index for a field based on scoring logic."""
    best_i: int | None = None  # Track the index of the highest scoring column
    best_s = -1.0  # Track the value of the highest score found
    for i, header in enumerate(headers_norm):  # Iterate through all normalized header strings
        if i in taken:  # Skip columns that have already been assigned to a different logical field
            continue
        score = scorer(header, _header_tokens(header))  # Calculate score using the provided scorer function
        if score > best_s:  # If this score is better than the previous best
            best_s = score  # Update the best score
            best_i = i  # Update the best index
    if best_i is None or best_s < min_score:  # If no column was found or the best score is too weak
        return None  # Return None to indicate no confident match
    taken.add(best_i)  # Mark this column as assigned so it won't be reused
    return best_i  # Return the index of the detected column


def _fallback_slot(preferred: int, column_count: int, taken: set[int]) -> int | None:
    """Provides a positional fallback if heuristic scoring fails to identify a column."""
    if preferred < column_count and preferred not in taken:  # If the standard position is within range and available
        return preferred  # Return the preferred positional index
    for j in range(column_count):  # Otherwise, search for the first available unassigned column
        if j not in taken:
            return j  # Return the first free column
    return None  # Return None if all columns are occupied


def detect_columns(headers: list[str]) -> dict[str, int | None]:
    """Map logical fields to column indices using header text, then positional hints."""
    norm = [clean_text(h) for h in headers]  # Normalize all header strings for consistent matching
    n = len(headers)  # Total number of columns in the CSV
    taken: set[int] = set()  # Tracks which column indices have been mapped to logical fields
    mapping: dict[str, int | None] = {  # Initialize the mapping structure with None values
        "date": None,
        "merchant": None,
        "amount": None,
        "category": None,
        "subcategory": None,
    }

    # Apply heuristic scoring to find the most likely column for each field
    mapping["date"] = _pick_column(norm, taken, _score_date, min_score=5.0)  # Detect Date column
    mapping["merchant"] = _pick_column(norm, taken, _score_merchant, min_score=5.0)  # Detect Merchant column
    mapping["amount"] = _pick_column(norm, taken, _score_amount, min_score=5.0)  # Detect Amount column
    mapping["subcategory"] = _pick_column(norm, taken, _score_subcategory, min_score=9.0)  # Detect Subcategory column
    mapping["category"] = _pick_column(norm, taken, _score_category, min_score=4.0)  # Detect Category column

    # Fallback logic: If a field wasn't found by name, assume standard CSV positioning
    if mapping["date"] is None and n:  # Fallback for Date: usually the first column (0)
        slot = _fallback_slot(0, n, taken)
        if slot is not None:
            mapping["date"] = slot
            taken.add(slot)
    if mapping["merchant"] is None and n > 1:  # Fallback for Merchant: usually second (1)
        slot = _fallback_slot(1, n, taken)
        if slot is not None:
            mapping["merchant"] = slot
            taken.add(slot)
    if mapping["amount"] is None and n > 2:  # Fallback for Amount: usually third (2)
        slot = _fallback_slot(2, n, taken)
        if slot is not None:
            mapping["amount"] = slot
            taken.add(slot)
    if mapping["category"] is None and n > 3:  # Fallback for Category: usually fourth (3)
        slot = _fallback_slot(3, n, taken)
        if slot is not None:
            mapping["category"] = slot
            taken.add(slot)

    return mapping  # Return the final dictionary of logical field names to column indices