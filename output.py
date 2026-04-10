"""Console output for analysis reports."""

from __future__ import annotations  # Enables postponed evaluation of type annotations

# Import specialized TypedDicts and data structures for type safety
from schemas import (
    AnalysisReport,
    AnomalyReport,
    DayOfWeekSpendRow,
    MerchantFrequencySummaryRow,
    MerchantSpendSummaryRow,
    MonthlyTrendRow,
)
# Import utility for consistent currency formatting (e.g., adding $ and commas)
from storage import format_money


def print_top_frequency(rows: list[MerchantFrequencySummaryRow]) -> None:
    """Prints a table showing merchants sorted by how often they appear."""
    print("Top merchants by frequency")  # Header title for the frequency table
    print(f"{'Rank':<6}{'Merchant':<28}{'Count':>8}")  # Column headers with fixed-width alignment
    print("-" * 42)  # Visual separator line for the table header
    for index, row in enumerate(rows, start=1):  # Iterate through rows with a counter starting at 1
        print(f"{index:<6}{row['merchant'][:27]:<28}{row['count']:>8}")  # Print rank, merchant (truncated), and count


def print_top_spend(rows: list[MerchantSpendSummaryRow]) -> None:
    """Prints a table showing merchants where the most total money was spent."""
    print("Top merchants by spend")  # Header title for the spend table
    print(f"{'Rank':<6}{'Merchant':<28}{'Total':>14}")  # Column headers with alignment for currency
    print("-" * 48)  # Visual separator line for the spend table
    for index, row in enumerate(rows, start=1):  # Loop through sorted merchant rows
        print(f"{index:<6}{row['merchant'][:27]:<28}{format_money(row['total']):>14}")  # Print rank, merchant, and formatted total


def print_day_breakdown(rows: list[DayOfWeekSpendRow]) -> None:
    """Prints spending statistics grouped by the day of the week."""
    print("Day-of-week breakdown")  # Header title for the day breakdown
    print(f"{'Day':<12}{'Count':>8}{'Total':>16}{'Average':>16}")  # Headers for day, volume, total, and mean spend
    print("-" * 52)  # Visual separator line for the day-of-week table
    for row in rows:  # Iterate through each day's data
        print(f"{row['day']:<12}{row['count']:>8}{format_money(row['total']):>16}{format_money(row['average']):>16}")  # Print stats for each day


def print_monthly_trends(rows: list[MonthlyTrendRow]) -> None:
    """Prints a comparison of spending across different months with trend indicators."""
    print("Monthly trend tracking")  # Header title for the monthly trend section
    print(f"{'Month':<10}{'Total Spend':>16}{'Trend':>12}")  # Headers for month name, spend, and the trend label
    print("-" * 40)  # Visual separator line for the trends table
    for row in rows:  # Loop through each month recorded in the data
        print(f"{row['month']:<10}{format_money(row['total']):>16}{row['trend']:>12}")  # Print month, amount, and trend (Up/Down)


def print_anomalies(report: AnomalyReport) -> None:
    """Prints transactions that significantly exceed the average for their category."""
    anomalies = report["anomalies"]  # Extract the list of anomalous transaction rows
    if not anomalies:  # Check if any anomalies were actually found
        print("No anomalies crossed the 3x category average threshold.")  # Friendly message if data is clean
        return  # Exit function early

    print("Anomalies")  # Header title for the anomaly report
    print(f"{'Date':<12}{'Merchant':<26}{'Amount':>12}{'Avg':>12}{'X Over':>10}")  # Headers including the multiplier column
    print("-" * 72)  # Visual separator line for the anomaly table
    for row in anomalies:  # Iterate through every flagged transaction
        print(
            f"{row['date'].isoformat():<12}"  # Format the date object as a string (YYYY-MM-DD)
            f"{row['merchant'][:25]:<26}"  # Print merchant name, truncated for layout
            f"{format_money(row['amount']):>12}"  # Print the specific transaction amount
            f"{format_money(row['category_average']):>12}"  # Print the average for comparison
            f"{row['multiple']:>10.2f}"  # Print how many times higher the amount was than the average
        )
    print()  # Add an empty line for spacing
    print(f"Affected categories: {', '.join(sorted(report['affected_categories']))}")  # List unique categories containing anomalies


def print_full_analysis(report: AnalysisReport, duplicate_count: int = 0) -> None:
    """Aggregates and prints every section of the transaction analysis report."""
    print_top_frequency(report["top_by_frequency"])  # Print the merchant frequency section
    print()  # Blank line separator
    print_top_spend(report["top_by_spend"])  # Print the merchant spend section
    print()  # Blank line separator
    print_day_breakdown(report["day_of_week"])  # Print the daily breakdown section
    print()  # Blank line separator

    weekend = report["weekend_vs_weekday"]  # Extract the weekend/weekday comparison data
    print(
        "Weekend vs weekday average spend: "  # Label for the average comparison
        f"{format_money(weekend['weekend_avg'])} vs {format_money(weekend['weekday_avg'])} "  # Print both averages
        f"({weekend['percentage_difference']:.1f}% difference)"  # Show the delta as a percentage
    )

    time_split = report["time_of_month"]  # Extract the pre/post payday split data
    print(
        "Time of month split: "  # Label for the temporal split
        f"pre-payday {format_money(time_split['pre_payday_total'])} "  # Total spent before the payday date
        f"vs post-payday {format_money(time_split['post_payday_total'])}"  # Total spent on/after the payday date
    )
    print()  # Blank line separator
    print_monthly_trends(report["monthly_trends"])  # Print the month-over-month trend section
    print()  # Blank line separator
    print_anomalies(report["anomaly_report"])  # Print the anomaly detection section
    print()  # Blank line separator
    print(f"Duplicate transactions skipped during load: {duplicate_count}")  # Inform user of skipped redundant data