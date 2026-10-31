from pathlib import Path

from scripts import verify_submission
from scripts.verify_submission import mp4_duration_seconds, pptx_text_and_slide_count


ROOT = Path(__file__).resolve().parents[1]


def test_committed_video_is_under_three_minutes():
    duration = mp4_duration_seconds(ROOT / "submission/opsintel-ai-demo.mp4")

    assert 0 < duration < 180


def test_pitch_deck_is_readable_and_has_expected_slide_count():
    text, slide_count = pptx_text_and_slide_count(
        ROOT / "submission/opsintel-ai-pitch-deck.pptx"
    )

    assert slide_count == 11
    assert "EVIDENCE-FIRST PIPELINE INVESTIGATION" in text.upper()
    assert "VERIFIED MEMORY REQUIRES A SEPARATE REVIEWER" in text.upper()


def test_current_test_count_must_appear_in_deck_and_demo_script(monkeypatch):
    monkeypatch.setattr(verify_submission, "_current_test_count", lambda: 100)
    result = verify_submission.verify(allow_dirty=True)
    assert "Current automated-test result is missing from the deck" in result["failures"]
    assert "Current automated-test result is missing from the demo script" in result["failures"]
