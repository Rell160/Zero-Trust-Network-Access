"""
Risk Scoring Engine implementation.

Calculates weighted risk scores from normalized context features,
classifies risk levels, and generates explainable output.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from src.common.config import RiskEngineConfig, RiskThresholds, RiskWeights
from src.common.logging import get_logger
from src.common.models import AccessContext, RiskLevel, RiskScore
from src.risk_engine.features import extract_all_features

logger = get_logger("risk_engine.engine")


class RiskScoringEngine:
    """Core risk scoring engine for ZTNA."""

    def __init__(
        self,
        thresholds: RiskThresholds | None = None,
        weights: RiskWeights | None = None,
    ) -> None:
        """Initialize the risk engine with thresholds and weights.

        Args:
            thresholds: Risk score threshold boundaries.
            weights: Feature weights for risk scoring.
        """
        self.thresholds = thresholds or RiskThresholds()
        self.weights = weights or RiskWeights()
        self._normalized_weights = self.weights.normalized()

    @classmethod
    def from_config(cls, config: RiskEngineConfig) -> RiskScoringEngine:
        """Construct engine instance from configuration model.

        Args:
            config: RiskEngineConfig loaded from YAML/Env.

        Returns:
            Configured RiskScoringEngine.
        """
        return cls(thresholds=config.thresholds, weights=config.weights)

    def classify_level(self, score: float) -> RiskLevel:
        """Classify a numerical score (0-100) into a RiskLevel.

        Thresholds mapping:
          [0.0, low]          -> RiskLevel.LOW
          (low, medium]       -> RiskLevel.MEDIUM
          (medium, high]      -> RiskLevel.HIGH
          (high, 100.0]       -> RiskLevel.CRITICAL

        Args:
            score: Clamped risk score in [0.0, 100.0].

        Returns:
            RiskLevel enum.
        """
        if score <= self.thresholds.low:
            return RiskLevel.LOW
        elif score <= self.thresholds.medium:
            return RiskLevel.MEDIUM
        elif score <= self.thresholds.high:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def calculate_contributions(
        self, features: dict[str, float]
    ) -> tuple[float, dict[str, float]]:
        """Calculate weighted score and individual feature point contributions.

        Formula:
          raw_score = sum(weight_i * feature_i) * 100
          contribution_i = (weight_i * feature_i) * 100

        Args:
            features: Dictionary of normalized features in [0.0, 1.0].

        Returns:
            Tuple of (clamped_score, feature_contributions_dict).
        """
        raw_score = 0.0
        contributions: dict[str, float] = {}

        for feat_name, feat_val in features.items():
            weight = self._normalized_weights.get(feat_name, 0.0)
            pts = weight * feat_val * 100.0
            contributions[feat_name] = round(pts, 2)
            raw_score += pts

        clamped_score = max(0.0, min(100.0, round(raw_score, 2)))
        return clamped_score, contributions

    def generate_explanation(
        self,
        level: RiskLevel,
        score: float,
        contributions: dict[str, float],
    ) -> str:
        """Generate human-readable explanation of risk contributors.

        Args:
            level: The classified risk level.
            score: The overall computed score.
            contributions: Points contributed by each feature.

        Returns:
            Descriptive string explaining top risk drivers.
        """
        # Sort contributors descending by point contribution
        sorted_contribs = sorted(
            contributions.items(), key=lambda x: x[1], reverse=True
        )

        # Filter features that contributed more than 0 points
        active_drivers = [
            f"{name} (+{pts} pts)" for name, pts in sorted_contribs if pts > 0.0
        ]

        if not active_drivers:
            return f"Calculated score {score:.1f} ({level.value.upper()} risk). All context features within normal parameters."

        top_drivers_str = ", ".join(active_drivers[:3])
        return (
            f"Calculated score {score:.1f} ({level.value.upper()} risk). "
            f"Primary risk drivers: {top_drivers_str}."
        )

    def evaluate(self, context: AccessContext) -> RiskScore:
        """Evaluate an access context and produce a complete RiskScore.

        Args:
            context: Incoming access request context.

        Returns:
            RiskScore object with score, level, contributions, and explanation.
        """
        start_time = time.perf_counter()

        features = extract_all_features(context)
        score, contributions = self.calculate_contributions(features)
        level = self.classify_level(score)
        explanation = self.generate_explanation(level, score, contributions)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            "Risk evaluated",
            extra={
                "extra_data": {
                    "user_id": context.user_id,
                    "score": score,
                    "level": level.value,
                    "elapsed_ms": round(elapsed_ms, 3),
                }
            },
        )

        return RiskScore(
            score=score,
            level=level,
            feature_contributions=contributions,
            explanation=explanation,
            timestamp=datetime.now(timezone.utc),
        )
