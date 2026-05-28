# ECC Harness Instructions

Use the local ECC harness whenever work needs coordination with Claude, Linear, GitHub, Slack, or Notion.

## Local Queue

- Check work: `python ecc.py status`
- Create work: `python ecc.py task create --title "..." --body "..."`
- Claim work: `python ecc.py task claim <task-id> --agent codex`
- Log progress: `python ecc.py log --agent codex --task <task-id> --message "..."`
- Complete work: `python ecc.py task done <task-id> --agent codex --summary "..."`
- Dispatch open work: `python ecc.py dispatch --agents claude,codex`
- Run assigned work once: `python ecc.py auto --agents claude,codex`
- Keep polling: `python ecc.py auto --dispatch --loop --max-cycles 20 --interval 30`

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
