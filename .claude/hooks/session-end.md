---
name: session-end
description: Capture an end-of-session summary for optional Notion sync.
triggers:
  - Stop
---

# Session End Hook

At the end of a Claude session, capture what happened in the local ECC queue.

## Behavior

1. Check current work:

```bash
python ecc.py status
```

2. Add a meeting-style session note when useful:

```bash
python ecc.py meeting add --title "Session summary" --participants "Claude, Codex" --notes "..."
```

3. Sync to Notion only when explicitly requested:

```bash
python ecc.py sync notion --meeting <meeting-id>
```

## Rules

- Keep session notes focused on decisions, completed work, blockers, and follow-ups.
- Do not write to Notion automatically from this hook.
