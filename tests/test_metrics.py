"""Tests for public functions in :mod:`metrics`."""

from __future__ import annotations

from datetime import date

from metrics import (
    count_by_merchant,
    day_of_week_breakdown,
    detect_anomalies,
    group_category_averages,
    monthly_trends,
    run_all_reports,
    spend_by_merchant,
    time_of_month_analysis,
    weekend_vs_weekday,
)

_FIXTURE = [
    {
        "date": date(2024, 1, 1),
        "merchant": "A",
        "amount": 10.0,
        "category": "Cat",
        "subcategory": "Cat",
    },
    {
        "date": date(2024, 1, 2),
        "merchant": "A",
        "amount": 20.0,
        "category": "Cat",
        "subcategory": "Cat",
    },
    {
        "date": date(2024, 1, 8),
        "merchant": "B",
        "amount": 5.0,
        "category": "Cat",
        "subcategory": "Cat",
    },
]


def test_count_and_spend_by_merchant() -> None:
    freq = count_by_merchant(_FIXTURE)
    assert freq[0]["merchant"] == "A"
    assert freq[0]["count"] == 2
    spend = spend_by_merchant(_FIXTURE)
    assert spend[0]["merchant"] == "A"
    assert spend[0]["total"] == 30.0


def test_day_of_week_and_weekend() -> None:
    dow = day_of_week_breakdown(_FIXTURE)
    assert len(dow) == 7
    ww = weekend_vs_weekday(_FIXTURE)
    assert "weekend_total" in ww
    assert "percentage_difference" in ww


def test_time_of_month_and_monthly_trends() -> None:
    tom = time_of_month_analysis(_FIXTURE, payday_date=5)
    assert tom["pre_payday_count"] + tom["post_payday_count"] == len(_FIXTURE)
    trends = monthly_trends(_FIXTURE)
    assert len(trends) >= 1
    assert trends[0]["trend"] == "starting point"


def test_group_category_averages() -> None:
    g = group_category_averages(_FIXTURE)
    assert "Cat" in g
    assert g["Cat"]["count"] == 3


def test_run_all_reports_bundle() -> None:
    rep = run_all_reports(_FIXTURE, payday_date=10)
    assert rep["record_count"] == 3
    assert rep["top_by_frequency"]
    assert rep["anomaly_report"]["counts"] is not None


def test_metrics_accepts_string_dates_like_coerced_csv() -> None:
    rows = [
        {
            "date": "2024-01-01",
            "merchant": "A",
            "amount": 1.0,
            "category": "C",
            "subcategory": "C",
        }
    ]
    dow = day_of_week_breakdown(rows)
    assert any(r["day"] == "Monday" for r in dow)


def test_detect_anomalies_empty_when_low() -> None:
    low = [
        {
            "date": date(2024, 1, 1),
            "merchant": "x",
            "amount": 1.0,
            "category": "Z",
            "subcategory": "Z",
        }
    ]
    rep = detect_anomalies(low)
    assert rep["anomalies"] == []
