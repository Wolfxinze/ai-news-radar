from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.export_knowledge_base import (
    evidence_from_story,
    export_payload,
    selected_stories,
    stable_record_id,
)


NOW = datetime(2026, 7, 27, 6, 0, tzinfo=timezone.utc)


def make_story(
    idx: int,
    *,
    score: float = 0.8,
    source_count: int = 1,
    reasons: list[str] | None = None,
    url: str | None = None,
) -> dict:
    primary_url = url or f"https://example.com/releases/{idx}?utm_source=rss"
    sources = [
        {
            "id": f"item-{idx}-{source_idx}",
            "title": f"Example AI release {idx}",
            "title_en": f"Example AI release {idx}",
            "title_zh": None,
            "title_original": f"Example AI release {idx}",
            "summary": f"Summary {idx}",
            "recommend_reason_zh": f"Why {idx}",
            "url": primary_url if source_idx == 0 else f"https://publisher{source_idx}.example/{idx}",
            "source": f"Publisher {source_idx}",
            "source_name": "Official AI Updates" if source_idx == 0 else "Curated Media",
            "site_id": "official_ai" if source_idx == 0 else "curated_media",
            "published_at": "2026-07-27T05:00:00Z",
        }
        for source_idx in range(source_count)
    ]
    return {
        "story_id": f"story-{idx}",
        "title": f"Example AI release {idx}",
        "url": primary_url,
        "primary_url": primary_url,
        "source": "Publisher 0",
        "source_name": "Official AI Updates",
        "sources": sources,
        "source_count": source_count,
        "score": score,
        "importance_score": score,
        "importance_label": "Official update",
        "importance_breakdown": {"editorial": 0.9},
        "category": "official" if "official_source" in (reasons or []) else "watch",
        "reasons": reasons or [],
        "earliest_at": "2026-07-27T05:00:00Z",
        "latest_at": "2026-07-27T05:00:00Z",
        "primary_item": sources[0],
    }


def make_payload(*stories: dict, generated_at: str = "2026-07-27T05:30:00Z") -> dict:
    return {
        "generated_at": generated_at,
        "window_hours": 24,
        "total_stories": len(stories),
        "stories": list(stories),
    }


def test_stable_record_id_ignores_tracking_parameters():
    first = make_story(1, url="https://Example.com/release/?utm_source=rss#section")
    second = make_story(1, url="https://example.com/release")

    assert stable_record_id(first) == stable_record_id(second)


def test_stable_record_id_survives_title_enhancement_for_normal_urls():
    first = make_story(1, url="https://example.com/release")
    second = make_story(1, url="https://example.com/release")
    second["title"] = "A clearer rewritten release title"
    second["primary_item"]["title_original"] = "A clearer rewritten release title"

    assert stable_record_id(first) == stable_record_id(second)


def test_shared_hub_urls_use_title_to_avoid_collisions():
    first = make_story(1, url="https://waytoagi.example/wiki")
    second = make_story(2, url="https://waytoagi.example/wiki")
    first["primary_item"]["site_id"] = "waytoagi"
    second["primary_item"]["site_id"] = "waytoagi"

    assert stable_record_id(first) != stable_record_id(second)


def test_candidate_gate_keeps_strong_corroborated_and_official_stories():
    weak = make_story(1, score=0.2)
    strong = make_story(2, score=0.8)
    corroborated = make_story(3, score=0.4, source_count=2)
    official = make_story(4, score=0.4, reasons=["official_source"])

    selected = selected_stories(
        [weak, strong, corroborated, official],
        min_importance=0.72,
        max_items=10,
    )

    assert {story["story_id"] for story in selected} == {"story-2", "story-3", "story-4"}


def test_evidence_deduplicates_same_publisher_and_canonical_url():
    story = make_story(1)
    duplicate = dict(story["sources"][0])
    duplicate["url"] = "https://example.com/releases/1?utm_campaign=duplicate"
    story["sources"].append(duplicate)

    evidence = evidence_from_story(story)

    assert len(evidence) == 1
    assert evidence[0]["publisher"] == "Publisher 0"


def test_export_preserves_existing_review_note(tmp_path: Path):
    payload = make_payload(make_story(1))
    output_dir = tmp_path / "knowledge-base"

    first_manifest = export_payload(payload, output_dir=output_dir, now=NOW)
    note_path = next((output_dir / "notes").rglob("*.md"))
    note_path.write_text("human review", encoding="utf-8")
    second_manifest = export_payload(payload, output_dir=output_dir, now=NOW)

    assert first_manifest["new_note_count"] == 1
    assert second_manifest["new_note_count"] == 0
    assert second_manifest["preserved_note_count"] == 1
    assert note_path.read_text(encoding="utf-8") == "human review"
    current = [
        json.loads(line)
        for line in (output_dir / "generated" / "current.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert current[0]["status"] == "candidate"
    assert current[0]["provenance"]["verification"] == "unverified_candidate"


def test_export_rejects_stale_payload_by_default(tmp_path: Path):
    stale = make_payload(make_story(1), generated_at="2026-07-20T05:30:00Z")

    with pytest.raises(ValueError, match="stale"):
        export_payload(stale, output_dir=tmp_path / "knowledge-base", now=NOW)


def test_export_allows_stale_payload_for_backfill(tmp_path: Path):
    stale = make_payload(make_story(1), generated_at="2026-07-20T05:30:00Z")

    manifest = export_payload(
        stale,
        output_dir=tmp_path / "knowledge-base",
        now=NOW,
        allow_stale=True,
    )

    assert manifest["record_count"] == 1
