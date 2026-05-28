---
name: ecc
description: Coordinate Claude/Codex work through the local ECC harness.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /ecc

Use this command when work should be tracked, handed off, or synchronized through the local ECC harness.

## Workflow

1. Inspect queue: `python ecc.py status`
2. Create or claim a task.
3. Log material progress with `python ecc.py log --agent claude --task <task-id> --message "..."`
4. When complete, run `python ecc.py task done <task-id> --agent claude --summary "..."`
5. Sync externally only when requested or when the workflow clearly needs it:
   - `python ecc.py sync linear --task <task-id>`
   - `python ecc.py sync github --task <task-id>`
   - `python ecc.py sync notion --meeting <meeting-id>`
   - `python ecc.py sync slack --message "..."`

## Automatic Loop

Use this when Claude and Codex should pass work through the local queue without manual handoffs:

```bash
python ecc.py auto --dispatch --loop --max-cycles 20 --interval 30
```

Override local CLI commands in `.env` if this machine uses different command names:

```env
ECC_CLAUDE_COMMAND=claude -p
ECC_CODEX_COMMAND=codex exec
```

## Rules

- Do not put tokens in command files, MCP config, or committed docs.
- Use `.env` for credentials.
- Keep local task summaries short and actionable.
- Prefer one task per coherent unit of work.
