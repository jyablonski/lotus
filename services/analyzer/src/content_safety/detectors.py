from __future__ import annotations

from abc import ABC, abstractmethod
import re

from src.content_safety.schemas import (
    ContentFlagDetection,
    ContentSafetyDetectionResult,
    FlagType,
)

_PROFANITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("damn", re.compile(r"\bdamn(?:ed|ing)?\b", re.IGNORECASE)),
    ("hell", re.compile(r"\bhell\b", re.IGNORECASE)),
    ("shit", re.compile(r"\bshit(?:ty|ting)?\b", re.IGNORECASE)),
    ("fuck", re.compile(r"\bfuck(?:ing|ed)?\b", re.IGNORECASE)),
    ("bitch", re.compile(r"\bbitch(?:y|es)?\b", re.IGNORECASE)),
    ("asshole", re.compile(r"\basshole(?:s)?\b", re.IGNORECASE)),
)

_CRISIS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("self-harm", re.compile(r"\bself[- ]harm\b", re.IGNORECASE)),
    ("kill myself", re.compile(r"\bkill myself\b", re.IGNORECASE)),
    ("end my life", re.compile(r"\bend my life\b", re.IGNORECASE)),
    ("suicide", re.compile(r"\bsuicid(?:e|al)\b", re.IGNORECASE)),
    ("hurt myself", re.compile(r"\bhurt myself\b", re.IGNORECASE)),
    ("abuse", re.compile(r"\babus(?:e|ed|ive)\b", re.IGNORECASE)),
    ("unsafe at home", re.compile(r"\bunsafe at home\b", re.IGNORECASE)),
    ("want to disappear", re.compile(r"\bwant to disappear\b", re.IGNORECASE)),
)


class ContentSafetyDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> ContentSafetyDetectionResult:
        """Detect sensitive or inappropriate content from free text."""


class RegexContentSafetyDetector(ContentSafetyDetector):
    def detect(self, text: str) -> ContentSafetyDetectionResult:
        normalized_text = text.strip()
        if not normalized_text:
            return ContentSafetyDetectionResult(flags=[])

        detections = []
        for flag_type, patterns in (
            ("profanity", _PROFANITY_PATTERNS),
            ("crisis", _CRISIS_PATTERNS),
        ):
            matches = self._find_matches(normalized_text, patterns)
            if not matches:
                continue

            detections.append(
                ContentFlagDetection(
                    flag_type=flag_type,
                    severity=self._severity_for(flag_type, matches),
                    matched_terms=matches,
                )
            )

        return ContentSafetyDetectionResult(flags=detections)

    @staticmethod
    def _find_matches(text: str, patterns: tuple[tuple[str, re.Pattern[str]], ...]) -> list[str]:
        matches = [label for label, pattern in patterns if pattern.search(text)]
        return sorted(set(matches))

    @staticmethod
    def _severity_for(flag_type: FlagType, matches: list[str]) -> str:
        if flag_type == "crisis":
            if any(
                term in {"kill myself", "end my life", "suicide", "self-harm"} for term in matches
            ):
                return "high"
            return "medium"

        if len(matches) >= 3 or any(term in {"fuck", "asshole"} for term in matches):
            return "medium"
        return "low"
