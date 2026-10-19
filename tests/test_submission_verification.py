from pathlib import Path

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
    assert "FOLLOW THE EVIDENCE" in text.upper()
