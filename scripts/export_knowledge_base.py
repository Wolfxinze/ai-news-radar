from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from scripts.update_news import canonical_story_url, parse_iso
except ModuleNotFoundError:  # Direct execution: python scripts/export_knowledge_base.py
    from update_news import canonical_story_url, parse_iso


UTC = timezone.utc
SCHEMA_VERSION = 1
DEFAULT_MIN_IMPORTANCE = 0.72
DEFAULT_MAX_ITEMS = 50
DEFAULT_MAX_AGE_HOURS = 36.0
SHARED_URL_SITE_IDS = {"waytoagi"}


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def stable_record_id(story: dict[str, Any]) -> str:
    primary_url = canonical_story_url(str(story.get("primary_url") or story.get("url") or ""))
    primary = story.get("primary_item") if isinstance(story.get("primary_item"), dict) else {}
    title = compact_text(primary.get("title_original") or story.get("title")).lower()
    site_id = str(primary.get("site_id") or "")
    if not site_id and isinstance(story.get("sources"), list):
        for source in story["sources"]:
            if not isinstance(source, dict):
                continue
            source_url = canonical_story_url(str(source.get("url") or ""))
            if source_url == primary_url:
                site_id = str(source.get("site_id") or "")
                break
    if primary_url and site_id in SHARED_URL_SITE_IDS and title:
        # Some community feeds publish unrelated notes under one shared hub URL.
        basis = f"{primary_url}\x1f{title}"
    else:
        basis = primary_url or title
    if not basis:
        basis = str(story.get("story_id") or "")
    if not basis:
        raise ValueError("Story has no URL, title, or story_id")
    return "ai-event-" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]


def numeric(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def integer(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def story_is_candidate(story: dict[str, Any], min_importance: float) -> bool:
    reasons = {str(reason) for reason in story.get("reasons", []) if reason}
    return (
        numeric(story.get("importance_score", story.get("score"))) >= min_importance
        or integer(story.get("source_count"), 1) >= 2
        or "official_source" in reasons
    )


def selected_stories(
    stories: Iterable[dict[str, Any]],
    *,
    min_importance: float,
    max_items: int,
) -> list[dict[str, Any]]:
    candidates = [story for story in stories if story_is_candidate(story, min_importance)]

    def sort_key(story: dict[str, Any]) -> tuple[float, float, str]:
        latest = parse_iso(str(story.get("latest_at") or ""))
        return (
            -numeric(story.get("importance_score", story.get("score"))),
            -(latest.timestamp() if latest else 0.0),
            compact_text(story.get("title")),
        )

    candidates.sort(
        key=sort_key
    )
    return candidates[:max_items]


def confidence_for_story(story: dict[str, Any]) -> str:
    reasons = {str(reason) for reason in story.get("reasons", []) if reason}
    if "official_source" in reasons or story.get("category") == "official":
        return "official_first_party"
    if integer(story.get("source_count"), 1) >= 2:
        return "multi_source_signal"
    return "single_source"


def evidence_from_story(story: dict[str, Any]) -> list[dict[str, Any]]:
    raw_sources = story.get("sources")
    if not isinstance(raw_sources, list):
        raw_sources = story.get("items") if isinstance(story.get("items"), list) else []

    evidence: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        url = str(source.get("url") or "").strip()
        if not url:
            continue
        publisher = compact_text(source.get("source") or source.get("source_name"))
        key = (canonical_story_url(url), publisher.lower())
        if key in seen:
            continue
        seen.add(key)
        evidence.append(
            {
                "title": compact_text(source.get("title")),
                "publisher": publisher,
                "source_group": compact_text(source.get("source_name")),
                "url": url,
                "published_at": source.get("published_at"),
            }
        )

    if evidence:
        return evidence

    fallback_url = str(story.get("primary_url") or story.get("url") or "").strip()
    if fallback_url:
        evidence.append(
            {
                "title": compact_text(story.get("title")),
                "publisher": compact_text(story.get("source")),
                "source_group": compact_text(story.get("source_name")),
                "url": fallback_url,
                "published_at": story.get("latest_at") or story.get("earliest_at"),
            }
        )
    return evidence


def record_from_story(story: dict[str, Any], *, source_generated_at: str, exported_at: str) -> dict[str, Any]:
    primary = story.get("primary_item") if isinstance(story.get("primary_item"), dict) else {}
    canonical_url = canonical_story_url(str(story.get("primary_url") or story.get("url") or ""))
    reasons = [str(reason) for reason in story.get("reasons", []) if reason]
    return {
        "schema_version": SCHEMA_VERSION,
        "id": stable_record_id(story),
        "kind": "ai_event",
        "status": "candidate",
        "title": compact_text(story.get("title")),
        "title_zh": compact_text(primary.get("title_zh")) or None,
        "title_en": compact_text(primary.get("title_en")) or None,
        "summary_zh": compact_text(primary.get("summary")) or None,
        "why_it_matters_zh": compact_text(primary.get("recommend_reason_zh")) or None,
        "canonical_url": canonical_url,
        "published_at": story.get("latest_at") or story.get("earliest_at"),
        "first_seen_at": story.get("earliest_at"),
        "last_seen_at": story.get("latest_at"),
        "confidence": confidence_for_story(story),
        "labels": {
            "category": story.get("category"),
            "importance_label": story.get("importance_label"),
            "reasons": reasons,
        },
        "radar": {
            "story_id": story.get("story_id"),
            "importance_score": round(numeric(story.get("importance_score", story.get("score"))), 4),
            "importance_breakdown": story.get("importance_breakdown") or {},
            "source_count": integer(story.get("source_count"), 1),
        },
        "evidence": evidence_from_story(story),
        "provenance": {
            "provider": "LearnPrompt/ai-news-radar",
            "source_generated_at": source_generated_at,
            "exported_at": exported_at,
            "verification": "unverified_candidate",
        },
    }


def validate_payload_freshness(
    payload: dict[str, Any],
    *,
    now: datetime,
    max_age_hours: float,
    allow_stale: bool,
) -> str:
    generated_at = str(payload.get("generated_at") or "")
    generated = parse_iso(generated_at)
    if generated is None:
        raise ValueError("stories payload has no valid generated_at timestamp")
    age_hours = (now - generated).total_seconds() / 3600
    if age_hours < -1:
        raise ValueError(f"stories payload timestamp is {abs(age_hours):.1f}h in the future")
    if age_hours > max_age_hours and not allow_stale:
        raise ValueError(
            f"stories payload is stale ({age_hours:.1f}h old; maximum is {max_age_hours:.1f}h). "
            "Use --allow-stale only for intentional backfills."
        )
    return generated_at


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def yaml_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def markdown_link_text(value: Any) -> str:
    return compact_text(value).replace("[", "\\[").replace("]", "\\]")


def markdown_note(record: dict[str, Any]) -> str:
    summary = record.get("summary_zh") or "Radar did not provide a summary. Review the original evidence."
    why = record.get("why_it_matters_zh") or "Not provided. Add a verified assessment during review."
    evidence_lines = []
    for evidence in record.get("evidence", []):
        label = markdown_link_text(evidence.get("title") or evidence.get("publisher") or evidence.get("url"))
        publisher = compact_text(evidence.get("publisher"))
        suffix = f" — {publisher}" if publisher else ""
        evidence_lines.append(f"- [{label}]({evidence['url']}){suffix}")
    if not evidence_lines:
        evidence_lines.append("- No source URL was available; do not publish this candidate.")

    frontmatter = [
        "---",
        f"id: {yaml_value(record['id'])}",
        f"kind: {yaml_value(record['kind'])}",
        f"status: {yaml_value(record['status'])}",
        f"title: {yaml_value(record['title'])}",
        f"canonical_url: {yaml_value(record['canonical_url'])}",
        f"published_at: {yaml_value(record['published_at'])}",
        f"confidence: {yaml_value(record['confidence'])}",
        f"radar_story_id: {yaml_value(record['radar']['story_id'])}",
        f"radar_importance: {record['radar']['importance_score']}",
        f"source_generated_at: {yaml_value(record['provenance']['source_generated_at'])}",
        "---",
    ]
    return "\n".join(
        [
            *frontmatter,
            "",
            f"# {record['title']}",
            "",
            "> Candidate generated from AI News Radar. The summary and recommendation below are unverified routing signals, not established facts.",
            "",
            "## Radar summary",
            "",
            str(summary),
            "",
            "## Why it may matter",
            "",
            str(why),
            "",
            "## Evidence",
            "",
            *evidence_lines,
            "",
            "## Review checklist",
            "",
            "- [ ] Open and verify the primary source.",
            "- [ ] Separate confirmed claims from commentary or projections.",
            "- [ ] Resolve conflicts between sources.",
            "- [ ] Add entities, products, models, and durable topic tags.",
            "- [ ] Change `status` to `reviewed`, `published`, or `rejected`.",
            "",
        ]
    )


def record_date(record: dict[str, Any], fallback: datetime) -> str:
    published = parse_iso(str(record.get("published_at") or ""))
    return (published or fallback).date().isoformat()


def export_payload(
    payload: dict[str, Any],
    *,
    output_dir: Path,
    now: datetime,
    min_importance: float = DEFAULT_MIN_IMPORTANCE,
    max_items: int = DEFAULT_MAX_ITEMS,
    max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
    allow_stale: bool = False,
    overwrite_notes: bool = False,
) -> dict[str, Any]:
    source_generated_at = validate_payload_freshness(
        payload,
        now=now,
        max_age_hours=max_age_hours,
        allow_stale=allow_stale,
    )
    stories = payload.get("stories")
    if not isinstance(stories, list):
        raise ValueError("stories payload must contain a stories array")

    exported_at = iso(now)
    selected = selected_stories(
        (story for story in stories if isinstance(story, dict)),
        min_importance=min_importance,
        max_items=max_items,
    )
    records = [
        record_from_story(story, source_generated_at=source_generated_at, exported_at=exported_at)
        for story in selected
    ]

    generated_dir = output_dir / "generated"
    records_dir = generated_dir / "records"
    notes_dir = output_dir / "notes"
    new_notes = 0
    preserved_notes = 0

    current_jsonl = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    write_text_atomic(generated_dir / "current.jsonl", current_jsonl)

    for record in records:
        write_text_atomic(records_dir / f"{record['id']}.json", json_text(record))
        date_parts = record_date(record, now).split("-")
        note_path = notes_dir.joinpath(*date_parts, f"{record['id']}.md")
        if note_path.exists() and not overwrite_notes:
            preserved_notes += 1
            continue
        write_text_atomic(note_path, markdown_note(record))
        new_notes += 1

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": exported_at,
        "source_generated_at": source_generated_at,
        "record_count": len(records),
        "new_note_count": new_notes,
        "preserved_note_count": preserved_notes,
        "filters": {
            "min_importance": min_importance,
            "max_items": max_items,
            "max_age_hours": max_age_hours,
            "allow_stale": allow_stale,
        },
        "outputs": {
            "current_jsonl": "generated/current.jsonl",
            "records": "generated/records/",
            "notes": "notes/YYYY/MM/DD/",
        },
    }
    write_text_atomic(generated_dir / "manifest.json", json_text(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export AI News Radar story clusters as provenance-first knowledge-base candidates."
    )
    parser.add_argument("--stories", default="data/stories-merged.json", help="Input stories-merged.json path")
    parser.add_argument("--output-dir", default="knowledge-base", help="Knowledge-base output directory")
    parser.add_argument("--min-importance", type=float, default=DEFAULT_MIN_IMPORTANCE)
    parser.add_argument("--max-items", type=int, default=DEFAULT_MAX_ITEMS)
    parser.add_argument("--max-age-hours", type=float, default=DEFAULT_MAX_AGE_HOURS)
    parser.add_argument("--allow-stale", action="store_true", help="Allow stale input for intentional backfills")
    parser.add_argument(
        "--overwrite-notes",
        action="store_true",
        help="Overwrite existing review notes. Disabled by default to preserve human edits.",
    )
    args = parser.parse_args()

    if not 0 <= args.min_importance <= 1:
        parser.error("--min-importance must be between 0 and 1")
    if args.max_items < 1:
        parser.error("--max-items must be at least 1")
    if args.max_age_hours <= 0:
        parser.error("--max-age-hours must be positive")

    stories_path = Path(args.stories)
    try:
        payload = json.loads(stories_path.read_text(encoding="utf-8"))
        manifest = export_payload(
            payload,
            output_dir=Path(args.output_dir),
            now=utc_now(),
            min_importance=args.min_importance,
            max_items=args.max_items,
            max_age_hours=args.max_age_hours,
            allow_stale=args.allow_stale,
            overwrite_notes=args.overwrite_notes,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(1, f"knowledge-base export failed: {exc}\n")

    print(
        "Knowledge-base export complete: "
        f"{manifest['record_count']} records, "
        f"{manifest['new_note_count']} new notes, "
        f"{manifest['preserved_note_count']} preserved notes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
