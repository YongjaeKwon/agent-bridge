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

## 4. 토큰 발급 링크

외부 sync를 쓰는 서비스만 채우면 됩니다. 로컬 Claude/Codex 자동 루프만 쓸 때는 서비스 토큰이 없어도 됩니다.

### GitHub

- 공식 문서: [Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- 바로가기: [GitHub fine-grained tokens](https://github.com/settings/personal-access-tokens)
- `.env` 값:

```env
GITHUB_TOKEN=github_pat_... 또는 ghp_...
GITHUB_REPOSITORY=owner/repo
```

권장 권한:

- Repository access: 이 하네스를 쓸 repo만 선택
- Permissions: Issues read/write

`GITHUB_REPOSITORY`는 GitHub URL의 `owner/repo`입니다. 예: `YongjaeKwon/portfolio`. 이미 GitHub origin remote가 있으면 비워둬도 자동 추론을 시도합니다.

### Linear

- 공식 문서: [Linear GraphQL API authentication](https://linear.app/developers/graphql)
- 설정 위치: Linear `Settings` -> `Account` -> `Security & Access` -> `Personal API keys`
- `.env` 값:

```env
LINEAR_API_KEY=lin_api_...
LINEAR_TEAM_ID=
LINEAR_PROJECT_ID=
```

`LINEAR_TEAM_ID`는 팀 이름이 아니라 내부 team id입니다. 팀이 하나뿐이면 비워둬도 하네스가 자동 선택합니다. 팀이 여러 개면 `python ecc.py sync linear --task ...` 실행 시 후보를 보여주므로 그때 나온 id를 넣으세요.

Linear Project로 이슈를 나누려면 `LINEAR_PROJECT_ID`를 넣습니다. 프로젝트 id는 아래 명령으로 확인합니다.

```bash
python ecc.py sync linear-projects
```

한 번만 특정 프로젝트에 넣고 싶으면:

```bash
python ecc.py sync linear --task task-xxxxxxxx --project-id <linear-project-id>
```

### Notion

- 공식 문서: [Notion internal integrations](https://developers.notion.com/guides/get-started/internal-integrations)
- 바로가기: [Notion integrations](https://www.notion.so/my-integrations)
- `.env` 값:

```env
NOTION_TOKEN=ntn_...
NOTION_PARENT_PAGE_ID=page_id
```

사용 순서:

1. Notion integration을 만들고 internal integration token을 복사합니다.
2. 회의록/작업 로그를 모을 parent page를 하나 만듭니다.
3. 그 페이지의 Share/Connections에서 integration을 연결합니다.
4. 페이지 링크에서 page id를 복사해 `NOTION_PARENT_PAGE_ID`에 넣습니다.

integration을 parent page에 연결하지 않으면 Notion API가 `object_not_found` 또는 권한 오류를 반환합니다.

### Slack

- 공식 문서: [Slack tokens](https://docs.slack.dev/authentication/tokens/)
- 앱 생성: [Slack apps](https://api.slack.com/apps)
- `.env` 값:

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_TEAM_ID=T...
SLACK_DEFAULT_CHANNEL_ID=C...
```

기본 흐름:

1. Slack app을 생성합니다.
2. Bot Token Scopes에 `chat:write`를 추가합니다.
3. 앱을 workspace에 설치합니다.
4. Bot User OAuth Token(`xoxb-...`)을 `SLACK_BOT_TOKEN`에 넣습니다.
5. 메시지를 보낼 채널에 앱을 초대하고 channel id를 `SLACK_DEFAULT_CHANNEL_ID`에 넣습니다.

## 5. 시작

```bash
python ecc.py init
python main.py
```

`python main.py`는 토큰이 준비됐는지 확인합니다.

## 6. 작업 만들기

```bash
python ecc.py task create --title "로그인 API 수정" --body "실패 케이스 재현 후 테스트와 수정 추가"
```

## 7. 자동으로 분배하고 실행

먼저 실제 실행 없이 확인:

```bash
python ecc.py auto --dispatch --dry-run
```

괜찮으면 자동 루프 실행:

```bash
python ecc.py auto --dispatch --loop --max-cycles 20 --interval 30
```

이 명령은 열린 작업을 Claude/Codex에 분배하고, 각 CLI를 실행합니다. 각 CLI는 자기 역할 설정대로 작업하고 `.ecc`에 진행 로그를 남깁니다.
Claude/Codex CLI 출력은 현재 터미널에 그대로 표시됩니다.

## 8. 자주 쓰는 명령

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

## 9. 외부 도구로 sync

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

## 10. MCP 사용

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

## 11. 커밋하면 좋은 것

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
