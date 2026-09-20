const state = {
  rooms: [],
  room: null,
  eventIds: new Set(),
  socket: null,
  reconnectTimer: null,
  profiles: null,
  followTranscript: true,
};

const $ = (selector) => document.querySelector(selector);
const views = [$("#welcome-view"), $("#create-view"), $("#room-view")];
const agentFallbackNames = { agent_a: "Agent A", agent_b: "Agent B", agent_c: "Agent C" };

function observerDraftKey(roomId) {
  return `codex-room:observer-draft:${roomId}`;
}

function loadObserverDraft(roomId) {
  try {
    const raw = localStorage.getItem(observerDraftKey(roomId));
    if (!raw) return null;
    const draft = JSON.parse(raw);
    if (typeof draft?.content !== "string" || typeof draft?.target !== "string") return null;
    return draft;
  } catch (_) {
    return null;
  }
}

function saveObserverDraft() {
  if (!state.room) return;
  const form = $("#message-form");
  const draft = {
    content: form.elements.content.value,
    target: form.elements.target.value,
  };
  try {
    localStorage.setItem(observerDraftKey(state.room.id), JSON.stringify(draft));
  } catch (_) { /* local persistence is best-effort */ }
}

function clearObserverDraft(roomId) {
  if (!roomId) return;
  try {
    localStorage.removeItem(observerDraftKey(roomId));
  } catch (_) { /* local persistence is best-effort */ }
}

function resizeObserverComposer() {
  const textarea = $("#message-form textarea");
  textarea.style.height = "auto";
  textarea.style.height = `${textarea.scrollHeight}px`;
}

function restoreObserverDraft(roomId) {
  const form = $("#message-form");
  const draft = loadObserverDraft(roomId);
  form.elements.content.value = draft?.content || "";
  form.elements.target.value = "all";
  if (draft?.target && [...form.elements.target.options].some((option) => option.value === draft.target)) {
    form.elements.target.value = draft.target;
  }
  resizeObserverComposer();
}

function focusObserverComposer() {
  $("#message-form textarea").focus({ preventScroll: true });
}

function principalConsultationAnswered(eventId) {
  return (state.room?.events || []).some(
    (event) => event.event_type === "principal_reply" && event.related_event_id === eventId,
  );
}

function markPrincipalConsultationAnswered(eventId) {
  if (!eventId) return;
  const article = document.querySelector(`.event[data-event-id="${eventId}"]`);
  if (!article) return;
  article.querySelector(".principal-reply-form")?.remove();
  if (!article.querySelector(".principal-reply-status")) {
    const status = document.createElement("small");
    status.className = "principal-reply-status";
    status.textContent = "Private reply recorded";
    article.querySelector(".event-body")?.append(status);
  }
}

function buildPrincipalReplyForm(event) {
  const form = document.createElement("form");
  form.className = "principal-reply-form";
  const requestedCeiling = event.metadata?.requested_task_cognition_ceiling;

  if (requestedCeiling) {
    const approvalLabel = document.createElement("strong");
    approvalLabel.textContent = `Task cognition request: ${requestedCeiling}`;
    const approve = document.createElement("button");
    approve.type = "button";
    approve.className = "control primary";
    approve.textContent = "Approve for this Task";
    const decline = document.createElement("button");
    decline.type = "button";
    decline.className = "control";
    decline.textContent = "Decline";
    const hint = document.createElement("small");
    hint.textContent = "Private · approval applies only to Agent C and expires when this Task ends";
    form.append(approvalLabel, approve, decline, hint);

    const sendDecision = async (decision) => {
      if (!state.room || !["running", "paused"].includes(state.room.status)) {
        showRoomError("This principal consultation is no longer open.");
        return;
      }
      approve.disabled = true;
      decline.disabled = true;
      const approved = decision === "approve";
      try {
        await api(`/api/rooms/${state.room.id}/principal-replies`, {
          method: "POST",
          body: JSON.stringify({
            consultation_event_id: event.id,
            content: approved
              ? `Approved ${requestedCeiling} for this Task.`
              : `Declined ${requestedCeiling} for this Task.`,
            cognition_approval: decision,
          }),
        });
        form.replaceWith(Object.assign(document.createElement("small"), {
          className: "principal-reply-status",
          textContent: approved ? "Task cognition escalation approved" : "Task cognition escalation declined",
        }));
      } catch (error) {
        showRoomError(error.message);
        approve.disabled = false;
        decline.disabled = false;
      }
    };
    approve.addEventListener("click", () => sendDecision("approve"));
    decline.addEventListener("click", () => sendDecision("decline"));
    return form;
  }

  const textarea = document.createElement("textarea");
  textarea.rows = 2;
  textarea.maxLength = 50000;
  textarea.required = true;
  textarea.placeholder = "Reply privately to Agent C…";
  textarea.setAttribute("aria-label", "Private reply to Agent C");
  const button = document.createElement("button");
  button.type = "submit";
  button.className = "control primary";
  button.textContent = "Reply privately";
  const hint = document.createElement("small");
  hint.textContent = "Only you and Agent C · Enter to send · Shift+Enter for newline";
  form.append(textarea, button, hint);

  form.addEventListener("submit", async (submitEvent) => {
    submitEvent.preventDefault();
    if (!state.room || !["running", "paused"].includes(state.room.status)) {
      showRoomError("This principal consultation is no longer open.");
      return;
    }
    button.disabled = true;
    try {
      await api(`/api/rooms/${state.room.id}/principal-replies`, {
        method: "POST",
        body: JSON.stringify({
          consultation_event_id: event.id,
          content: textarea.value,
        }),
      });
      form.replaceWith(Object.assign(document.createElement("small"), {
        className: "principal-reply-status",
        textContent: "Private reply sent",
      }));
    } catch (error) {
      showRoomError(error.message);
      button.disabled = false;
    }
  });

  textarea.addEventListener("keydown", (keyEvent) => {
    if (keyEvent.key !== "Enter" || keyEvent.isComposing || keyEvent.shiftKey) return;
    keyEvent.preventDefault();
    if (!button.disabled) form.requestSubmit();
  });
  return form;
}

function agentLetter(agentKey) {
  return agentKey.replace(/^agent_/, "").slice(0, 1).toLowerCase();
}

function agentName(agent) {
  return agent?.name || agentFallbackNames[agent?.agent_key] || agent?.agent_key || "Agent";
}

function executionSummary(execution) {
  if (!execution) return null;
  const label = (value, fallback) => String(value || fallback).replaceAll("_", " ");
  const phase = label(execution.phase, "unknown");
  const health = label(execution.health, "unknown");
  return {
    text: `Execution: ${phase} · ${health}`,
    title: execution.reason || "No additional execution-health detail is available.",
    healthClass: String(execution.health || "unknown").replace(/[^a-z0-9_-]/gi, "-"),
  };
}

function statusLabel(status) {
  return ({
    available: "Available",
    interaction_required: "Auth / interaction required",
    unavailable: "Disabled / unavailable",
    unknown: "Unknown / not inspectable",
  })[status] || String(status || "unknown").replaceAll("_", " ");
}

function compactNumber(value) {
  if (typeof value !== "number") return "—";
  return new Intl.NumberFormat().format(value);
}

function statusCard(title, status, summary, details = [], key = null) {
  const card = document.createElement("article");
  card.className = "status-card";
  if (key) card.dataset.statusTool = key;
  const head = document.createElement("div");
  head.className = "status-card-head";
  const strong = document.createElement("strong");
  strong.textContent = title;
  head.append(strong);
  if (status) {
    const badge = document.createElement("span");
    badge.className = `status-badge ${status}`;
    badge.textContent = statusLabel(status);
    head.append(badge);
  }
  card.append(head);
  if (summary) {
    const paragraph = document.createElement("p");
    paragraph.textContent = summary;
    card.append(paragraph);
  }
  if (details.length) {
    const list = document.createElement("div");
    list.className = "status-list";
    details.forEach(([label, value]) => {
      const row = document.createElement("div");
      row.className = "status-list-row";
      const left = document.createElement("span");
      left.textContent = label;
      const right = document.createElement("span");
      right.textContent = value ?? "—";
      row.append(left, right);
      list.append(row);
    });
    card.append(list);
  }
  return card;
}

function statusSection(title) {
  const section = document.createElement("section");
  section.className = "status-section";
  const heading = document.createElement("h3");
  heading.textContent = title;
  section.append(heading);
  return section;
}

function statusGrid() {
  const grid = document.createElement("div");
  grid.className = "status-grid";
  return grid;
}

function renderStatusTools(payload) {
  const root = $("#status-tools-content");
  root.replaceChildren();
  const work = payload.work || {};
  const round = work.round;
  const task = work.task;

  const current = statusSection("Current work");
  if (round?.objective) {
    const objective = document.createElement("p");
    objective.className = "status-section-note";
    objective.textContent = round.objective;
    current.append(objective);
  }
  const workGrid = statusGrid();
  workGrid.append(statusCard(
    "Round",
    null,
    round ? (round.title || "Untitled round") : "No active round",
    round ? [
      ["State", round.status || "—"],
      ["Completion", String(round.completion_policy || "—").replaceAll("_", " ")],
      ["Turns", compactNumber(round.turn_count)],
    ] : [],
  ));
  workGrid.append(statusCard(
    "Task",
    null,
    task ? "Current bounded objective state" : "No transaction Task exists yet.",
    task ? [
      ["State", task.state || "—"],
      ["C ceiling", task.c_cognition_ceiling || "—"],
      ["Assignments", String(task.assignments?.length || 0)],
    ] : [],
  ));
  current.append(workGrid);
  if (task?.assignments?.length) {
    const assignments = statusGrid();
    task.assignments.forEach((assignment) => {
      const label = agentFallbackNames[assignment.agent_key] || assignment.agent_key || "Agent";
      assignments.append(statusCard(
        `${label} assignment`,
        null,
        assignment.instruction || "No instruction summary available.",
        [["State", assignment.state || "—"]],
      ));
    });
    current.append(assignments);
  }
  root.append(current);

  const agentsSection = statusSection("Agents & economics");
  const agentGrid = statusGrid();
  (work.agents || []).forEach((agent) => {
    const economics = work.recent_economics?.[agent.agent_key];
    const tokens = economics?.usage_delta?.total_tokens;
    agentGrid.append(statusCard(
      agent.name || agentFallbackNames[agent.agent_key] || agent.agent_key,
      null,
      `${String(agent.work_state || agent.status || "unknown").replaceAll("_", " ")} · ${String(agent.execution_health || "health unknown").replaceAll("_", " ")} · ${agent.model || "model not run yet"}${agent.reasoning_effort ? ` · ${agent.reasoning_effort}` : ""}`,
      [
        ["Model evidence", agent.model_recency || "not recorded"],
        ["Queued / processing", `${agent.pending_count || 0} / ${agent.processing_count || 0}`],
        ["Recent execution tokens", compactNumber(tokens)],
        ["Recent tool calls", compactNumber(economics?.tool_calls)],
      ],
    ));
  });
  const context = work.coordinator_context;
  if (context) {
    agentGrid.append(statusCard(
      "C context guidance",
      null,
      `Refresh guidance: ${String(context.guidance_level || "unknown").replaceAll("_", " ")}`,
      [
        ["Executions on context", compactNumber(context.executions_on_context)],
        ["Last execution input", compactNumber(context.last_execution_input_tokens)],
        ["Cached input", compactNumber(context.last_execution_cached_input_tokens)],
        ["Consider refresh at", compactNumber(context.advisory_consider_input_tokens)],
        ["Strongly prefer at", compactNumber(context.advisory_strongly_prefer_input_tokens)],
      ],
    ));
  }
  agentsSection.append(agentGrid);
  root.append(agentsSection);

  const capabilities = statusSection("Room-native deterministic capabilities");
  const capabilityGrid = statusGrid();
  (payload.room_capabilities || []).forEach((capability) => {
    capabilityGrid.append(statusCard(
      capability.id || "Capability",
      "available",
      capability.description || "Registered deterministic capability.",
      [
        ["Origin", capability.origin || "—"],
        ["Scope", capability.scope || "—"],
        ["Version", capability.version || "—"],
      ],
    ));
  });
  if (!payload.room_capabilities?.length) {
    capabilityGrid.append(statusCard("Capabilities", "unavailable", "No Room-native deterministic capabilities were reported."));
  }
  capabilities.append(capabilityGrid);
  root.append(capabilities);

  const codexSection = statusSection("Inherited Codex surface");
  const runtime = payload.codex?.runtime || {};
  const runtimeNote = document.createElement("small");
  runtimeNote.textContent = `Runtime ${runtime.name || "Codex"} ${runtime.version || "version unknown"} · read-only inspection`;
  codexSection.append(runtimeNote);
  const toolGrid = statusGrid();
  const labels = {
    workspace_files: "Workspace files",
    command_execution: "Command execution",
    web_search: "Web search",
    skills: "Skills",
    mcp: "MCP",
    apps: "Apps / connectors",
    plugins: "Plugins",
  };
  Object.entries(labels).forEach(([key, label]) => {
    const category = payload.codex?.tools?.[key] || { status: "unknown", summary: "Not inspected." };
    const details = [];
    if (typeof category.total_count === "number") details.push(["Discovered", compactNumber(category.total_count)]);
    if (typeof category.enabled_count === "number") details.push(["Enabled", compactNumber(category.enabled_count)]);
    if (typeof category.available_count === "number") details.push(["Usable", compactNumber(category.available_count)]);
    if (typeof category.interaction_required_count === "number") details.push(["Needs auth", compactNumber(category.interaction_required_count)]);
    if (typeof category.callable_count === "number") details.push(["Callable", compactNumber(category.callable_count)]);
    if (category.mode) details.push(["Mode", category.mode]);
    (category.items || []).slice(0, 6).forEach((item) => {
      const suffix = item.tool_count != null
        ? `${item.tool_count} tool(s) · ${statusLabel(item.status)}`
        : item.scope
          ? `${item.scope} · ${item.enabled ? "enabled" : "disabled"}`
          : item.auth_policy
            ? `${statusLabel(item.status)} · auth ${item.auth_policy}`
            : statusLabel(item.status);
      details.push([item.name || "Item", suffix]);
    });
    if (category.truncated) details.push(["Inventory", "Additional items omitted from this compact view"]);
    toolGrid.append(statusCard(label, category.status, category.summary, details, key));
  });
  codexSection.append(toolGrid);
  root.append(codexSection);
}

async function loadStatusTools() {
  if (!state.room) return;
  const dialog = $("#status-tools-dialog");
  const root = $("#status-tools-content");
  const openButton = $("#status-tools-button");
  const refreshButton = $("#refresh-status-tools");
  if (!dialog.open) dialog.showModal();
  root.replaceChildren(Object.assign(document.createElement("div"), {
    className: "status-loading",
    textContent: "Inspecting current Room and Codex state…",
  }));
  openButton.disabled = true;
  refreshButton.disabled = true;
  try {
    const payload = await api(`/api/rooms/${state.room.id}/status-tools`);
    renderStatusTools(payload);
  } catch (error) {
    root.replaceChildren(Object.assign(document.createElement("div"), {
      className: "error-banner",
      textContent: error.message,
    }));
  } finally {
    openButton.disabled = false;
    refreshButton.disabled = false;
  }
}

function isConversationalEvent(event) {
  return event.event_class === "conversation" || [
    "observer_message", "round_start_turn", "topic", "agent_message", "agent_pass",
    "agent_finish", "agent_reopened",
  ].includes(event.event_type);
}

function mergeEvents(...sources) {
  const merged = new Map();
  sources.flat().forEach((event) => merged.set(event.id, event));
  return [...merged.values()].sort((left, right) =>
    (left.sequence_no ?? Number.MAX_SAFE_INTEGER) - (right.sequence_no ?? Number.MAX_SAFE_INTEGER));
}

function showView(view) {
  views.forEach((element) => element.classList.toggle("hidden", element !== view));
}

function restoreDefaults(which = "all") {
  const form = $("#create-form");
  if (which === "all" || which === "a") form.elements.agent_a_instructions.value = "";
  if (which === "all" || which === "b") form.elements.agent_b_instructions.value = "";
  if (which === "all" || which === "c") form.elements.agent_c_instructions.value = "";
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try { detail = (await response.json()).detail || detail; } catch (_) { /* noop */ }
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

async function checkHealth() {
  try {
    const health = await api("/api/health");
    $("#health-dot").className = "dot ok";
    $("#health-title").textContent = "Codex connected";
    $("#health-detail").textContent = health.codex.authenticated ? "Local authentication ready" : "Authentication needed";
  } catch (error) {
    $("#health-dot").className = "dot bad";
    $("#health-title").textContent = "Codex unavailable";
    $("#health-detail").textContent = error.message;
  }
}

async function loadRooms() {
  const include = $("#show-archived").checked;
  state.rooms = await api(`/api/rooms?include_archived=${include}`);
  renderRoomList();
  if (!state.room && !location.hash) showView(state.rooms.length ? $("#welcome-view") : $("#welcome-view"));
}

async function loadProfiles() {
  state.profiles = await api("/api/profiles/defaults");
  $("#agent-a-profile-hint").textContent = `Using saved personality: ${state.profiles.agent_a.name}`;
  $("#agent-b-profile-hint").textContent = `Using saved personality: ${state.profiles.agent_b.name}`;
  $("#agent-c-profile-hint").textContent = `Using saved personality: ${state.profiles.agent_c.name}`;
  return state.profiles;
}

function renderRoomList() {
  const list = $("#room-list");
  list.replaceChildren();
  for (const room of state.rooms) {
    const button = document.createElement("button");
    button.className = room.id === state.room?.id ? "active" : "";
    const strong = document.createElement("strong");
    strong.textContent = room.title;
    const small = document.createElement("small");
    const dot = document.createElement("i");
    dot.className = `mini-dot ${room.status}`;
    small.append(dot, document.createTextNode(`${room.status} · ${room.turn_count} turns`));
    button.append(strong, small);
    button.addEventListener("click", () => openRoom(room.id));
    list.append(button);
  }
}

function openCreate() {
  disconnectSocket();
  state.room = null;
  location.hash = "new";
  restoreDefaults();
  hideError("#create-error");
  showView($("#create-view"));
}

async function openRoom(roomId) {
  disconnectSocket();
  state.eventIds.clear();
  try {
    state.room = await api(`/api/rooms/${roomId}`);
    location.hash = `room=${roomId}`;
    showView($("#room-view"));
    renderRoom({ replaceTranscript: true });
    renderRoomList();
    restoreObserverDraft(roomId);
    focusObserverComposer();
    connectSocket(roomId);
  } catch (error) {
    showRoomError(error.message);
  }
}

function renderRoom({ replaceTranscript = false } = {}) {
  const room = state.room;
  if (!room) return;
  $("#room-title").textContent = room.title;
  $("#room-id").textContent = `Room ID ${room.id}`;
  $("#room-id").title = room.id;
  $("#room-status").textContent = room.status;
  $("#room-status").className = `status-pill ${room.status}`;
  const round = room.active_round;
  $("#round-summary").textContent = round
    ? `${round.title || "Untitled round"} · ${round.status} · ${round.turn_count} turns · starter ${round.starting_agent}${round.completion_policy === "continuous" ? " · continuous" : ""}`
    : "No active round";
  renderAgentStrip(room.agents || []);
  syncParticipantControls(room);
  $("#turn-counter").textContent = `${room.turn_count} / ${room.max_turns} turns`;
  $("#pause-room").disabled = room.status !== "running";
  $("#resume-room").disabled = !["paused", "stopped", "finished"].includes(room.status);
  $("#message-form").querySelector("button").disabled = !["running", "paused", "finished"].includes(room.status);
  $("#start-round").disabled = !round || round.status !== "preparing";
  if (replaceTranscript && room.events) renderTranscript(room.events);
}

function renderAgentStrip(agents) {
  const strip = $("#agent-strip");
  strip.replaceChildren();
  agents.forEach((agent, index) => {
    if (index) {
      const route = document.createElement("div");
      route.className = "route-line";
      route.setAttribute("aria-hidden", "true");
      route.innerHTML = "<i></i><span>routing</span><i></i>";
      strip.append(route);
    }
    const letter = agentLetter(agent.agent_key);
    const card = document.createElement("article");
    card.className = `agent-card agent-${letter}-card`;
    card.dataset.agentKey = agent.agent_key;
    const glyph = document.createElement("span");
    glyph.className = `agent-glyph ${letter}`;
    glyph.textContent = letter.toUpperCase();
    const info = document.createElement("div");
    info.className = "agent-info";
    const name = document.createElement("strong");
    name.textContent = agentName(agent);
    const threadEl = document.createElement("small");
    const thread = agent.thread_id || "not created";
    threadEl.textContent = `Thread ${thread}`;
    threadEl.title = thread;
    info.append(name, threadEl);
    const modelEl = document.createElement("small");
    modelEl.className = "model-state";
    const model = agent.execution?.model;
    const effort = agent.execution?.reasoning_effort;
    const recency = agent.execution?.model_recency;
    modelEl.textContent = model
      ? `Model ${model}${effort ? ` · ${effort}` : ""}`
      : "Model not run yet";
    modelEl.title = model
      ? `${recency === "current" ? "Current" : "Last"} execution model${effort ? ` · reasoning ${effort}` : ""}`
      : "This agent has not recorded a model execution yet.";
    info.append(modelEl);
    const execution = executionSummary(agent.execution);
    if (execution) {
      const executionEl = document.createElement("small");
      executionEl.className = `execution-state ${execution.healthClass}`;
      executionEl.textContent = execution.text;
      executionEl.title = execution.title;
      executionEl.setAttribute("aria-label", `${execution.text}. ${execution.title}`);
      info.append(executionEl);
    }
    const statusEl = document.createElement("span");
    statusEl.className = `agent-state ${agent.status}`;
    statusEl.replaceChildren(
      document.createElement("i"),
      document.createTextNode(` ${agent.status.replaceAll("_", " ")}`),
    );
    card.append(glyph, info, statusEl);
    strip.append(card);
  });
}

function syncParticipantControls(room) {
  const agents = room.agents || [];
  const hasC = agents.some((agent) => agent.agent_key === "agent_c");
  const addC = $("#add-agent-c");
  addC.classList.toggle("hidden", hasC);
  addC.disabled = room.status === "archived";

  const target = $("#message-form select[name=target]");
  const previousTarget = target.value;
  target.replaceChildren(new Option("All agents", "all"));
  agents.forEach((agent) => target.append(new Option(`${agentName(agent)} · private delivery`, agent.agent_key)));
  target.value = [...target.options].some((option) => option.value === previousTarget) ? previousTarget : "all";

  document.querySelectorAll(".agent-c-round-field").forEach((field) => {
    field.classList.toggle("hidden", !hasC);
    field.querySelectorAll("textarea").forEach((input) => { input.disabled = !hasC; });
  });
  const starter = $("#round-form select[name=starting_agent]");
  const previousStarter = starter.value;
  starter.replaceChildren();
  agents.forEach((agent) => starter.append(new Option(agentName(agent), agent.agent_key)));
  starter.append(new Option("All participants independently", "either"));
  starter.value = [...starter.options].some((option) => option.value === previousStarter)
    ? previousStarter
    : (hasC ? "agent_c" : agents[0]?.agent_key || "either");
}

function renderTranscript(events) {
  const transcript = $("#transcript");
  transcript.replaceChildren();
  state.eventIds.clear();
  if (!events.length) {
    const empty = document.createElement("div");
    empty.className = "empty-transcript";
    empty.textContent = "The Room is ready. Events will appear here as they are routed.";
    transcript.append(empty);
  } else {
    events.forEach(appendEvent);
  }
  const previousScrollBehavior = transcript.style.scrollBehavior;
  transcript.style.scrollBehavior = "auto";
  transcript.scrollTop = transcript.scrollHeight;
  transcript.style.scrollBehavior = previousScrollBehavior;
  state.followTranscript = true;
}

function reconcileTranscript(events) {
  const transcript = $("#transcript");
  if (!events?.length) return;
  const oldScrollTop = transcript.scrollTop;
  const anchor = [...transcript.querySelectorAll(".event")]
    .find((node) => node.offsetTop + node.offsetHeight >= oldScrollTop);
  const anchorOffset = anchor ? anchor.offsetTop - oldScrollTop : null;
  const existing = new Map(
    [...transcript.querySelectorAll(".event[data-event-id]")].map((node) => [node.dataset.eventId, node]),
  );
  const hasNewConversation = events.some(
    (event) => !existing.has(event.id) && isConversationalEvent(event),
  );

  let cursor = transcript.querySelector(".event");
  events.forEach((event) => {
    let node = existing.get(event.id);
    if (!node) node = appendEvent(event, { follow: false });
    if (node && node !== cursor && node.nextElementSibling !== cursor) {
      transcript.insertBefore(node, cursor);
    }
    cursor = node?.nextElementSibling || null;
  });

  const canonicalIds = new Set(events.map((event) => event.id));
  transcript.querySelectorAll(".event[data-event-id]").forEach((node) => {
    if (!canonicalIds.has(node.dataset.eventId)) node.remove();
  });
  state.eventIds = canonicalIds;
  if (state.followTranscript && hasNewConversation) transcript.scrollTop = transcript.scrollHeight;
  else if (anchor?.isConnected) transcript.scrollTop = anchor.offsetTop - anchorOffset;
  else transcript.scrollTop = oldScrollTop;
}

function appendEvent(event, { follow = true } = {}) {
  if (state.eventIds.has(event.id)) return;
  state.eventIds.add(event.id);
  $("#transcript .empty-transcript")?.remove();
  const transcript = $("#transcript");
  const names = Object.fromEntries((state.room?.agents || []).map((a) => [a.agent_key, a.name]));
  const speaker = names[event.source] || ({ observer: "Observer", room: "Room" }[event.source] || event.source);
  const article = document.createElement("article");
  article.dataset.eventId = event.id;
  const activity = ["agent_activity", "tool_activity"].includes(event.event_type);
  const system = event.source === "room" || ["error", "stale_result"].includes(event.event_type);
  const pass = event.event_type === "agent_pass";
  const attemptWarning = event.event_type === "agent_error" && event.metadata?.will_retry === true;
  const terminalError = event.event_type === "agent_error" && event.metadata?.will_retry !== true;
  const recovery = event.metadata?.retry_recovery;
  article.className = `event ${event.source} ${activity ? "activity" : ""} ${system ? "system" : ""} ${pass ? "pass" : ""} ${attemptWarning ? "attempt-warning" : ""} ${terminalError ? "terminal-error" : ""} ${recovery?.status === "recovered" ? "recovered" : ""}`;

  const rail = document.createElement("div");
  rail.className = "event-rail";
  const who = document.createElement("strong");
  who.textContent = speaker;
  const time = document.createElement("time");
  time.dateTime = event.created_at;
  time.textContent = new Date(event.created_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" });
  rail.append(who, time);

  const body = document.createElement("div");
  body.className = "event-body";
  const meta = document.createElement("div");
  meta.className = "event-meta";
  const type = document.createElement("span");
  type.className = "event-badge";
  type.textContent = attemptWarning ? "attempt warning" : (
    terminalError ? "agent error · recovery failed" : event.event_type.replaceAll("_", " ")
  );
  meta.append(type);
  if (recovery?.status === "recovered") {
    const recovered = document.createElement("span");
    recovered.className = "event-badge recovered";
    const count = recovery.attempt_failure_count || 1;
    recovered.textContent = `recovered after ${count} ${count === 1 ? "retry" : "retries"}`;
    meta.append(recovered);
  } else if (attemptWarning && event.metadata?.operator_state === "recovered") {
    const recovered = document.createElement("span");
    recovered.className = "event-badge recovered";
    recovered.textContent = "recovered";
    meta.append(recovered);
  }
  if (event.event_class) {
    const classification = document.createElement("span");
    classification.className = "event-badge";
    classification.textContent = event.event_class;
    meta.append(classification);
  }
  if ((event.metadata?.input_event_ids || []).length > 1) {
    const batch = document.createElement("span");
    batch.className = "event-badge";
    batch.textContent = `coalesced ${(event.metadata.input_event_ids).length} inputs`;
    meta.append(batch);
  }
  if (event.metadata?.private) {
    const badge = document.createElement("span");
    badge.className = "event-badge private";
    badge.textContent = event.metadata?.principal_channel
      ? (event.event_type === "principal_reply"
        ? "private · you → Agent C"
        : "private · Agent C → you")
      : `private · only ${names[event.destination] || event.destination} received`;
    meta.append(badge);
  }
  const text = document.createElement("p");
  text.textContent = event.content || (pass ? "Passed without sending a message." : "No message text.");
  body.append(meta, text);
  if (event.event_type === "principal_message" && event.metadata?.principal_channel) {
    article.classList.add("principal-consultation");
    if (principalConsultationAnswered(event.id)) {
      const status = document.createElement("small");
      status.className = "principal-reply-status";
      status.textContent = "Private reply recorded";
      body.append(status);
    } else if (["running", "paused"].includes(state.room?.status)) {
      body.append(buildPrincipalReplyForm(event));
    } else {
      const status = document.createElement("small");
      status.className = "principal-reply-status";
      status.textContent = "Consultation closed with the Room lifecycle";
      body.append(status);
    }
  } else if (event.event_type === "principal_reply" && event.metadata?.principal_channel) {
    article.classList.add("principal-reply");
  }
  article.append(rail, body);
  transcript.append(article);
  if (event.event_type === "principal_reply") {
    markPrincipalConsultationAnswered(event.related_event_id);
  }
  if (follow && state.followTranscript && isConversationalEvent(event)) {
    transcript.scrollTop = transcript.scrollHeight;
  }
  return article;
}

function connectSocket(roomId) {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${location.host}/ws/rooms/${roomId}`);
  state.socket = socket;
  socket.onmessage = ({ data }) => {
    const payload = JSON.parse(data);
    if (payload.kind === "snapshot") {
      const previousEvents = state.room?.events || [];
      const snapshotEvents = payload.room.events || [];
      state.room = { ...payload.room, events: mergeEvents(previousEvents, snapshotEvents) };
      renderRoom();
      reconcileTranscript(state.room.events);
    } else if (payload.kind === "event") {
      state.room.events = [...(state.room.events || []), payload.event];
      appendEvent(payload.event);
    } else if (payload.kind === "state") {
      state.room = { ...state.room, ...payload.room, events: state.room.events };
      renderRoom();
      loadRooms().catch(() => {});
    }
  };
  socket.onclose = () => {
    if (state.room?.id === roomId) state.reconnectTimer = setTimeout(() => connectSocket(roomId), 1500);
  };
}

function disconnectSocket() {
  clearTimeout(state.reconnectTimer);
  if (state.socket) {
    state.socket.onclose = null;
    state.socket.close();
    state.socket = null;
  }
}

function showRoomError(message) {
  const el = $("#room-error");
  el.textContent = message;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 9000);
}

function hideError(selector) { $(selector).classList.add("hidden"); }

async function roomAction(action, body) {
  if (!state.room) return false;
  hideError("#room-error");
  try {
    const result = await api(`/api/rooms/${state.room.id}/${action}`, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
    if (result?.agents) {
      const previousEvents = state.room.events || [];
      const resultEvents = result.events || [];
      state.room = { ...result, events: mergeEvents(previousEvents, resultEvents) };
      renderRoom();
      reconcileTranscript(state.room.events);
    }
    return true;
  } catch (error) {
    showRoomError(error.message);
    return false;
  }
}

$("#new-room-button").addEventListener("click", openCreate);
$("#welcome-new-room").addEventListener("click", openCreate);
$("#cancel-create").addEventListener("click", () => { location.hash = ""; showView($("#welcome-view")); });
$("#show-archived").addEventListener("change", () => loadRooms().catch((e) => showRoomError(e.message)));
document.querySelectorAll(".restore-default").forEach((button) => button.addEventListener("click", () => restoreDefaults(button.dataset.agent)));
document.querySelectorAll(".close-dialog").forEach((button) => button.addEventListener("click", () => button.closest("dialog").close()));

$("#create-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const submit = form.querySelector("button[type=submit]");
  submit.disabled = true;
  hideError("#create-error");
  const values = Object.fromEntries(new FormData(form));
  if (!values.agent_a_instructions.trim()) delete values.agent_a_instructions;
  if (!values.agent_b_instructions.trim()) delete values.agent_b_instructions;
  if (!values.agent_c_instructions.trim()) delete values.agent_c_instructions;
  ["max_turns", "max_consecutive_passes", "inactivity_seconds"].forEach((key) => values[key] = Number(values[key]));
  try {
    const room = await api("/api/rooms", { method: "POST", body: JSON.stringify(values) });
    await loadRooms();
    await openRoom(room.id);
  } catch (error) {
    const banner = $("#create-error");
    banner.textContent = error.message;
    banner.classList.remove("hidden");
  } finally { submit.disabled = false; }
});

$("#message-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  const button = form.querySelector("button");
  const roomId = state.room?.id;
  button.disabled = true;
  try {
    if (await roomAction("messages", values)) {
      clearObserverDraft(roomId);
      if (state.room?.id === roomId) {
        form.elements.content.value = "";
        resizeObserverComposer();
        focusObserverComposer();
      }
    }
  } finally { button.disabled = false; }
});

$("#message-form textarea").addEventListener("input", () => {
  resizeObserverComposer();
  saveObserverDraft();
});
$("#message-form select[name=target]").addEventListener("change", saveObserverDraft);

$("#message-form textarea").addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.isComposing || event.shiftKey) return;
  event.preventDefault();
  const form = event.currentTarget.form;
  const submit = form.querySelector("button[type=submit]");
  if (!submit.disabled) form.requestSubmit();
});
$("#pause-room").addEventListener("click", () => roomAction("pause"));
$("#resume-room").addEventListener("click", () => roomAction("resume"));
$("#stop-room").addEventListener("click", () => { if (confirm("Stop this discussion and cancel queued deliveries?")) roomAction("stop"); });
$("#add-agent-c").addEventListener("click", async (event) => {
  if (!state.room || state.room.agents.some((agent) => agent.agent_key === "agent_c")) return;
  if (!confirm("Upgrade this historical two-agent Room to the permanent triad? A and B keep their existing thread identities. A fresh Agent C will join without receiving pre-join Room events.")) return;
  event.currentTarget.disabled = true;
  try {
    await roomAction("agents", { agent_key: "agent_c" });
  } finally {
    if (!state.room?.agents.some((agent) => agent.agent_key === "agent_c")) event.currentTarget.disabled = false;
  }
});
$("#reset-room").addEventListener("click", () => {
  const count = state.room?.agents.length || 0;
  if (confirm(`Replace all ${count} persistent Codex thread identities? Old thread IDs remain in the transcript.`)) roomAction("reset");
});
$("#archive-room").addEventListener("click", async () => {
  if (!state.room || !confirm(`Archive this Room and all ${state.room.agents.length} Codex threads?`)) return;
  if (!(await roomAction("archive"))) return;
  state.room = null; location.hash = ""; disconnectSocket(); await loadRooms(); showView($("#welcome-view"));
});
$("#export-md").addEventListener("click", () => { if (state.room) location.href = `/api/rooms/${state.room.id}/export?format=markdown`; });
$("#export-json").addEventListener("click", () => { if (state.room) location.href = `/api/rooms/${state.room.id}/export?format=json`; });
$("#status-tools-button").addEventListener("click", () => loadStatusTools());
$("#refresh-status-tools").addEventListener("click", () => loadStatusTools());
$("#new-round").addEventListener("click", () => {
  if (state.room) {
    syncParticipantControls(state.room);
    const agents = state.room.agents || [];
    const starter = $("#round-form select[name=starting_agent]");
    starter.value = agents.some((agent) => agent.agent_key === "agent_c")
      ? "agent_c"
      : agents[0]?.agent_key || "either";
  }
  $("#round-dialog").showModal();
});
$("#start-round").addEventListener("click", async () => {
  const round = state.room?.active_round;
  if (round?.status === "preparing") await roomAction(`rounds/${round.id}/start`);
});
$("#round-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  if (!values.prompt.trim()) return;
  for (const key of ["title", "task_overlay"]) {
    if (!values[key]?.trim()) delete values[key];
  }
  const participantPrivate = {};
  const participantOverlays = {};
  for (const agent of state.room?.agents || []) {
    const privateKey = `${agent.agent_key}_private`;
    const overlayKey = `${agent.agent_key}_overlay`;
    if (values[privateKey]?.trim()) participantPrivate[agent.agent_key] = values[privateKey].trim();
    if (values[overlayKey]?.trim()) participantOverlays[agent.agent_key] = values[overlayKey].trim();
    delete values[privateKey];
    delete values[overlayKey];
  }
  if (Object.keys(participantPrivate).length) values.participant_private = participantPrivate;
  if (Object.keys(participantOverlays).length) values.participant_overlays = participantOverlays;
  if (await roomAction("rounds", values)) {
    $("#round-dialog").close();
    form.reset();
  }
});

$("#profiles-button").addEventListener("click", async () => {
  const profiles = await loadProfiles();
  const form = $("#profiles-form");
  form.elements.agent_a_name.value = profiles.agent_a.name;
  form.elements.agent_a_instructions.value = profiles.agent_a.developer_instructions;
  form.elements.agent_b_name.value = profiles.agent_b.name;
  form.elements.agent_b_instructions.value = profiles.agent_b.developer_instructions;
  form.elements.agent_c_name.value = profiles.agent_c.name;
  form.elements.agent_c_instructions.value = profiles.agent_c.developer_instructions;
  $("#profiles-dialog").showModal();
});
$("#profiles-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  state.profiles = await api("/api/profiles/defaults", {
    method: "PUT",
    body: JSON.stringify(Object.fromEntries(new FormData(form))),
  });
  $("#agent-a-profile-hint").textContent = `Using saved personality: ${state.profiles.agent_a.name}`;
  $("#agent-b-profile-hint").textContent = `Using saved personality: ${state.profiles.agent_b.name}`;
  $("#agent-c-profile-hint").textContent = `Using saved personality: ${state.profiles.agent_c.name}`;
  $("#profiles-dialog").close();
});

$("#transcript").addEventListener("scroll", (event) => {
  const transcript = event.currentTarget;
  state.followTranscript = transcript.scrollHeight - transcript.scrollTop - transcript.clientHeight < 100;
});

async function boot() {
  restoreDefaults();
  await Promise.all([checkHealth(), loadRooms(), loadProfiles()]);
  const match = location.hash.match(/^#room=(.+)$/);
  if (match) await openRoom(match[1]);
  else if (location.hash === "#new") openCreate();
  else showView($("#welcome-view"));
}

boot().catch((error) => {
  $("#health-dot").className = "dot bad";
  $("#health-title").textContent = "Startup error";
  $("#health-detail").textContent = error.message;
  showView($("#welcome-view"));
});
