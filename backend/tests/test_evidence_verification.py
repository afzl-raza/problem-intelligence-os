import pytest

from app.models.evidence import ConfidenceLevel
from app.models.source import Source
from app.services.evidence import verification_status


def source(is_verified: bool) -> Source:
    return Source(name="s", is_verified=is_verified)


@pytest.mark.parametrize(
    "confidence,src,expected",
    [
        (ConfidenceLevel.HIGH, None, "unverified"),  # no cataloged source
        (ConfidenceLevel.HIGH, source(False), "unverified"),  # source not verified
        (ConfidenceLevel.UNVERIFIED, source(True), "unverified"),  # confidence says unverified
        (ConfidenceLevel.UNVERIFIED, None, "unverified"),
        (ConfidenceLevel.HIGH, source(True), "verified"),
        (ConfidenceLevel.MEDIUM, source(True), "verified"),
        (ConfidenceLevel.LOW, source(True), "verified"),
    ],
)
def test_verification_status_rule(confidence, src, expected):
    assert verification_status(confidence, src) == expected
