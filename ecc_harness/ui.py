from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from config.settings import get_env, integration_status, load_environment

from .agent_config import list_agent_definitions, main_agent_id
from .env_file import read_env_file, write_env_values
from .i18n import locale, ui_messages
from .integrations import infer_github_repository, list_linear_projects
from .meetings import add_meeting_digest
from .runner import start_auto_process
from .store import EVENTS_FILE, list_tasks, read_jsonl
from .task_ops import create_planner_request, should_auto_sync_linear


ENV_FIELDS = (
    "GITHUB_TOKEN",
    "GITHUB_REPOSITORY",
    "LINEAR_API_KEY",
    "LINEAR_TEAM_ID",
    "LINEAR_PROJECT_ID",
    "NOTION_TOKEN",
    "NOTION_PARENT_PAGE_ID",
    "SLACK_BOT_TOKEN",
    "SLACK_TEAM_ID",
    "SLACK_DEFAULT_CHANNEL_ID",
    "ECC_PLANNER_COMMAND",
    "ECC_CODEX_COMMAND",
    "ECC_GEMINI_COMMAND",
    "ECC_CLAUDE_CODE_COMMAND",
    "ECC_AUTO_SYNC_LINEAR",
    "ECC_COMPACT_PROMPTS",
    "ECC_AUTO_LOOP_CYCLES",
    "ECC_AUTO_LOOP_INTERVAL",
    "ECC_LOCALE",
)


class EnvUpdate(BaseModel):
    values: dict[str, str]


class PlannerRequest(BaseModel):
    goal: str


class RunRequest(BaseModel):
    task_id: str = ""
    agents: str = ""
    dispatch: bool = False
    loop: bool = False


class MeetingDigestRequest(BaseModel):
    title: str = "ECC Agent Meeting Digest"
    task_id: str = ""


def create_app() -> FastAPI:
    load_environment()
    app = FastAPI(title="ECC Console")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return HTML

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> Response:
        return Response(status_code=204)

    @app.get("/api/state")
    def state() -> dict[str, Any]:
        load_environment()
        env_values = read_env_file()
        return {
            "integrations": integration_status(),
            "env": {field: {"set": bool(env_values.get(field) or get_env(field))} for field in ENV_FIELDS},
            "agents": [
                {
                    "id": agent.id,
                    "runner": agent.runner,
                    "role": agent.role,
                    "model_policy": agent.model_policy,
                    "command_env": agent.command_env,
                    "command": " ".join(agent.command),
                    "enabled": agent.enabled,
                    "optional": agent.optional,
                    "main": agent.id == main_agent_id(),
                }
                for agent in list_agent_definitions()
            ],
            "tasks": list_tasks(),
            "events": read_jsonl(EVENTS_FILE)[-100:],
            "github_repository": infer_github_repository(),
            "locale": locale(),
            "messages": ui_messages(),
        }

    @app.post("/api/env")
    def update_env(payload: EnvUpdate) -> dict[str, bool]:
        allowed = {key: value for key, value in payload.values.items() if key in ENV_FIELDS}
        write_env_values(allowed)
        load_environment()
        return {"ok": True}

    @app.post("/api/request")
    def request(payload: PlannerRequest) -> dict[str, Any]:
        goal = payload.goal.strip()
        if not goal:
            raise HTTPException(status_code=400, detail="Goal is required")
        return create_planner_request(goal, "ui-request", should_auto_sync_linear())

    @app.post("/api/launch")
    def launch(payload: PlannerRequest) -> dict[str, Any]:
        goal = payload.goal.strip()
        if not goal:
            raise HTTPException(status_code=400, detail="Goal is required")
        task = create_planner_request(goal, "ui-launch", should_auto_sync_linear())
        planner = start_auto_process(task["id"], main_agent_id(), False, False)
        workers = start_auto_process("", "", True, True)
        return {"task": task, "planner": planner, "workers": workers}

    @app.post("/api/run")
    def run(payload: RunRequest) -> dict[str, str]:
        if payload.task_id:
            task = next((item for item in list_tasks() if item["id"] == payload.task_id), None)
            if not task:
                raise HTTPException(status_code=404, detail="Unknown task id")
            agents = payload.agents or task.get("assignee", "")
        else:
            agents = payload.agents
        return start_auto_process(payload.task_id, agents, payload.dispatch, payload.loop)

    @app.post("/api/meeting/digest")
    def meeting_digest(payload: MeetingDigestRequest) -> dict[str, Any]:
        return add_meeting_digest(payload.title, payload.task_id, "ui")

    @app.get("/api/linear/projects")
    def linear_projects() -> dict[str, Any]:
        try:
            return {"ok": True, "projects": list_linear_projects()}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "projects": []}

    return app


HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ECC Console</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --surface: #ffffff;
      --surface-2: #eef1f4;
      --ink: #15191f;
      --muted: #64707d;
      --line: #d9dee5;
      --accent: #176b87;
      --accent-2: #2d7d46;
      --warn: #a86416;
      --bad: #b42318;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink); }
    header { height: 56px; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; border-bottom: 1px solid var(--line); background: var(--surface); }
    h1 { font-size: 18px; margin: 0; font-weight: 700; }
    h2 { font-size: 15px; margin: 0 0 12px; }
    main { display: grid; grid-template-columns: 280px 1fr; min-height: calc(100vh - 56px); }
    nav { border-right: 1px solid var(--line); background: var(--surface); padding: 18px; }
    nav button { width: 100%; height: 38px; border: 0; background: transparent; border-radius: 6px; text-align: left; padding: 0 12px; color: var(--muted); font-weight: 650; cursor: pointer; }
    nav button.active { color: var(--ink); background: var(--surface-2); }
    section { padding: 22px; display: none; }
    section.active { display: block; }
    .grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 14px; }
    .panel { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }
    .span-4 { grid-column: span 4; }
    .span-6 { grid-column: span 6; }
    .span-8 { grid-column: span 8; }
    .span-12 { grid-column: span 12; }
    label { display: block; color: var(--muted); font-size: 12px; font-weight: 700; margin: 10px 0 6px; }
    input, textarea, select { width: 100%; border: 1px solid var(--line); border-radius: 6px; background: #fff; color: var(--ink); padding: 10px 11px; font: inherit; }
    textarea { min-height: 140px; resize: vertical; }
    .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .btn { border: 1px solid var(--line); background: #fff; color: var(--ink); border-radius: 6px; height: 36px; padding: 0 12px; font-weight: 700; cursor: pointer; }
    .btn.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
    .btn.good { background: var(--accent-2); color: #fff; border-color: var(--accent-2); }
    .pill { display: inline-flex; align-items: center; height: 24px; border-radius: 999px; padding: 0 9px; font-size: 12px; font-weight: 800; border: 1px solid var(--line); color: var(--muted); }
    .pill.ready, .pill.enabled { color: var(--accent-2); border-color: #9ed2ad; background: #eef8f1; }
    .pill.missing, .pill.disabled { color: var(--bad); border-color: #f0b5ae; background: #fff0ee; }
    .pill.blocked { color: var(--bad); border-color: #f0b5ae; background: #fff0ee; }
    .pill.optional { color: var(--warn); border-color: #e7c991; background: #fff8eb; }
    .list { display: grid; gap: 10px; }
    .item { border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fff; }
    .item strong { display: block; font-size: 14px; margin-bottom: 4px; }
    .muted { color: var(--muted); font-size: 13px; }
    .mono { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 12px; }
    .event { display: grid; grid-template-columns: 110px 120px 1fr; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--line); }
    .event:last-child { border-bottom: 0; }
    @media (max-width: 900px) {
      main { grid-template-columns: 1fr; }
      nav { display: flex; gap: 8px; overflow-x: auto; border-right: 0; border-bottom: 1px solid var(--line); }
      nav button { min-width: 130px; }
      .span-4, .span-6, .span-8 { grid-column: span 12; }
    }
  </style>
</head>
<body>
  <header>
    <h1>ECC Console</h1>
    <div class="row"><span id="refreshState" class="pill">loading</span><button class="btn" onclick="loadState()" data-i18n="refresh">Refresh</button></div>
  </header>
  <main>
    <nav>
      <button class="active" data-tab="overview" data-i18n="overview">Overview</button>
      <button data-tab="setup" data-i18n="setup">Setup</button>
      <button data-tab="agents" data-i18n="agents">Agents</button>
      <button data-tab="work" data-i18n="work">Work</button>
      <button data-tab="events" data-i18n="events">Events</button>
      <button data-tab="meetings" data-i18n="meetings">Meetings</button>
    </nav>
    <section id="overview" class="active">
      <div class="grid">
        <div class="panel span-12"><h2 data-i18n="integration_status">Integration status</h2><div id="integrationCards" class="grid"></div></div>
        <div class="panel span-6"><h2 data-i18n="agents">Agents</h2><div id="agentSummary" class="list"></div></div>
        <div class="panel span-6"><h2 data-i18n="recent_work">Recent work</h2><div id="taskSummary" class="list"></div></div>
      </div>
    </section>
    <section id="setup">
      <div class="grid">
        <div class="panel span-8">
          <h2 data-i18n="setup">Setup</h2>
          <div id="envForm"></div>
          <div class="row" style="margin-top:14px"><button class="btn primary" onclick="saveEnv()" data-i18n="save">Save</button><button class="btn" onclick="loadLinearProjects()" data-i18n="load_linear_projects">Load Linear projects</button></div>
        </div>
        <div class="panel span-4"><h2 data-i18n="linear_projects">Linear Projects</h2><div id="linearProjects" class="list"><p class="muted" data-i18n="linear_help">Save a Linear API key first.</p></div></div>
      </div>
    </section>
    <section id="agents"><div class="panel"><h2 data-i18n="agent_roster">Agent roster</h2><div id="agentList" class="list"></div></div></section>
    <section id="work">
      <div class="grid">
        <div class="panel span-6">
          <h2 data-i18n="one_prompt_control">One prompt control</h2>
          <textarea id="goal" placeholder="Describe the goal. The planner will split work and start the worker loop." data-i18n-placeholder="goal_placeholder"></textarea>
          <div class="row" style="margin-top:12px">
            <button class="btn good" onclick="launchOptimized()" data-i18n="create_run">Create + Run</button>
            <button class="btn primary" onclick="createPlannerRequest()" data-i18n="create_only">Create only</button>
            <button class="btn" onclick="startAutoLoop()" data-i18n="start_worker_loop">Start worker loop</button>
          </div>
          <p class="muted" data-i18n="create_run_help">Create + Run creates a planner task, starts the planner, then starts the dispatch loop for workers. Compact prompts are used by default.</p>
        </div>
        <div class="panel span-6"><h2 data-i18n="task_queue">Task queue</h2><div id="taskList" class="list"></div></div>
      </div>
    </section>
    <section id="events"><div class="panel"><h2 data-i18n="agent_events">Agent events</h2><div id="eventList"></div></div></section>
    <section id="meetings">
      <div class="panel">
        <h2 data-i18n="meeting_digest">Meeting digest</h2>
        <div class="row">
          <input id="meetingTitle" value="ECC Agent Meeting Digest" />
          <input id="meetingTask" placeholder="Optional task id scope" data-i18n-placeholder="meeting_task_placeholder" />
          <button class="btn primary" onclick="createMeetingDigest()" data-i18n="create_digest">Create digest</button>
        </div>
        <p class="muted" data-i18n="digest_help">Digest includes agent contributions, decisions, blockers, outcomes, and next actions. Sync the created meeting to Notion with the existing Notion sync flow.</p>
      </div>
    </section>
  </main>
  <script>
    const fields = ["GITHUB_TOKEN","GITHUB_REPOSITORY","LINEAR_API_KEY","LINEAR_TEAM_ID","LINEAR_PROJECT_ID","NOTION_TOKEN","NOTION_PARENT_PAGE_ID","SLACK_BOT_TOKEN","SLACK_TEAM_ID","SLACK_DEFAULT_CHANNEL_ID","ECC_PLANNER_COMMAND","ECC_CODEX_COMMAND","ECC_GEMINI_COMMAND","ECC_CLAUDE_CODE_COMMAND","ECC_AUTO_SYNC_LINEAR","ECC_COMPACT_PROMPTS","ECC_AUTO_LOOP_CYCLES","ECC_AUTO_LOOP_INTERVAL"];
    let state = {};
    function t(key) {
      return state.messages?.[key] || key;
    }
    document.querySelectorAll("nav button").forEach(button => {
      button.addEventListener("click", () => {
        document.querySelectorAll("nav button, section").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        document.getElementById(button.dataset.tab).classList.add("active");
      });
    });
    async function api(path, options) {
      const res = await fetch(path, options);
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    }
    async function loadState() {
      state = await api("/api/state");
      document.getElementById("refreshState").textContent = "live";
      render();
    }
    function render() {
      renderIntegrations();
      renderI18n();
      renderEnv();
      renderAgents();
      renderTasks();
      renderEvents();
    }
    function renderI18n() {
      document.documentElement.lang = state.locale || "en";
      document.querySelectorAll("[data-i18n]").forEach(item => { item.textContent = t(item.dataset.i18n); });
      document.querySelectorAll("[data-i18n-placeholder]").forEach(item => { item.placeholder = t(item.dataset.i18nPlaceholder); });
    }
    function renderIntegrations() {
      integrationCards.innerHTML = state.integrations.map(item => `<div class="item span-3"><div class="row"><strong>${item.name}</strong><span class="pill ${item.status}">${item.status}</span></div><div class="muted mono">${item.required}</div></div>`).join("");
    }
    function renderEnv() {
      envForm.innerHTML = fields.map(field => {
        const badge = state.env[field]?.set ? '<span class="pill ready">set</span>' : '';
        if (field === "ECC_LOCALE") {
          return `<label>${field} ${badge}</label><select data-env="${field}"><option value="en" ${state.locale === "en" ? "selected" : ""}>English</option><option value="ko" ${state.locale === "ko" ? "selected" : ""}>\uD55C\uAD6D\uC5B4</option></select>`;
        }
        const type = field.includes('TOKEN') || field.includes('KEY') ? 'password' : 'text';
        const placeholder = state.env[field]?.set ? t('saved_placeholder') : '';
        return `<label>${field} ${badge}</label><input data-env="${field}" type="${type}" placeholder="${placeholder}" />`;
      }).join("");
    }
    function renderAgents() {
      const html = state.agents.map(agent => `<div class="item"><div class="row"><strong>${agent.id}</strong><span class="pill ${agent.enabled ? 'enabled' : 'disabled'}">${agent.enabled ? 'enabled' : 'disabled'}</span>${agent.optional ? '<span class="pill optional">optional</span>' : ''}${agent.main ? '<span class="pill ready">main</span>' : ''}</div><div class="muted">${agent.role}</div><div class="muted">${agent.model_policy || ''}</div><div class="muted mono">${agent.command || 'no command configured'}</div></div>`).join("");
      agentList.innerHTML = html;
      agentSummary.innerHTML = html;
    }
    function renderTasks() {
      const tasks = [...state.tasks].reverse();
      const html = tasks.map(task => {
        const blocker = task.blocker_type ? `<span class="pill blocked">${task.blocker_type}</span>` : '';
        return `<div class="item"><div class="row"><strong>${task.title}</strong><span class="pill">${task.status}</span>${blocker}<span class="pill">${task.assignee || 'unassigned'}</span>${task.status === 'done' ? '' : `<button class="btn" onclick="runTask('${task.id}')">${t('run')}</button>`}</div><div class="muted mono">${task.id}</div><div class="muted">${task.summary || task.body || ''}</div></div>`;
      }).join("") || `<p class="muted">${t('no_tasks')}</p>`;
      taskList.innerHTML = html;
      taskSummary.innerHTML = tasks.slice(0, 5).map(task => `<div class="item"><strong>${task.title}</strong><div class="muted">${task.status} - ${task.assignee || 'unassigned'}</div></div>`).join("") || `<p class="muted">${t('no_tasks')}</p>`;
    }
    function renderEvents() {
      eventList.innerHTML = [...state.events].reverse().map(event => `<div class="event"><span class="mono">${event.agent}</span><span class="mono">${event.action}</span><span>${event.message}<div class="muted mono">${event.task_id || ''}</div></span></div>`).join("") || `<p class="muted">${t('no_events')}</p>`;
    }
    async function saveEnv() {
      const values = {};
      document.querySelectorAll("[data-env]").forEach(input => { if (input.value.trim()) values[input.dataset.env] = input.value.trim(); });
      await api("/api/env", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({values}) });
      await loadState();
    }
    async function createPlannerRequest() {
      const goal = document.getElementById("goal").value.trim();
      if (!goal) return;
      await api("/api/request", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({goal}) });
      document.getElementById("goal").value = "";
      await loadState();
    }
    async function launchOptimized() {
      const goal = document.getElementById("goal").value.trim();
      if (!goal) return;
      await api("/api/launch", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({goal}) });
      document.getElementById("goal").value = "";
      await loadState();
    }
    async function runTask(taskId) {
      await api("/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({task_id: taskId}) });
      await loadState();
    }
    async function startAutoLoop() {
      await api("/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({dispatch: true, loop: true}) });
      await loadState();
    }
    async function createMeetingDigest() {
      await api("/api/meeting/digest", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({title: document.getElementById("meetingTitle").value, task_id: document.getElementById("meetingTask").value})
      });
      await loadState();
    }
    async function loadLinearProjects() {
      const data = await api("/api/linear/projects");
      linearProjects.innerHTML = data.ok ? data.projects.map(project => `<div class="item"><strong>${project.name}</strong><div class="muted mono">${project.id}</div></div>`).join("") : `<p class="muted">${data.error}</p>`;
    }
    loadState();
    setInterval(loadState, 5000);
  </script>
</body>
</html>
"""


app = create_app()
