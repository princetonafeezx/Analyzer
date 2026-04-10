from __future__ import annotations

from schemas import (
    AnalysisReport,
    AnomalyReport,
    DayOfWeekSpendRow,
    MerchantFrequencySummaryRow,
    MerchantSpendSummaryRow,
    MonthlyTrendRow,
)
from storage import format_money

def print_top_frequency(rows: list[MerchantFrequencySummaryRow]) -> None:
    print("Top merchants by frequency")
    print(f"{'Rank':<6}{'Merchant':<28}{'Count':>8}")
    print("-" * 42)
    for index, row in enumerate(rows, start=1):
        print(f"{index:<6}{row['merchant'][:27]:<28}{row['count']:>8}")
