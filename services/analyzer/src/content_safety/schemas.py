from dataclasses import dataclass
from typing import Literal

FlagType = Literal["profanity", "crisis"]
Severity = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class ContentFlagDetection:
    flag_type: FlagType
    severity: Severity
    matched_terms: list[str]


@dataclass(frozen=True)
class ContentSafetyDetectionResult:
    flags: list[ContentFlagDetection]


@dataclass(frozen=True)
class ContentFlagAnalysis:
    flag_type: FlagType
    severity: Severity
    matched_terms: list[str]
    analysis_summary: str
