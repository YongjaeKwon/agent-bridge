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
ecc_agents.json
```

이미 `.codex/config.toml`이나 `.claude/`가 있으면 덮어쓰지 말고 필요한 부분만 합치세요.

## 2. 설치

```bash
pip install -r requirements.txt
```

Python 프로젝트가 아니어도 괜찮습니다. Python은 이 하네스와 로컬 콘솔 UI를 실행할 때만 씁니다.

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

ECC_PLANNER_COMMAND=
ECC_CODEX_COMMAND=codex exec
ECC_GEMINI_COMMAND=
ECC_CLAUDE_CODE_COMMAND=
```

멀티 에이전트 역할은 `ecc_agents.json`에서 관리합니다. 기본 구조는 Claude planner가 메인 에이전트이고, Codex/Claude Code가 기본 서브 에이전트입니다. Gemini는 나중에 붙일 수 있는 선택 서브 에이전트로 남겨둡니다. 사용자는 Claude planner에게만 목표를 주고, planner가 하위 task를 만들고 assignee를 지정합니다.

Windows 기본값:

```text
planner      -> cmd /c claude.cmd -p
codex        -> cmd /c codex.cmd exec
gemini       -> cmd /c gemini.cmd -p
claude-code  -> cmd /c claude.cmd -p
```

Gemini는 `ecc_agents.json`에서 `optional: true`, `enabledByDefault: false`로 둡니다. 나중에 Gemini CLI를 설치하고 `.env`에 `ECC_GEMINI_COMMAND=cmd /c gemini.cmd -p`처럼 값을 넣으면 자동 분배 후보에 포함됩니다.

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

처음 설정은 로컬 콘솔 UI로 하는 편이 가장 쉽습니다.

```bash
python ecc.py ui
```

브라우저에서 `http://127.0.0.1:8765`를 열면 토큰, GitHub repo, Linear team/project, Notion parent page, Slack channel, 에이전트 CLI 명령을 한 화면에서 관리할 수 있습니다. 비밀값은 저장 여부만 보여주고 값 자체는 다시 표시하지 않습니다.

UI에서 할 수 있는 일:

- Overview: GitHub/Linear/Slack/Notion 준비 상태 확인
- Setup: `.env` 값 저장, Linear 프로젝트 조회
- Agents: planner/codex/claude-code/Gemini 활성 상태 확인
- Work: Claude planner에게 최상위 요청 생성, 작업별 실행, 자동 루프 시작
- Events: 에이전트별 작업 로그 확인

Work에서 만든 요청은 상세 설명 템플릿으로 저장됩니다. Linear가 설정되어 있고 `ECC_AUTO_SYNC_LINEAR=true`이면 UI/MCP에서 만든 요청은 Linear에도 바로 생성됩니다. planner가 하위 업무를 나눌 때도 `Goal`, `Context`, `Deliverables`, `Acceptance Criteria`, `Suggested Verification`을 포함하고 `--parent-task <planner-task-id> --sync-linear`로 Linear에 sub-issue로 남기도록 지시됩니다.

기본 실행은 토큰을 아끼기 위해 compact prompt 모드(`ECC_COMPACT_PROMPTS=true`)를 사용합니다. CLI에는 짧은 실행 지시와 context 파일 경로만 전달하고, 긴 task body는 `.ecc/contexts/`에 저장합니다. 전체 프롬프트를 그대로 넘기고 싶을 때만 `.env`에서 `ECC_COMPACT_PROMPTS=false`로 바꾸세요.

UI의 Work 탭에서는 `Create + Run`을 쓰면 됩니다. 이 버튼은 하나의 프롬프트로 planner task를 만들고, planner를 한 번 실행한 뒤 worker auto loop를 시작합니다. worker loop 반복 횟수와 간격은 `ECC_AUTO_LOOP_CYCLES`, `ECC_AUTO_LOOP_INTERVAL`로 조절합니다.

PM/planner는 프로젝트 방향이 바뀌는 요청을 받으면 `docs/ecc/plan.md`, `docs/ecc/design.md`, `docs/ecc/decisions.md`를 만들거나 갱신하도록 지시됩니다. 각 agent에는 `modelPolicy`가 있어 planner는 기획/설계/최종 결정에만 강한 모델을 쓰고, worker는 빠르고 저렴한 모델을 기본으로 쓰도록 안내합니다. 실제 모델 플래그는 각 CLI마다 다르므로 `.env`의 `ECC_PLANNER_COMMAND`, `ECC_CODEX_COMMAND`, `ECC_CLAUDE_CODE_COMMAND`에서 조절하세요.

회의록은 `python ecc.py meeting digest` 또는 UI의 Meetings 탭에서 만들 수 있습니다. digest에는 agent별 기여, 결정과 근거, blocker, 완료 결과, 다음 액션이 포함됩니다. 생성된 meeting은 기존 Notion sync 명령으로 Notion에 올릴 수 있습니다.

국가 언어는 `ECC_LOCALE`로 지정합니다. 현재 기본 지원은 `en`, `ko`입니다. 이 값은 UI 라벨, task description 섹션, planner 출력 언어 지시, 회의록 digest 언어에 적용됩니다.

## 6. 작업 만들기

```bash
python ecc.py task create --title "로그인 API 수정" --body "실패 케이스 재현 후 테스트와 수정 추가"
```

사용자 요청을 메인 Claude planner에게 보내려면:

```bash
python ecc.py request --goal "회원가입/로그인 기능을 기획하고 역할별 작업으로 나눠줘" --sync-linear
```

Windows 터미널에서 한글이 깨지면 UTF-8 파일을 사용하세요.

```bash
python ecc.py request --goal-file docs/request.md --sync-linear
```

configured agent 목록 확인:

```bash
python ecc.py agents
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

이 명령은 열린 작업을 configured agent에 분배하고, 각 CLI를 실행합니다. 각 CLI는 자기 역할 설정대로 작업하고 `.ecc`에 진행 로그를 남깁니다.
agent CLI 출력은 현재 터미널에 그대로 표시됩니다.

여러 에이전트가 무엇을 하는지 한 화면에서 보고 싶으면 다른 터미널/cmd 창에서 멀티 뷰를 켭니다.

```bash
python ecc.py watch
```

보고 싶은 에이전트만 고를 수도 있습니다.

```bash
python ecc.py watch --agents planner,codex,claude-code
```

`watch`는 `.ecc/tasks.jsonl`과 `.ecc/events.jsonl`을 읽어서 에이전트별 task와 진행 로그를 계속 갱신합니다. 실제 작업 실행은 별도 터미널에서 `python ecc.py auto ...`로 돌리고, 관제 화면은 `watch`로 보는 방식입니다.

특정 작업만 실행하려면:

```bash
python ecc.py auto --task task-xxxxxxxx --agents planner --max-cycles 1
```

CLI가 인증, 토큰, quota, rate limit, context limit, budget 문제로 실패하면 터미널 출력에 원인이 보이고 task는 `blocked`로 남습니다. 하네스는 출력의 마지막 부분을 자동 분류해서 `blocker_type`에 `quota_exhausted`, `rate_limited`, `context_limited`, `auth_required`, `token_budget` 같은 값을 기록합니다. UI의 Work 탭에도 blocker 배지가 표시되므로, 해결 후 다시 `python ecc.py auto --task ...`로 이어가면 됩니다.

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
ecc_agents.json
```

커밋하지 말 것:

```text
.env
.ecc/*.jsonl
```

`.env`에는 토큰이 들어가고, `.ecc/*.jsonl`에는 런타임 작업 로그가 들어갑니다.
