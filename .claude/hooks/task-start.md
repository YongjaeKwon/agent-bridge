---
name: task-start
description: Record the start of Claude work in the local ECC queue.
triggers:
  - PreToolUse
matcher:
  - Edit
  - Write
---

# Task Start Hook

When Claude starts editing or writing files, use the ECC harness as the source of truth.

## Behavior

1. Check the current queue with `python ecc.py status`.
2. If the active task is known, claim it:

```bash
python ecc.py task claim <task-id> --agent claude
```

3. Record a short start log:

```bash
python ecc.py log --agent claude --task <task-id> --message "Started work"
```

## Rules

- Do not create Linear, GitHub, Notion, or Slack records from this hook.
- External writes must happen through explicit `python ecc.py sync ...` commands.
- If no task id is known, continue work and create or claim a task manually when context is clear.
