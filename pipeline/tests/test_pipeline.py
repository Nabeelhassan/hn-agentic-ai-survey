from __future__ import annotations

from hn_agents.aggregate import _breakdown
from hn_agents.extract import _signature
from hn_agents.merge import choose_record
from hn_agents.normalize import _depths, html_to_markdown


def test_html_to_markdown_decodes_entities_and_links():
    raw = "I use &quot;Claude&quot; &amp; Codex.<p>See <a href=\"https://x.dev\" rel=\"nofollow\">https://x.dev</a></p>"
    text = html_to_markdown(raw)
    assert '"Claude" & Codex.' in text
    assert "https://x.dev" in text
    assert "<" not in text


def test_depths_follow_parent_chain():
    records = {
        "1": {"parent_id": "story", "is_top_level": True},
        "2": {"parent_id": "1", "is_top_level": False},
        "3": {"parent_id": "2", "is_top_level": False},
        "4": {"parent_id": "missing", "is_top_level": False},
    }
    depths = _depths(records)
    assert depths == {"1": 0, "2": 1, "3": 2, "4": 0}


def test_choose_record_prefers_confidence_then_primary_model():
    low = {"model": "z-ai/glm-5.3-flash", "status": "ok", "confidence": 0.4}
    high = {"model": "deepseek/deepseek-v4.1-flash", "status": "ok", "confidence": 0.9}
    tie = {"model": "deepseek/deepseek-v4.1-flash", "status": "ok", "confidence": 0.9}
    assert choose_record([low, high]) is high
    assert choose_record([high, tie]) is high


def test_breakdown_keeps_unstated_row():
    rows = _breakdown({"anthropic": {"a", "b"}}, {"anthropic": {"1", "2"}}, 4, {"anthropic": "Anthropic"})
    assert [row["node"] for row in rows] == ["anthropic", "unstated"]
    assert rows[1]["count"] == 2


def test_signature_ignores_tier_text():
    left = {"answers_questions": "partial", "q1_subscriptions": [{"node": "anthropic", "tier_raw": "Max"}]}
    right = {"answers_questions": "partial", "q1_subscriptions": [{"node": "anthropic", "tier_raw": "Pro"}]}
    assert _signature(left) == _signature(right)
