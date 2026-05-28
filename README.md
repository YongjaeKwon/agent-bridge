# ECC 협업 하네스

Claude CLI와 Codex CLI가 같은 프로젝트에서 작업을 주고받게 하는 간단한 하네스입니다.

Linear, GitHub, Slack, Notion 토큰을 `.env`에 넣어두면 작업 생성, 분배, 로그, 회의록, 외부 sync까지 한 흐름으로 묶을 수 있습니다.

## 1. 기존 프로젝트에 복사

기존 프로젝트 루트에 아래 파일/폴더를 복사합니다.

```text
ecc.py
ecc_mcp.py
ecc_harness/
scripts/
mcp-configs/
.env.example
.ecc/README.md
.codex/config.toml
.codex/AGENTS.md
.claude/commands/ecc.md
```

이미 `.codex/config.toml`이나 `.claude/`가 있으면 덮어쓰지 말고 필요한 부분만 합치세요.

## 2. 설치

```bash
pip install python-dotenv
```

Python 프로젝트가 아니어도 괜찮습니다. Python은 이 하네스를 실행할 때만 씁니다.

## 3. 토큰 입력

```bash
copy .env.example .env
```

macOS/Linux에서는:

```bash
cp .env.example .env
```

`.env`에 필요한 값을 채웁니다.

```env
GITHUB_TOKEN=
GITHUB_REPOSITORY=owner/repo

LINEAR_API_KEY=
LINEAR_TEAM_ID=

SLACK_BOT_TOKEN=
SLACK_TEAM_ID=
SLACK_DEFAULT_CHANNEL_ID=

NOTION_TOKEN=
NOTION_PARENT_PAGE_ID=

ECC_CLAUDE_COMMAND=claude -p
ECC_CODEX_COMMAND=codex exec
```

역할은 Claude/Codex CLI 쪽 설정에서 부여하세요. 하네스는 어떤 CLI를 깨울지만 담당합니다.

## 4. 시작

```bash
python ecc.py init
python main.py
```

`python main.py`는 토큰이 준비됐는지 확인합니다.

## 5. 작업 만들기

```bash
python ecc.py task create --title "로그인 API 수정" --body "실패 케이스 재현 후 테스트와 수정 추가"
```

## 6. 자동으로 분배하고 실행

먼저 실제 실행 없이 확인:

```bash
python ecc.py auto --dispatch --dry-run
```

괜찮으면 자동 루프 실행:

```bash
python ecc.py auto --dispatch --loop --max-cycles 20 --interval 30
```

이 명령은 열린 작업을 Claude/Codex에 분배하고, 각 CLI를 실행합니다. 각 CLI는 자기 역할 설정대로 작업하고 `.ecc`에 진행 로그를 남깁니다.

## 7. 자주 쓰는 명령

작업 목록:

```bash
python ecc.py status
```

작업 수동 배정:

```bash
python ecc.py dispatch --agents claude,codex
```

진행 로그:

```bash
python ecc.py log --agent codex --task task-xxxxxxxx --message "원인 확인 완료"
```

완료 처리:

```bash
python ecc.py task done task-xxxxxxxx --agent codex --summary "테스트와 수정 완료"
```

회의록 저장:

```bash
python ecc.py meeting add --title "주간 싱크" --participants "Claude, Codex" --notes "결정사항..."
```

## 8. 외부 도구로 sync

Linear 티켓 생성:

```bash
python ecc.py sync linear --task task-xxxxxxxx
```

GitHub issue 생성:

```bash
python ecc.py sync github --task task-xxxxxxxx
```

Notion 회의록 생성:

```bash
python ecc.py sync notion --meeting mtg-xxxxxxxx
```

Slack 메시지 전송:

```bash
python ecc.py sync slack --message "작업 분배 완료"
```

외부 도구에 쓰는 작업은 `sync` 명령을 실행할 때만 일어납니다.

## 9. MCP 사용

Codex는 `.codex/config.toml`을 사용합니다.

Codex에는 Claude 스타일의 `.claude/hooks/*.md` 훅이 없습니다. 대신 아래 세 가지가 Codex 쪽 훅 역할을 합니다.

```text
.codex/AGENTS.md
ecc_mcp.py
python ecc.py auto --dispatch --loop
```

즉, Claude는 `.claude/hooks/`로 작업 습관을 안내하고, Codex는 `.codex/AGENTS.md`와 ECC MCP/auto loop로 같은 규칙을 따릅니다.

Claude Desktop용 예시는:

```text
mcp-configs/claude_desktop_config.example.json
```

로컬 ECC MCP 서버는 다음 도구를 제공합니다.

```text
ecc_create_task
ecc_list_tasks
ecc_claim_task
ecc_complete_task
ecc_log
ecc_add_meeting
```

## 10. 커밋하면 좋은 것

커밋:

```text
ecc.py
ecc_mcp.py
ecc_harness/
scripts/
mcp-configs/
.env.example
.ecc/README.md
.codex/
.claude/commands/ecc.md
```

커밋하지 말 것:

```text
.env
.ecc/*.jsonl
```

`.env`에는 토큰이 들어가고, `.ecc/*.jsonl`에는 런타임 작업 로그가 들어갑니다.
