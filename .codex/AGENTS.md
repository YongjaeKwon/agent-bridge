# ECC Harness Instructions

Use the local ECC harness whenever work needs coordination with Claude, Linear, GitHub, Slack, or Notion.

Codex does not use Claude-style `.claude/hooks/*.md` files. Treat this file, the ECC MCP server, and the `python ecc.py auto ...` loop as the Codex-side hook layer.

## Local Queue

- Check work: `python ecc.py status`
- Create work: `python ecc.py task create --title "..." --body "..."`
- Claim work: `python ecc.py task claim <task-id> --agent codex`
- Log progress: `python ecc.py log --agent codex --task <task-id> --message "..."`
- Complete work: `python ecc.py task done <task-id> --agent codex --summary "..."`
- Dispatch open work: `python ecc.py dispatch --agents claude,codex`
- Run assigned work once: `python ecc.py auto --agents claude,codex`
- Keep polling: `python ecc.py auto --dispatch --loop --max-cycles 20 --interval 30`

## Codex Work Contract

At the start of assigned work:

```bash
python ecc.py task claim <task-id> --agent codex
```

During work:

```bash
python ecc.py log --agent codex --task <task-id> --message "..."
```

When complete:

```bash
python ecc.py task done <task-id> --agent codex --summary "..."
```

If Claude should continue, create a follow-up task:

```bash
python ecc.py task create --title "..." --body "..." --assignee claude
```

## External Sync

- Linear ticket: `python ecc.py sync linear --task <task-id>`
- GitHub issue: `python ecc.py sync github --task <task-id>`
- Notion meeting page: `python ecc.py sync notion --meeting <meeting-id>`
- Slack update: `python ecc.py sync slack --message "..."`

Never write tokens into config files. Read them from `.env`.

## Agent Commands

The auto loop calls local CLI commands. Override them in `.env` when needed:

- `ECC_CLAUDE_COMMAND=claude -p`
- `ECC_CODEX_COMMAND=codex exec`
