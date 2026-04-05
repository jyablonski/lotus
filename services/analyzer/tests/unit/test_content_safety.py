from src.content_safety import RegexContentSafetyDetector, RuleBasedContentFlagAnalyzer
from src.content_safety.schemas import ContentFlagDetection


def test_regex_detector_returns_profanity_and_crisis_flags():
    detector = RegexContentSafetyDetector()

    result = detector.detect(
        "This meeting was shit and I keep thinking about suicide and self-harm."
    )

    assert len(result.flags) == 2
    flags_by_type = {flag.flag_type: flag for flag in result.flags}
    assert flags_by_type["profanity"].severity == "low"
    assert flags_by_type["profanity"].matched_terms == ["shit"]
    assert flags_by_type["crisis"].severity == "high"
    assert flags_by_type["crisis"].matched_terms == ["self-harm", "suicide"]


def test_rule_based_analyzer_builds_summary():
    analyzer = RuleBasedContentFlagAnalyzer()

    result = analyzer.analyze(
        ContentFlagDetection(
            flag_type="crisis",
            severity="medium",
            matched_terms=["abuse", "unsafe at home"],
        )
    )

    assert result.flag_type == "crisis"
    assert result.severity == "medium"
    assert "abuse" in result.analysis_summary


def test_regex_detector_returns_no_flags_for_blank_text():
    detector = RegexContentSafetyDetector()

    result = detector.detect("   ")

    assert result.flags == []


def test_regex_detector_sets_medium_profanity_severity_for_stronger_matches():
    detector = RegexContentSafetyDetector()

    result = detector.detect("Fuck this, damn this, you asshole.")

    assert len(result.flags) == 1
    assert result.flags[0].flag_type == "profanity"
    assert result.flags[0].severity == "medium"


def test_rule_based_analyzer_promotes_profanity_to_medium_for_multiple_matches():
    analyzer = RuleBasedContentFlagAnalyzer()

    result = analyzer.analyze(
        ContentFlagDetection(
            flag_type="profanity",
            severity="low",
            matched_terms=["damn", "hell", "shit"],
        )
    )

    assert result.flag_type == "profanity"
    assert result.severity == "medium"
    assert "damn, hell, shit" in result.analysis_summary
