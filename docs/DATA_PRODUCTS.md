# 数据产物 / Data products

Each pipeline run writes a set of static JSON files. The site reads only these
files; there is no backend. GitHub Pages is the canonical data source. A Vercel
host, if used, is another front for the same files.

## Core files

- `data/daily-brief.json`: 伯乐精选 20 条日报成品。From v0.8 this includes persona scores and commentary fields.
- `data/top3-personas.json`: Side-by-side three-persona commentary for the day's TOP3 stories.
- `data/latest-24h.json`: AI-strong items from the last 24 hours (the curated signal pool).
- `data/latest-24h-all.json`: Broader AI-related items from the last 24 hours (`score >= 0.3`).
- `data/latest-24h-all-raw.json`: Unfiltered last-24h dump. Dev-only; the frontend does not load it.
- `data/source-status.json`: Fetch status, success rates, site coverage, and source health.
- `data/stories-merged.json`: Full event set after story merge.
- `data/merge-log.json`: Story-merge process and match records, for debugging and audit.

## Fallback behavior

If `daily-brief.json` is missing, the page falls back to the candidate signal
list. If `stories-merged.json` exists, the page uses the full story pool to fill
later storylines so the UI is not limited to a small curated set.
