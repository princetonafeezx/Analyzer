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

def print_top_spend(rows: list[MerchantSpendSummaryRow]) -> None:
    print("Top merchants by spend")
    print(f"{'Rank':<6}{'Merchant':<28}{'Total':>14}")
    print("-" * 48)
    for index, row in enumerate(rows, start=1):
        print(f"{index:<6}{row['merchant'][:27]:<28}{format_money(row['total']):>14}")

def print_day_breakdown(rows: list[DayOfWeekSpendRow]) -> None:
    print("Day-of-week breakdown")
    print(f"{'Day':<12}{'Count':>8}{'Total':>16}{'Average':>16}")
    print("-" * 52)
    for row in rows:
        print(f"{row['day']:<12}{row['count']:>8}{format_money(row['total']):>16}{format_money(row['average']):>16}")

def print_monthly_trends(rows: list[MonthlyTrendRow]) -> None:
    print("Monthly trend tracking")
    print(f"{'Month':<10}{'Total Spend':>16}{'Trend':>12}")
    print("-" * 40)
    for row in rows:
        print(f"{row['month']:<10}{format_money(row['total']):>16}{row['trend']:>12}")
