"""
Compliance Checker - Platform-specific validation
Ensures creatives meet Meta, Google, TikTok requirements
"""
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComplianceRule:
    """Single compliance rule"""
    rule_id: str
    platform: str
    severity: str  # 'error', 'warning', 'info'
    check_type: str  # 'text', 'duration', 'ratio', 'content'
    message: str


class ComplianceChecker:
    """Production-ready compliance validation"""
    
    # Platform-specific rules
    RULES = [
        # Meta/Facebook Rules
        ComplianceRule(
            "meta_text_limit",
            "meta",
            "error",
            "text",
            "Text overlay cannot exceed 20% of frame"
        ),
        ComplianceRule(
            "meta_prohibited_words",
            "meta",
            "error",
            "text",
            "Contains prohibited words (guarantee, miracle, etc.)"
        ),
        ComplianceRule(
            "meta_duration_reels",
            "meta",
            "error",
            "duration",
            "Reels must be 15-90 seconds"
        ),
        ComplianceRule(
            "meta_ratio_reels",
            "error",
            "ratio",
            "meta",
            "Reels must be 9:16 aspect ratio"
        ),
        ComplianceRule(
            "meta_before_after",
            "meta",
            "warning",
            "content",
            "Before/after claims require disclaimers"
        ),
        
        # Google Ads Rules
        ComplianceRule(
            "google_text_length",
            "google",
            "error",
            "text",
            "Headlines must be 30 characters max"
        ),
        ComplianceRule(
            "google_duration_shorts",
            "google",
            "error",
            "duration",
            "YouTube Shorts must be under 60 seconds"
        ),
        ComplianceRule(
            "google_prohibited_words",
            "google",
            "error",
            "text",
            "Contains prohibited words (click here, free, etc.)"
        ),
        
        # Universal Rules
        ComplianceRule(
            "universal_audio_required",
            "all",
            "warning",
            "content",
            "Videos with audio perform 40% better"
        ),
        ComplianceRule(
            "universal_hook_3sec",
            "all",
            "warning",
            "duration",
            "Hook should capture attention in first 3 seconds"
        )
    ]
    
    # Prohibited words by platform
    PROHIBITED_WORDS = {
        "meta": [
            "guarantee", "guaranteed", "miracle", "cure", "100%",
            "risk-free", "no risk", "limited time only", "act now",
            "click here", "free money", "get rich quick"
        ],
        "google": [
            "click here", "click now", "free", "buy now",
            "100% guaranteed", "miracle", "cure-all"
        ]
    }
    
    def __init__(self):
        """Initialize compliance checker"""
        self.rules = self.RULES
        self.prohibited_words = self.PROHIBITED_WORDS
    
    def check_compliance(
        self,
        creative: Dict[str, Any],
        platform: str = "meta",
        variant: str = "reels"
    ) -> Dict[str, Any]:
        """
        Check creative compliance against platform rules
        
        Args:
            creative: Creative data (hook, script, duration, ratio)
            platform: Target platform (meta, google, tiktok)
            variant: Ad format (reels, feed, stories, shorts)
        
        Returns:
            Compliance report with errors, warnings, and overall status
        """
        errors = []
        warnings = []
        info = []
        
        # Get applicable rules
        applicable_rules = [
            rule for rule in self.rules
            if rule.platform in [platform, "all"]
        ]
        
        # Run checks
        for rule in applicable_rules:
            violation = self._check_rule(creative, rule, variant)
            if violation:
                if rule.severity == "error":
                    errors.append(violation)
                elif rule.severity == "warning":
                    warnings.append(violation)
                else:
                    info.append(violation)
        
        # Determine overall status
        status = "pass"
        if errors:
            status = "fail"
        elif warnings:
            status = "review"
        
        report = {
            "status": status,
            "platform": platform,
            "variant": variant,
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "compliant": len(errors) == 0,
            "needs_review": len(warnings) > 0
        }
        
        logger.info(f"Compliance check: {status} ({len(errors)} errors, {len(warnings)} warnings)")
        
        return report
    
    def _check_rule(
        self,
        creative: Dict[str, Any],
        rule: ComplianceRule,
        variant: str
    ) -> Optional[Dict[str, str]]:
        """Check a single compliance rule"""
        
        if rule.check_type == "text":
            return self._check_text(creative, rule)
        elif rule.check_type == "duration":
            return self._check_duration(creative, rule, variant)
        elif rule.check_type == "ratio":
            return self._check_ratio(creative, rule, variant)
        elif rule.check_type == "content":
            return self._check_content(creative, rule)
        
        return None
    
    def _check_text(
        self,
        creative: Dict[str, Any],
        rule: ComplianceRule
    ) -> Optional[Dict[str, str]]:
        """Check text-related rules"""
        
        # Combine all text
        text_parts = [
            creative.get("hook", ""),
            creative.get("cta", ""),
            str(creative.get("script", ""))
        ]
        full_text = " ".join(text_parts).lower()
        
        # Check prohibited words
        if "prohibited" in rule.rule_id:
            prohibited = self.prohibited_words.get(rule.platform, [])
            for word in prohibited:
                if word.lower() in full_text:
                    return {
                        "rule_id": rule.rule_id,
                        "message": f"{rule.message}: Found '{word}'",
                        "severity": rule.severity
                    }
        
        # Check text length (for headlines)
        if "text_length" in rule.rule_id:
            hook = creative.get("hook", "")
            if len(hook) > 30:
                return {
                    "rule_id": rule.rule_id,
                    "message": f"{rule.message}: Current length {len(hook)}",
                    "severity": rule.severity
                }
        
        return None
    
    def _check_duration(
        self,
        creative: Dict[str, Any],
        rule: ComplianceRule,
        variant: str
    ) -> Optional[Dict[str, str]]:
        """Check duration rules"""
        
        duration = creative.get("duration_seconds", 30)
        
        # Meta Reels: 15-90 seconds
        if rule.rule_id == "meta_duration_reels" and variant == "reels":
            if duration < 15 or duration > 90:
                return {
                    "rule_id": rule.rule_id,
                    "message": f"{rule.message}: Current {duration}s",
                    "severity": rule.severity
                }
        
        # Google Shorts: under 60 seconds
        if rule.rule_id == "google_duration_shorts" and variant == "shorts":
            if duration > 60:
                return {
                    "rule_id": rule.rule_id,
                    "message": f"{rule.message}: Current {duration}s",
                    "severity": rule.severity
                }
        
        return None
    
    def _check_ratio(
        self,
        creative: Dict[str, Any],
        rule: ComplianceRule,
        variant: str
    ) -> Optional[Dict[str, str]]:
        """Check aspect ratio rules"""
        
        resolution = creative.get("resolution", "1080x1920")
        
        # Meta Reels: must be 9:16
        if rule.rule_id == "meta_ratio_reels" and variant == "reels":
            if resolution != "1080x1920":
                return {
                    "rule_id": rule.rule_id,
                    "message": f"{rule.message}: Current {resolution}",
                    "severity": rule.severity
                }
        
        return None
    
    def _check_content(
        self,
        creative: Dict[str, Any],
        rule: ComplianceRule
    ) -> Optional[Dict[str, str]]:
        """Check content-related rules"""
        
        # Check for before/after claims
        if rule.rule_id == "meta_before_after":
            text = " ".join([
                creative.get("hook", ""),
                str(creative.get("script", ""))
            ]).lower()
            
            before_after_terms = ["before", "after", "transformation", "results"]
            if any(term in text for term in before_after_terms):
                return {
                    "rule_id": rule.rule_id,
                    "message": rule.message,
                    "severity": rule.severity
                }
        
        return None
    
    def get_platform_requirements(self, platform: str) -> Dict[str, Any]:
        """Get all requirements for a platform"""
        
        platform_rules = [
            rule for rule in self.rules
            if rule.platform in [platform, "all"]
        ]
        
        requirements = {
            "platform": platform,
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "severity": rule.severity,
                    "message": rule.message
                }
                for rule in platform_rules
            ],
            "prohibited_words": self.prohibited_words.get(platform, [])
        }
        
        return requirements


# Global instance
compliance_checker = ComplianceChecker()
