"""Golden-utterance end-to-end coverage for ovos-skill-news (en-US).

``news`` and ``global_news`` are Padatious ``.intent`` handlers on an
``OVOSCommonPlaybackSkill`` (OCP-flavored playback intents, not classic
Adapt intents). Each handler ends by calling ``self.play_media`` to hand the
matched stream off to the audio pipeline, which is out of scope for intent
routing coverage and would otherwise reach out to real news feeds/URLs, so
``play_media`` is mocked for the duration of the suite and only intent
routing (the ``ovos.intent.matched`` bus message and its ``intent_name``)
is asserted.

Rows were probe-verified against a live MiniCroft loading this skill before
being committed here; wording that the actual Padatious templates rejected
was discarded in favor of phrasings that matched.

Run:
    uv run pytest test/end2end/ -v
"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

SKILL_ID = "ovos-skill-news.openvoiceos"
LANG = "en-US"

_PIPELINE = [
    "ovos-adapt-pipeline-plugin-high",
    "ovos-padatious-pipeline-plugin-high",
    "ovos-padacioso-pipeline-plugin-high",
    "ovos-adapt-pipeline-plugin-medium",
    "ovos-padacioso-pipeline-plugin-medium",
    "ovos-adapt-pipeline-plugin-low",
]

GOLDEN_PATH = Path(__file__).parent / "golden_utterances.jsonl"

NEGATIVE_UTTERANCES = [
    ("what's the weather", "ovos-skill-weather.openvoiceos"),
    ("play some music", "ovos-skill-music.openvoiceos"),
    ("what time is it", "ovos-skill-date-time.openvoiceos"),
    ("tell me a joke", "skill-icanhazdadjokes.openvoiceos"),
]


def _load_golden_rows():
    rows = []
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("needs_manual"):
                continue
            rows.append(row)
    return rows


GOLDEN_ROWS = [pytest.param(r, id=r["utterance"]) for r in _load_golden_rows()]


def _fake_play_media(*args, **kwargs):
    """Stand-in for OVOSCommonPlaybackSkill.play_media, used to keep this
    suite focused on intent routing instead of real audio playback."""
    return None


@pytest.fixture(scope="module")
def minicroft():
    with patch(
        "ovos_workshop.skills.common_play.OVOSCommonPlaybackSkill.play_media",
        new=_fake_play_media,
    ):
        mc = get_minicroft([SKILL_ID])
        yield mc
        mc.stop()


def _capture(mc, text, session_id):
    session = Session(session_id)
    session.lang = LANG
    session.pipeline = list(_PIPELINE)
    utterance = Message(
        "recognizer_loop:utterance",
        {"utterances": [text], "lang": LANG},
        {"session": session.serialize(), "source": "A", "destination": "B"},
    )
    capture = CaptureSession(mc)
    capture.capture(utterance, timeout=30)
    return capture.finish()


@pytest.mark.timeout(60)
@pytest.mark.parametrize("row", GOLDEN_ROWS, ids=lambda r: r["utterance"])
def test_golden_utterance(minicroft, row):
    expected_intent = f"{SKILL_ID}:{row['intent_label']}"
    messages = _capture(minicroft, row["utterance"], f"golden-{row['utterance']}")
    matched = [m for m in messages if m.msg_type == "ovos.intent.matched"]
    assert matched, (
        f"{row['utterance']!r}: expected ovos.intent.matched, got "
        f"{[m.msg_type for m in messages]!r}"
    )
    names = [m.data.get("intent_name") for m in matched]
    assert expected_intent in names, (
        f"{row['utterance']!r}: expected intent_name {expected_intent!r}, got {names!r}"
    )


@pytest.mark.timeout(60)
@pytest.mark.parametrize("negative", NEGATIVE_UTTERANCES, ids=lambda n: n[0])
def test_negative_confusable_not_claimed(minicroft, negative):
    text, source_skill = negative
    messages = _capture(minicroft, text, f"negative-{text}")
    matched = [m for m in messages if m.msg_type == "ovos.intent.matched"]
    claimed = any(
        (m.data.get("intent_name") or "").startswith(f"{SKILL_ID}:") for m in matched
    )
    assert not claimed, f"{text!r} (from {source_skill}) was incorrectly claimed by {SKILL_ID}"
