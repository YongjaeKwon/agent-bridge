---
name: task-complete
description: Record Claude work completion in the local ECC queue.
triggers:
  - PostToolUse
matcher:
  - Edit
  - Write
---

# Task Complete Hook

After Claude finishes a coherent edit, summarize the work through the ECC harness.

## Behavior

1. Log the important change:

```bash
python ecc.py log --agent claude --task <task-id> --message "Changed: ..."
```

2. When the task is actually complete, mark it done:

```bash
python ecc.py task done <task-id> --agent claude --summary "..."
```

3. If another CLI should continue, create a follow-up task and assign it:

```bash
python ecc.py task create --title "..." --body "..." --assignee codex
```

## Rules

- Keep summaries short and concrete.
- Run relevant verification before marking a task done.
- Do not sync to external services unless explicitly requested.
