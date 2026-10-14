"""
Prometheus metrics definitions shared across services.

Centralizes metric definitions to ensure consistency.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge

# --- Risk Engine Metrics ---
RISK_SCORE_HISTOGRAM = Histogram(
    "ztna_risk_score",
    "Distribution of computed risk scores",
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
)

RISK_EVALUATION_LATENCY = Histogram(
    "ztna_risk_evaluation_latency_seconds",
    "Time to compute a risk score",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

RISK_LEVEL_COUNTER = Counter(
    "ztna_risk_level_total",
    "Count of risk evaluations by level",
    ["level"],
)

# --- MFA Metrics ---
MFA_VERIFICATION_LATENCY = Histogram(
    "ztna_mfa_verification_latency_seconds",
    "MFA verification response time",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

MFA_VERIFICATION_COUNTER = Counter(
    "ztna_mfa_verification_total",
    "Count of MFA verification attempts",
    ["method", "result"],
)

# --- ZTNA Policy Metrics ---
POLICY_DECISION_LATENCY = Histogram(
    "ztna_policy_decision_latency_seconds",
    "ZTNA policy decision latency",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
)

POLICY_DECISION_COUNTER = Counter(
    "ztna_policy_decision_total",
    "Count of policy decisions",
    ["decision"],
)

# --- PEP Metrics ---
PEP_REQUEST_COUNTER = Counter(
    "ztna_pep_request_total",
    "Total requests processed by PEP",
    ["method", "status"],
)

PEP_REQUEST_LATENCY = Histogram(
    "ztna_pep_request_latency_seconds",
    "End-to-end request latency through PEP",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

# --- Adaptation Metrics ---
ADAPTATION_TIME = Histogram(
    "ztna_adaptation_time_seconds",
    "Time between risk score change and new policy enforcement",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# --- System Metrics ---
ACTIVE_SESSIONS = Gauge(
    "ztna_active_sessions",
    "Number of active sessions",
)
