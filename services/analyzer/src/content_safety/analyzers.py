from __future__ import annotations

from abc import ABC, abstractmethod

from src.content_safety.schemas import ContentFlagAnalysis, ContentFlagDetection


class ContentFlagAnalyzer(ABC):
    @abstractmethod
    def analyze(self, detection: ContentFlagDetection) -> ContentFlagAnalysis:
        """Produce a persisted analysis record for a flag detection."""


class RuleBasedContentFlagAnalyzer(ContentFlagAnalyzer):
    def analyze(self, detection: ContentFlagDetection) -> ContentFlagAnalysis:
        severity = detection.severity
        if detection.flag_type == "crisis":
            severity = (
                "high"
                if any(
                    term in {"kill myself", "end my life", "suicide", "self-harm"}
                    for term in detection.matched_terms
                )
                else "medium"
            )
            summary = (
                "Detected crisis-oriented language that may indicate self-harm, suicidal ideation, "
                f"or abuse concerns. Matched terms: {', '.join(detection.matched_terms)}."
            )
        else:
            if len(detection.matched_terms) >= 3:
                severity = "medium"
            summary = (
                "Detected inappropriate or profane language in the journal entry. "
                f"Matched terms: {', '.join(detection.matched_terms)}."
            )

        return ContentFlagAnalysis(
            flag_type=detection.flag_type,
            severity=severity,
            matched_terms=detection.matched_terms,
            analysis_summary=summary,
        )
