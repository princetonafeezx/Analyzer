"""Spending statistics and bundled report generation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from parsing import parse_date
from records import coerce_analysis_records
from schemas import (
    AnalysisReport,
    AnomalyReport,
    CategorizedRecord,
    DayOfWeekSpendRow,
    MerchantFrequencySummaryRow,
    MerchantSpendSummaryRow,
    MonthlyTrendLiteral,
    MonthlyTrendRow,
    SpendingAnomalyRow,
    TimeOfMonthSplit,
    WeekendWeekdaySummary,
)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _record_date(record: CategorizedRecord) -> date:
    """Normalize transaction date to :class:`datetime.date` for metrics."""
    d_raw = record["date"]
    if isinstance(d_raw, date):
        return d_raw
    return parse_date(str(d_raw))


def _merchant_freq_row(merchant: str, count: int) -> MerchantFrequencySummaryRow:
    return {"merchant": merchant, "count": count}


def _merchant_spend_row(merchant: str, total: float) -> MerchantSpendSummaryRow:
    return {"merchant": merchant, "total": total}


def _dow_row(day: str, total: float, count: int, average: float) -> DayOfWeekSpendRow:
    return {"day": day, "total": total, "count": count, "average": average}


def _monthly_row(month: str, total: float, trend: MonthlyTrendLiteral) -> MonthlyTrendRow:
    return {"month": month, "total": total, "trend": trend}


def _anomaly_row(
    *,
    d_val: date,
    merchant: str,
    amount: float,
    category: str,
    category_average: float,
    multiple: float,
) -> SpendingAnomalyRow:
    return {
        "date": d_val,
        "merchant": merchant,
        "amount": amount,
        "category": category,
        "category_average": category_average,
        "multiple": multiple,
    }


def count_by_merchant(records: Sequence[CategorizedRecord]) -> list[MerchantFrequencySummaryRow]:
    """Top merchants by transaction count without using collections.Counter."""
    counts: dict[str, int] = {}
    for record in records:
        merchant = str(record.get("merchant", "(unknown)"))
        counts[merchant] = counts.get(merchant, 0) + 1
    pairs = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [_merchant_freq_row(m, c) for m, c in pairs[:10]]


def spend_by_merchant(records: Sequence[CategorizedRecord]) -> list[MerchantSpendSummaryRow]:
    """Top merchants by total spend."""
    totals: dict[str, float] = {}
    for record in records:
        merchant = str(record.get("merchant", "(unknown)"))
        totals[merchant] = totals.get(merchant, 0.0) + float(record.get("amount", 0.0))
    pairs = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    return [_merchant_spend_row(m, float(t)) for m, t in pairs[:10]]


def day_of_week_breakdown(records: Sequence[CategorizedRecord]) -> list[DayOfWeekSpendRow]:
    """Calculate total and average spend per weekday."""
    buckets: dict[str, dict[str, float | int | str]] = {}
    for day_name in DAY_NAMES:
        buckets[day_name] = {"day": day_name, "total": 0.0, "count": 0, "average": 0.0}

    for record in records:
        d = _record_date(record)
        day_name = DAY_NAMES[d.weekday()]
        amt = float(record.get("amount", 0.0))
        b = buckets[day_name]
        b["total"] = float(b["total"]) + amt
        b["count"] = int(b["count"]) + 1

    rows: list[DayOfWeekSpendRow] = []
    for day_name in DAY_NAMES:
        b = buckets[day_name]
        count = int(b["count"])
        total = float(b["total"])
        average = (total / count) if count else 0.0
        rows.append(_dow_row(str(b["day"]), total, count, average))
    return rows


def weekend_vs_weekday(records: Sequence[CategorizedRecord]) -> WeekendWeekdaySummary:
    """Compare weekend and weekday spend totals and averages."""
    weekend = weekday = 0.0
    weekend_count = weekday_count = 0
    for record in records:
        d = _record_date(record)
        amt = float(record.get("amount", 0.0))
        if d.weekday() >= 5:
            weekend += amt
            weekend_count += 1
        else:
            weekday += amt
            weekday_count += 1

    weekend_avg = weekend / weekend_count if weekend_count else 0.0
    weekday_avg = weekday / weekday_count if weekday_count else 0.0

    if weekday_avg == 0 and weekend_avg == 0:
        percentage_difference = 0.0
    elif weekday_avg == 0:
        percentage_difference = 100.0
    else:
        percentage_difference = ((weekend_avg - weekday_avg) / weekday_avg) * 100

    return {
        "weekend_total": weekend,
        "weekday_total": weekday,
        "weekend_avg": weekend_avg,
        "weekday_avg": weekday_avg,
        "percentage_difference": percentage_difference,
    }


def time_of_month_analysis(
    records: Sequence[CategorizedRecord], payday_date: int = 15
) -> TimeOfMonthSplit:
    """Split spending into pre-payday and post-payday windows."""
    pre_total = post_total = 0.0
    pre_count = post_count = 0
    for record in records:
        d = _record_date(record)
        amt = float(record.get("amount", 0.0))
        if d.day < payday_date:
            pre_total += amt
            pre_count += 1
        else:
            post_total += amt
            post_count += 1

    return {
        "pre_payday_total": pre_total,
        "pre_payday_count": pre_count,
        "post_payday_total": post_total,
        "post_payday_count": post_count,
    }


def monthly_trends(records: Sequence[CategorizedRecord]) -> list[MonthlyTrendRow]:
    """Calculate total spend per month and whether it rose or fell."""
    totals: dict[str, float] = {}
    for record in records:
        d = _record_date(record)
        key = d.strftime("%Y-%m")
        totals[key] = totals.get(key, 0.0) + float(record.get("amount", 0.0))

    rows: list[MonthlyTrendRow] = [
        _monthly_row(month, float(total), "flat") for month, total in totals.items()
    ]
    rows.sort(key=lambda item: str(item["month"]))

    previous_total: float | None = None
    for row in rows:
        total = float(row["total"])
        if previous_total is None:
            trend: MonthlyTrendLiteral = "starting point"
        elif total > previous_total:
            trend = "up"
        elif total < previous_total:
            trend = "down"
        else:
            trend = "flat"
        row["trend"] = trend
        previous_total = total
    return rows


def group_category_averages(records: Sequence[CategorizedRecord]) -> dict[str, dict[str, float | int]]:
    """Build category totals and counts before anomaly detection."""
    groups: dict[str, dict[str, float | int]] = {}
    for record in records:
        category = str(record.get("category", "Unknown"))
        if category not in groups:
            groups[category] = {"total": 0.0, "count": 0}
        groups[category]["total"] += float(record.get("amount", 0.0))
        groups[category]["count"] += 1
    for _category, data in groups.items():
        data["average"] = data["total"] / data["count"] if data["count"] else 0.0
    return groups


def detect_anomalies(records: Sequence[CategorizedRecord]) -> AnomalyReport:
    """Flag anything above 3x the category average."""
    category_info = group_category_averages(records)
    anomalies: list[SpendingAnomalyRow] = []
    affected_categories: set[str] = set()

    for record in records:
        category = str(record.get("category", "Unknown"))
        average = float(category_info[category]["average"])
        amt = float(record.get("amount", 0.0))
        if average > 0 and amt > average * 3:
            multiple = amt / average
            d_val = _record_date(record)
            anomalies.append(
                _anomaly_row(
                    d_val=d_val,
                    merchant=str(record.get("merchant", "")),
                    amount=amt,
                    category=category,
                    category_average=average,
                    multiple=multiple,
                )
            )
            affected_categories.add(category)

    anomaly_counts: dict[str, int] = {c: 0 for c in affected_categories}
    for anomaly in anomalies:
        anomaly_counts[anomaly["category"]] = anomaly_counts.get(anomaly["category"], 0) + 1

    anomalies.sort(key=lambda item: (-item["multiple"], -item["amount"]))
    return {
        "anomalies": anomalies,
        "counts": anomaly_counts,
        "affected_categories": affected_categories,
    }


def run_all_reports(
    records: Sequence[Mapping[str, Any]],
    payday_date: int = 15,
) -> AnalysisReport:
    """Bundle the core analysis into one dictionary."""
    rows = coerce_analysis_records(records)
    report: AnalysisReport = {
        "record_count": len(rows),
        "top_by_frequency": count_by_merchant(rows),
        "top_by_spend": spend_by_merchant(rows),
        "day_of_week": day_of_week_breakdown(rows),
        "weekend_vs_weekday": weekend_vs_weekday(rows),
        "time_of_month": time_of_month_analysis(rows, payday_date=payday_date),
        "monthly_trends": monthly_trends(rows),
        "anomaly_report": detect_anomalies(rows),
    }
    return report
