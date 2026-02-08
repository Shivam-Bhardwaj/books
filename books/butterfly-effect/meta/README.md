# StoryOS Metadata Hub

Aggregated project dashboard for **Butterfly Effect**.

## What's Here

| File | Description |
|------|-------------|
| `storyos.json` | Generated JSON payload with all project metadata |
| `storyos.md` | Generated Markdown dashboard (same data, scannable) |
| `ui/` | Local web UI for browsing the dashboard |

All files are **generated** by `tools/build_storyos.py`. Do not hand-edit them.

The hand-edited control plane lives at `schema/storyos.yaml` (threads, promises, pins, arc metadata).

## Rebuild

```bash
# Validate schema only
python3 tools/build_storyos.py --check

# Generate storyos.json + storyos.md
python3 tools/build_storyos.py
```

## View the Web UI

Serve the book directory and open the UI:

```bash
python3 -m http.server 8800 --directory .
# then open http://localhost:8800/meta/ui/
```

Or use the project dev server and navigate to the UI path.

## Data Sources

- `schema/storyos.yaml` - threads, promises, pins (hand-edited)
- `schema/entities.yaml` - characters, places, concepts
- `schema/chapter-cards.yaml` - 40-chapter table
- `book.yaml` - title, subtitle
- `outline/ARCS.md` - arc table
- `outline/BUTTERFLY_GRAPH.md` - causal chains
- `review/continuity-log.md` - chapter coverage
- `review/revision-queue.md` - open/closed items
- `manuscript/**/*.html` - drafted chapters
