"""
Alert Rules Configuration
Defines configurable alert rules for performance monitoring
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Types of alerts that can be triggered"""
    ROAS_DROP = "roas_drop"
    BUDGET_WARNING = "budget_warning"
    BUDGET_DEPLETED = "budget_depleted"
    AD_DISAPPROVED = "ad_disapproved"
    CTR_ANOMALY = "ctr_anomaly"
    CONVERSION_SPIKE = "conversion_spike"
    PREDICTION_MISS = "prediction_miss"
    CAMPAIGN_PAUSED = "campaign_paused"
    HIGH_CPA = "high_cpa"
    LOW_IMPRESSIONS = "low_impressions"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"  # Immediate action required (budget depleted, ad disapproved)
    HIGH = "high"          # Action needed soon (ROAS drop, high CPA)
    MEDIUM = "medium"      # Monitor closely (CTR anomaly, budget warning)
    LOW = "low"            # Informational (conversion spike, prediction miss)
    INFO = "info"          # For tracking purposes


@dataclass
class AlertRule:
    """
    Configurable alert rule for performance monitoring

    Attributes:
        rule_id: Unique identifier for the rule
        name: Human-readable name
        alert_type: Type of alert (from AlertType enum)
        severity: Alert severity (from AlertSeverity enum)
        enabled: Whether the rule is active
        threshold: Numeric threshold for triggering alert
        threshold_operator: Comparison operator ('>', '<', '>=', '<=', '==', '!=')
        lookback_minutes: Time window to consider for metrics
        cooldown_minutes: Minimum time between alerts for same entity
        conditions: Additional conditions (dict of key-value pairs)
        metadata: Additional metadata for the rule
        created_at: Timestamp when rule was created
        updated_at: Timestamp when rule was last updated
    """
    rule_id: str
    name: str
    alert_type: AlertType
    severity: AlertSeverity
    enabled: bool = True
    threshold: float = 0.0
    threshold_operator: str = "<"  # >, <, >=, <=, ==, !=
    lookback_minutes: int = 60
    cooldown_minutes: int = 30
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def evaluate(self, value: float, context: Dict[str, Any] = None) -> bool:
        """
        Evaluate if alert should be triggered based on value and threshold

        Args:
            value: Current metric value
            context: Additional context for evaluation

        Returns:
            True if alert should be triggered
        """
        if not self.enabled:
            return False

        # Check additional conditions if provided
        if context and self.conditions:
            for key, expected_value in self.conditions.items():
                if key not in context or context[key] != expected_value:
                    return False

        # Evaluate threshold
        operators = {
            '>': lambda v, t: v > t,
            '<': lambda v, t: v < t,
            '>=': lambda v, t: v >= t,
            '<=': lambda v, t: v <= t,
            '==': lambda v, t: v == t,
            '!=': lambda v, t: v != t,
        }

        operator_func = operators.get(self.threshold_operator)
        if not operator_func:
            logger.error(f"Invalid threshold operator: {self.threshold_operator}")
            return False

        return operator_func(value, self.threshold)

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary"""
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['severity'] = self.severity.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertRule':
        """Create AlertRule from dictionary"""
        data['alert_type'] = AlertType(data['alert_type'])
        data['severity'] = AlertSeverity(data['severity'])
        return cls(**data)


class AlertRuleManager:
    """
    Manages alert rules and provides default configurations
    """

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default alert rules for elite marketers"""

        default_rules = [
            # ROAS Drop - Critical for $20k/day spenders
            AlertRule(
                rule_id="roas_drop_critical",
                name="ROAS Drop Below 2.0x",
                alert_type=AlertType.ROAS_DROP,
                severity=AlertSeverity.HIGH,
                threshold=2.0,
                threshold_operator="<",
                lookback_minutes=60,
                cooldown_minutes=30,
                metadata={
                    "description": "ROAS has dropped below 2.0x threshold",
                    "action": "Review campaign performance and consider pausing low performers"
                }
            ),

            # ROAS Drop - Warning
            AlertRule(
                rule_id="roas_drop_warning",
                name="ROAS Drop Below 3.0x",
                alert_type=AlertType.ROAS_DROP,
                severity=AlertSeverity.MEDIUM,
                threshold=3.0,
                threshold_operator="<",
                lookback_minutes=120,
                cooldown_minutes=60,
                metadata={
                    "description": "ROAS has dropped below 3.0x threshold",
                    "action": "Monitor campaign closely"
                }
            ),

            # Budget Warning - 80% threshold
            AlertRule(
                rule_id="budget_warning_80",
                name="80% Daily Budget Spent",
                alert_type=AlertType.BUDGET_WARNING,
                severity=AlertSeverity.MEDIUM,
                threshold=80.0,
                threshold_operator=">=",
                lookback_minutes=1440,  # 24 hours
                cooldown_minutes=360,   # 6 hours
                metadata={
                    "description": "Campaign has spent 80% of daily budget",
                    "action": "Review budget allocation and performance"
                }
            ),

            # Budget Depleted - Critical
            AlertRule(
                rule_id="budget_depleted",
                name="Daily Budget Depleted",
                alert_type=AlertType.BUDGET_DEPLETED,
                severity=AlertSeverity.CRITICAL,
                threshold=100.0,
                threshold_operator=">=",
                lookback_minutes=1440,
                cooldown_minutes=720,   # 12 hours
                metadata={
                    "description": "Campaign has exhausted daily budget",
                    "action": "Increase budget or wait for next day"
                }
            ),

            # Ad Disapproved - Critical
            AlertRule(
                rule_id="ad_disapproved",
                name="Ad Disapproved by Meta",
                alert_type=AlertType.AD_DISAPPROVED,
                severity=AlertSeverity.CRITICAL,
                threshold=1.0,
                threshold_operator=">=",
                lookback_minutes=10,
                cooldown_minutes=0,  # No cooldown for disapprovals
                metadata={
                    "description": "Meta has disapproved an ad",
                    "action": "Review ad content and resubmit"
                }
            ),

            # CTR Anomaly - Drop detection
            AlertRule(
                rule_id="ctr_anomaly_drop",
                name="CTR Drop >20% from Average",
                alert_type=AlertType.CTR_ANOMALY,
                severity=AlertSeverity.MEDIUM,
                threshold=20.0,
                threshold_operator=">=",
                lookback_minutes=60,
                cooldown_minutes=120,
                metadata={
                    "description": "CTR has dropped more than 20% from average",
                    "action": "Check creative fatigue and audience overlap"
                }
            ),

            # Conversion Spike - Fraud detection
            AlertRule(
                rule_id="conversion_spike",
                name="Conversion Spike >50% (Fraud Check)",
                alert_type=AlertType.CONVERSION_SPIKE,
                severity=AlertSeverity.LOW,
                threshold=50.0,
                threshold_operator=">=",
                lookback_minutes=60,
                cooldown_minutes=120,
                metadata={
                    "description": "Conversions have spiked >50% (potential fraud)",
                    "action": "Verify conversion quality and check for fraud"
                }
            ),

            # Prediction Miss - Model accuracy
            AlertRule(
                rule_id="prediction_miss_high",
                name="Prediction Error >30%",
                alert_type=AlertType.PREDICTION_MISS,
                severity=AlertSeverity.LOW,
                threshold=30.0,
                threshold_operator=">=",
                lookback_minutes=240,
                cooldown_minutes=360,
                metadata={
                    "description": "Prediction error exceeds 30%",
                    "action": "Review model accuracy and consider retraining"
                }
            ),

            # High CPA - Cost per acquisition alert
            AlertRule(
                rule_id="high_cpa",
                name="CPA Above $100",
                alert_type=AlertType.HIGH_CPA,
                severity=AlertSeverity.HIGH,
                threshold=100.0,
                threshold_operator=">",
                lookback_minutes=120,
                cooldown_minutes=60,
                metadata={
                    "description": "Cost per acquisition is above $100",
                    "action": "Optimize targeting and creative"
                }
            ),

            # Low Impressions - Delivery issue
            AlertRule(
                rule_id="low_impressions",
                name="Impressions Below 1000/hour",
                alert_type=AlertType.LOW_IMPRESSIONS,
                severity=AlertSeverity.MEDIUM,
                threshold=1000.0,
                threshold_operator="<",
                lookback_minutes=60,
                cooldown_minutes=120,
                metadata={
                    "description": "Campaign receiving fewer than 1000 impressions/hour",
                    "action": "Check budget, bid, and audience size"
                }
            ),
        ]

        for rule in default_rules:
            self.rules[rule.rule_id] = rule

    def add_rule(self, rule: AlertRule) -> None:
        """Add or update an alert rule"""
        rule.updated_at = datetime.utcnow().isoformat()
        self.rules[rule.rule_id] = rule
        logger.info(f"Added/updated alert rule: {rule.rule_id}")

    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get a specific alert rule"""
        return self.rules.get(rule_id)

    def get_rules_by_type(self, alert_type: AlertType) -> List[AlertRule]:
        """Get all rules of a specific type"""
        return [rule for rule in self.rules.values() if rule.alert_type == alert_type]

    def get_enabled_rules(self) -> List[AlertRule]:
        """Get all enabled rules"""
        return [rule for rule in self.rules.values() if rule.enabled]

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            self.rules[rule_id].updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            self.rules[rule_id].updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def get_all_rules(self) -> List[AlertRule]:
        """Get all alert rules"""
        return list(self.rules.values())

    def export_rules(self) -> List[Dict[str, Any]]:
        """Export all rules as dictionaries"""
        return [rule.to_dict() for rule in self.rules.values()]

    def import_rules(self, rules_data: List[Dict[str, Any]]) -> int:
        """Import rules from dictionaries"""
        count = 0
        for rule_data in rules_data:
            try:
                rule = AlertRule.from_dict(rule_data)
                self.add_rule(rule)
                count += 1
            except Exception as e:
                logger.error(f"Failed to import rule: {e}")
        return count


# Global instance
alert_rule_manager = AlertRuleManager()
