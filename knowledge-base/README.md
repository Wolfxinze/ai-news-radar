# Knowledge-base export

This directory turns AI News Radar story clusters into durable, provenance-first
knowledge candidates. It is an editorial staging area, not an automatic source
of verified facts.

## Output layers

- `generated/current.jsonl`: the current quality-gated candidate set for search,
  RAG, databases, or downstream integrations.
- `generated/records/<id>.json`: the latest structured record for each event.
  Records persist after the event leaves the 24-hour Radar window.
- `generated/manifest.json`: source freshness, export counts, and filter settings.
- `notes/YYYY/MM/DD/<id>.md`: human-review notes. Existing notes are preserved
  on later runs so editorial changes are never silently overwritten.

Generated summaries, translations, importance scores, and recommendations remain
explicitly marked as unverified. Every candidate keeps its original evidence
links and Radar provenance. A `multi_source_signal` confidence value means Radar
grouped multiple source records; it does not by itself prove that every source
is independent or that the claims are correct.

## Run locally

First generate or download `data/stories-merged.json`, then run:

```bash
python scripts/export_knowledge_base.py \
  --stories data/stories-merged.json \
  --output-dir knowledge-base
```

Defaults:

- input must be no more than 36 hours old;
- stories pass when they have importance `>= 0.72`, multiple sources, or an
  official-source signal;
- at most 50 candidates are exported per run;
- existing Markdown review notes are not overwritten.

For an intentional historical backfill, add `--allow-stale`. Use
`--overwrite-notes` only when discarding human edits is explicitly intended.

## Downstream ingestion

Index `generated/current.jsonl` for a current-feed experience. Index
`generated/records/*.json` or reviewed Markdown notes for historical retrieval.
For a production knowledge base, publish only records whose review note status
has been changed from `candidate` to `reviewed` or `published`.

The exporter does not copy full publisher articles. It stores Radar metadata,
short upstream summaries when present, and source links so downstream systems
can retain attribution and perform their own authorized enrichment.
