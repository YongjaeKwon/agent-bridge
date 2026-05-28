# ECC Harness Instructions

Use the local ECC harness whenever work needs coordination with Claude, Codex, Gemini, Linear, GitHub, Slack, or Notion.

Codex does not use Claude-style `.claude/hooks/*.md` files. Treat this file, the ECC MCP server, and the `python ecc.py auto ...` loop as the Codex-side hook layer.

The main agent is `planner` and should run on Claude. Users should send top-level requests to the planner. Codex is a subagent for implementation, backend/integration, verification, and review.

## Local Queue

- Check work: `python ecc.py status`
- Send user request to main planner: `python ecc.py request --goal "..."`
- List configured agents: `python ecc.py agents`
- Create work: `python ecc.py task create --title "..." --body "..."`
- Claim work: `python ecc.py task claim <task-id> --agent codex`
- Log progress: `python ecc.py log --agent codex --task <task-id> --message "..."`
- Complete work: `python ecc.py task done <task-id> --agent codex --summary "..."`
- Dispatch open work: `python ecc.py dispatch`
- Run assigned work once: `python ecc.py auto`
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

If the planner or another subagent should continue, create a follow-up task using the configured agent id:

```bash
python ecc.py task create --title "..." --body "..." --assignee planner
```

## External Sync

- Linear ticket: `python ecc.py sync linear --task <task-id>`
- GitHub issue: `python ecc.py sync github --task <task-id>`
- Notion meeting page: `python ecc.py sync notion --meeting <meeting-id>`
- Slack update: `python ecc.py sync slack --message "..."`

Never write tokens into config files. Read them from `.env`.

## Agent Commands

The auto loop calls local CLI commands configured in `ecc_agents.json`. Override them in `.env` when needed:

- `ECC_PLANNER_COMMAND=claude -p`
- `ECC_CODEX_COMMAND=codex exec`
- `ECC_GEMINI_COMMAND=gemini -p`
- `ECC_CLAUDE_CODE_COMMAND=claude -p`
