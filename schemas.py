"""Typed public shapes for data flowing between app modules and the CLI.

Static-check contracts for :mod:`typing` / type checkers. Rows used in metrics are
also checked in :func:`records.normalize_analysis_record`.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal, TypedDict

from typing_extensions import NotRequired

# --- Shared string enums (CLI / storage values) ---

CompoundingLiteral = Literal["monthly", "annual"]
ContributionFrequencyLiteral = Literal["monthly", "annual"]
ContributionTimingLiteral = Literal["start", "end"]
BudgetComparisonStatusLiteral = Literal["OVER", "UNDER", "EVEN"]
BudgetTierLiteral = Literal["Needs", "Wants", "Savings"]
BudgetComparisonTierLiteral = Literal["Needs", "Wants", "Savings", "Unknown"]
MonthlyTrendLiteral = Literal["starting point", "up", "down", "flat"]


class CategoryRule(TypedDict):
    """Merchant rule target for the categorizer."""

    category: str
    subcategory: str


class RuleMatchResult(TypedDict):
    """Output of :func:`categorizer.find_best_rule_match`."""

    category: str
    subcategory: str
    confidence: float
    match_type: str
    rule_key: str


class CategorizedRecord(TypedDict):
    """Single transaction row after classification or when loaded for analysis.

    Core dimensions are always present after normalization; optional fields appear
    after classification or when shaping rows for specific consumers.
    """

    date: str | date
    merchant: str
    amount: float
    category: str
    subcategory: NotRequired[str]
    confidence: NotRequired[float]
    match_type: NotRequired[str]


class CategorySummaryRow(TypedDict):
    """One line from :func:`categorizer.summarize_categories`."""

    category: str
    total: float
    count: int


class ClassificationResult(TypedDict):
    """Return value of :func:`categorizer.run_classification`."""

    records: list[CategorizedRecord]
    flagged: list[CategorizedRecord]
    warnings: list[str]
    summary: list[CategorySummaryRow]
    rules: dict[str, CategoryRule]


class WeekendWeekdaySummary(TypedDict):
    weekend_total: float
    weekday_total: float
    weekend_avg: float
    weekday_avg: float
    percentage_difference: float


class TimeOfMonthSplit(TypedDict):
    pre_payday_total: float
    pre_payday_count: int
    post_payday_total: float
    post_payday_count: int


class SpendingAnomalyRow(TypedDict):
    """One flagged row from :func:`metrics.detect_anomalies`."""

    date: date
    merchant: str
    amount: float
    category: str
    category_average: float
    multiple: float


class AnomalyReport(TypedDict):
    anomalies: list[SpendingAnomalyRow]
    counts: dict[str, int]
    affected_categories: set[str]


class MerchantFrequencySummaryRow(TypedDict):
    """Shape of each row from :func:`metrics.count_by_merchant`."""

    merchant: str
    count: int


class MerchantSpendSummaryRow(TypedDict):
    """Shape of each row from :func:`metrics.spend_by_merchant`."""

    merchant: str
    total: float


class DayOfWeekSpendRow(TypedDict):
    """One weekday bucket from :func:`metrics.day_of_week_breakdown`."""

    day: str
    total: float
    count: int
    average: float


class MonthlyTrendRow(TypedDict):
    """One month line from :func:`metrics.monthly_trends`."""

    month: str
    total: float
    trend: MonthlyTrendLiteral


class AnalysisReport(TypedDict):
    """Return value of :func:`metrics.run_all_reports`."""

    record_count: int
    top_by_frequency: list[MerchantFrequencySummaryRow]
    top_by_spend: list[MerchantSpendSummaryRow]
    day_of_week: list[DayOfWeekSpendRow]
    weekend_vs_weekday: WeekendWeekdaySummary
    time_of_month: TimeOfMonthSplit
    monthly_trends: list[MonthlyTrendRow]
    anomaly_report: AnomalyReport


class GreedyTraceStep(TypedDict):
    denomination: int
    name: str
    before: int
    count: int
    after: int


class ParsedAmountToCents(TypedDict):
    """Parsed currency input expressed in cents and dollars."""

    input_text: str
    cents: int
    dollars: float
    rounded: bool


class ChangeResult(TypedDict):
    """Change-making breakdown from a cash-drawer style calculation.

    Parsing errors raise :class:`ValueError` before a result is returned; every
    successful return includes all keys below.
    """

    ok: bool
    cents: int
    amount: float
    rounded: bool
    breakdown: dict[int, int]
    trace: list[GreedyTraceStep]
    bill_count: int
    coin_count: int
    verification: float
    used_denominations: set[int]
    unused_denominations: set[int]
    message: str


class InvestmentScenario(TypedDict):
    """Inputs for compound-growth / investment scenario projection."""

    name: str
    initial_principal: float
    annual_rate: float
    years: int
    compounding: CompoundingLiteral
    contribution_amount: float
    contribution_frequency: ContributionFrequencyLiteral
    contribution_timing: ContributionTimingLiteral
    inflation_rate: float


class FinancialReportParams(TypedDict):
    """Inputs for building a text financial summary report."""

    payday: int
    income: float
    monthly: float
    rate: float
    years: int
    inflation: float
    output: str | None


class ProjectionYearRow(TypedDict):
    """One year of output from an investment projection."""

    year: int
    starting_balance: float
    contributions: float
    interest_earned: float
    ending_balance: float
    real_balance: float
    principal_portion: float
    interest_portion: float


class ProjectionResult(TypedDict):
    """Return value of an investment scenario projection."""

    scenario: InvestmentScenario
    rows: list[ProjectionYearRow]
    ending_balance: float
    total_contributed: float
    total_earned: float
    real_ending_balance: float
    purchasing_power_loss: float
    warning: str  # empty string when no high-rate warning


class BudgetCategoryProfile(TypedDict):
    """One category line inside :class:`BudgetAllocation` ``categories``."""

    tier: BudgetTierLiteral
    weight: int | float
    priority: int
    actual_spend: float
    budgeted_amount: float


class BudgetAllocation(TypedDict):
    """Return shape from budget ``allocate_*`` style functions."""

    strategy: str
    allocations: dict[str, float]
    categories: dict[str, BudgetCategoryProfile]
    allocated_total: float
    remaining: float
    warnings: list[str]


class BudgetComparisonRow(TypedDict):
    """One row from comparing actual spend to a budget."""

    category: str
    budgeted: float
    actual: float
    difference: float
    percentage_of_budget: float | None
    status: BudgetComparisonStatusLiteral
    tier: BudgetComparisonTierLiteral
    priority: int


class BudgetComparisonResult(TypedDict):
    """Return value of an actual-vs-budget comparison."""

    rows: list[BudgetComparisonRow]
    overages: set[str]
    under_budget: set[str]
    total_overage: float
    total_surplus: float
    total_actual: float
    total_budgeted: float


class ReconciliationRecord(TypedDict):
    """One normalized row from a reconciliation CSV (or mock data)."""

    date: date
    merchant: str
    merchant_key: str
    amount: float
    amount_cents: int
    source_label: str
    line_number: int


class ReconciliationPair(TypedDict):
    """A source row paired with a reference row and match metadata."""

    source: ReconciliationRecord
    reference: ReconciliationRecord
    confidence: float
    reason: str
    amount_delta: float
    date_gap: int


class ReconciliationSetSummary(TypedDict):
    """Counts of (date, merchant_key) keys across source vs reference."""

    shared_keys: int
    source_only_keys: int
    reference_only_keys: int
    symmetric_difference: int


class ReconciliationReport(TypedDict):
    """Return value of a reconciliation between two transaction sets."""

    matched: list[ReconciliationPair]
    amount_mismatch: list[ReconciliationPair]
    date_mismatch: list[ReconciliationPair]
    suspicious: list[ReconciliationPair]
    unmatched_source: list[ReconciliationRecord]
    unmatched_reference: list[ReconciliationRecord]
    set_summary: ReconciliationSetSummary
    source_total: float
    reference_total: float
    net_difference: float
    match_rate: float
    source_count: int
    reference_count: int


class DuplicateExactItem(TypedDict):
    """One exact-duplicate cluster inside a single file."""

    record: ReconciliationRecord
    count: int


class DuplicateNearItem(TypedDict):
    """Two rows with same merchant/amount and dates within the near window."""

    record: ReconciliationRecord
    next_record: ReconciliationRecord
    gap: int


class DuplicateDetectionResult(TypedDict):
    """Output of duplicate detection on reconciled transaction rows."""

    exact: list[DuplicateExactItem]
    near: list[DuplicateNearItem]


class RunReconciliationResult(TypedDict):
    """Return value of an end-to-end reconciliation run."""

    report: ReconciliationReport
    report_text: str
    warnings: list[str]
    duplicate_source: DuplicateDetectionResult
    duplicate_reference: DuplicateDetectionResult
    output_path: Path | None
