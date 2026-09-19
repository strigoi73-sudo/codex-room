const fs = require('node:fs');
const path = require('node:path');
const { test, expect } = require('@playwright/test');

const staticRoot = path.join(__dirname, '..', 'codex_room', 'static');
const indexHtml = fs.readFileSync(path.join(staticRoot, 'index.html'), 'utf8');
const appJavaScript = fs.readFileSync(path.join(staticRoot, 'app.js'), 'utf8');
const styles = fs.readFileSync(path.join(staticRoot, 'styles.css'), 'utf8');

test.use({ channel: process.env.ROOM_TEST_CHANNEL || 'chrome', viewport: { width: 1440, height: 900 } });

const roomId = 'room_transcript_stability';

function makeEvent(sequence, overrides = {}) {
  const source = sequence % 4 === 0 ? 'observer' : `agent_${['a', 'b', 'c'][sequence % 3]}`;
  return {
    id: `event_${String(sequence).padStart(5, '0')}`,
    sequence_no: sequence,
    source,
    event_type: source === 'observer' ? 'observer_message' : 'agent_message',
    event_class: 'conversation',
    content: `Transcript event ${sequence}. ${'Stable long-room history content. '.repeat(3)}`,
    created_at: new Date(Date.UTC(2026, 8, 1, 12, 0, sequence % 60)).toISOString(),
    ...overrides,
  };
}

function makeRoom(events, id = roomId, title = 'Large transcript stability fixture') {
  return {
    id,
    title,
    status: 'running',
    turn_count: 321,
    max_turns: 500,
    active_round: {
      id: 'round_fixture', title: 'Transcript fixture', status: 'running',
      turn_count: 23, starting_agent: 'either',
    },
    agents: ['a', 'b', 'c'].map((letter) => ({
      agent_key: `agent_${letter}`,
      name: `Agent ${letter.toUpperCase()}`,
      thread_id: `thread-${letter}`,
      status: 'idle',
      execution: { phase: 'idle', health: 'healthy', reason: 'No queued or active work.' },
    })),
    events,
  };
}

async function openFixture(page, initialRoom, additionalRooms = []) {
  const observerMessages = [];
  const principalReplies = [];
  const rooms = [initialRoom, ...additionalRooms];
  await page.addInitScript(() => {
    window.__roomSockets = [];
    class MockWebSocket {
      constructor(url) {
        this.url = url;
        this.readyState = 1;
        window.__roomSockets.push(this);
        queueMicrotask(() => this.onopen?.({}));
      }
      close() { this.readyState = 3; }
      send() {}
      emit(payload) { this.onmessage?.({ data: JSON.stringify(payload) }); }
      drop() {
        this.readyState = 3;
        this.onclose?.({ code: 1006, reason: 'fixture reconnect' });
      }
    }
    Object.defineProperty(window, 'WebSocket', { configurable: true, value: MockWebSocket });
  });

  await page.route('http://room.test/**', async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === '/') return route.fulfill({ contentType: 'text/html', body: indexHtml });
    if (pathname === '/app.js') return route.fulfill({ contentType: 'text/javascript', body: appJavaScript });
    if (pathname === '/styles.css') return route.fulfill({ contentType: 'text/css', body: styles });
    if (pathname === '/api/health') {
      return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ codex: { authenticated: true } }) });
    }
    if (pathname === '/api/profiles/defaults') {
      const profiles = Object.fromEntries(['a', 'b', 'c'].map((letter) => [
        `agent_${letter}`,
        { name: `Agent ${letter.toUpperCase()}`, developer_instructions: `Fixture ${letter}` },
      ]));
      return route.fulfill({ contentType: 'application/json', body: JSON.stringify(profiles) });
    }
    if (pathname === '/api/rooms') {
      return route.fulfill({ contentType: 'application/json', body: JSON.stringify(rooms) });
    }
    const detailRoom = rooms.find((room) => pathname === `/api/rooms/${room.id}`);
    if (detailRoom) {
      return route.fulfill({ contentType: 'application/json', body: JSON.stringify(detailRoom) });
    }
    const messageRoom = rooms.find((room) => pathname === `/api/rooms/${room.id}/messages`);
    if (messageRoom && route.request().method() === 'POST') {
      observerMessages.push(JSON.parse(route.request().postData() || '{}'));
      return route.fulfill({ contentType: 'application/json', body: '{}' });
    }
    const principalReplyRoom = rooms.find(
      (room) => pathname === `/api/rooms/${room.id}/principal-replies`,
    );
    if (principalReplyRoom && route.request().method() === 'POST') {
      principalReplies.push(JSON.parse(route.request().postData() || '{}'));
      return route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'event_principal_reply_fixture',
          event_type: 'principal_reply',
          source: 'observer',
          destination: 'agent_c',
        }),
      });
    }
    return route.fulfill({ status: 404, contentType: 'application/json', body: '{"detail":"fixture route not found"}' });
  });

  await page.goto(`http://room.test/#room=${initialRoom.id}`);
  await expect(page.locator('#transcript .event')).toHaveCount(initialRoom.events.length);
  await expect.poll(() => page.locator('#transcript').evaluate((element) =>
    element.scrollHeight - element.scrollTop - element.clientHeight)).toBeLessThan(5);
  await page.locator('#transcript').evaluate((element) => { element.style.scrollBehavior = 'auto'; });
  await expect.poll(() => page.evaluate(() => window.__roomSockets.length)).toBe(1);
  observerMessages.principalReplies = principalReplies;
  return observerMessages;
}

async function startTranscriptAudit(page) {
  await page.evaluate(() => {
    const transcript = document.querySelector('#transcript');
    window.__transcriptAudit = { records: 0, additions: 0, removals: 0, becameEmpty: false };
    window.__transcriptObserver?.disconnect();
    window.__transcriptObserver = new MutationObserver((records) => {
      for (const record of records) {
        if (record.type !== 'childList') continue;
        window.__transcriptAudit.records += 1;
        window.__transcriptAudit.additions += record.addedNodes.length;
        window.__transcriptAudit.removals += record.removedNodes.length;
        if (!transcript.children.length) window.__transcriptAudit.becameEmpty = true;
      }
    });
    window.__transcriptObserver.observe(transcript, { childList: true });
  });
}

async function emit(page, payload, socketIndex = -1) {
  await page.evaluate(({ payload, socketIndex }) => {
    const sockets = window.__roomSockets;
    const socket = socketIndex < 0 ? sockets[sockets.length - 1] : sockets[socketIndex];
    socket.emit(payload);
  }, { payload, socketIndex });
}

async function transcriptState(page) {
  return page.locator('#transcript').evaluate((element) => ({
    count: element.querySelectorAll('.event').length,
    ids: [...element.querySelectorAll('.event')].map((node) => node.dataset.eventId),
    scrollTop: element.scrollTop,
    scrollHeight: element.scrollHeight,
    clientHeight: element.clientHeight,
    audit: { ...window.__transcriptAudit },
  }));
}

test('observer composer sends on Enter, keeps Shift+Enter as newline, and ignores composing Enter', async ({ page }) => {
  const observerMessages = await openFixture(page, makeRoom([]));
  const composer = page.locator('#message-form textarea');

  await expect(composer).toBeFocused();
  await expect(page.locator('.composer-hint')).toHaveText('Enter to send · Shift+Enter for newline');

  await composer.fill('IME draft');
  await composer.evaluate((element) => {
    const event = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true });
    Object.defineProperty(event, 'isComposing', { value: true });
    element.dispatchEvent(event);
  });
  await expect(composer).toHaveValue('IME draft');
  expect(observerMessages).toHaveLength(0);

  await composer.fill('line one');
  await composer.press('Shift+Enter');
  await expect(composer).toHaveValue('line one\n');
  expect(observerMessages).toHaveLength(0);

  await composer.type('line two');
  await composer.press('Control+Enter');
  await expect.poll(() => observerMessages.length).toBe(1);
  expect(observerMessages[0]).toEqual({ target: 'all', content: 'line one\nline two' });
  await expect(composer).toHaveValue('');
  await expect(composer).toBeFocused();

  await composer.fill('plain enter');
  await composer.press('Enter');
  await expect.poll(() => observerMessages.length).toBe(2);
  expect(observerMessages[1]).toEqual({ target: 'all', content: 'plain enter' });
  await expect(composer).toHaveValue('');
  await expect(composer).toBeFocused();
});

test('observer composer grows and preserves per-Room drafts across switching and refresh', async ({ page }) => {
  const secondRoomId = 'room_composer_second';
  const firstRoom = makeRoom([], roomId, 'Primary room');
  const secondRoom = makeRoom([], secondRoomId, 'Second room');
  const observerMessages = await openFixture(page, firstRoom, [secondRoom]);
  const composer = page.locator('#message-form textarea');
  const target = page.locator('#message-form select[name=target]');

  const initialHeight = await composer.evaluate((element) => element.getBoundingClientRect().height);
  await composer.fill(['one', 'two', 'three', 'four', 'five', 'six'].join('\n'));
  const grownHeight = await composer.evaluate((element) => element.getBoundingClientRect().height);
  expect(grownHeight).toBeGreaterThan(initialHeight);

  await composer.fill(Array.from({ length: 16 }, (_, index) => `line ${index + 1}`).join('\n'));
  const capped = await composer.evaluate((element) => ({
    height: element.getBoundingClientRect().height,
    clientHeight: element.clientHeight,
    scrollHeight: element.scrollHeight,
    maxHeight: Number.parseFloat(getComputedStyle(element).maxHeight),
    overflowY: getComputedStyle(element).overflowY,
  }));
  expect(capped.height).toBeLessThanOrEqual(capped.maxHeight + 1);
  expect(capped.scrollHeight).toBeGreaterThan(capped.clientHeight);
  expect(capped.overflowY).toBe('auto');

  await composer.fill('First room draft');
  await target.selectOption('agent_b');
  await page.locator('#room-list button').filter({ hasText: 'Second room' }).click();
  await expect(composer).toBeFocused();
  await expect(composer).toHaveValue('');
  await expect(target).toHaveValue('all');

  await composer.fill('Second room draft');
  await target.selectOption('agent_c');
  await page.locator('#room-list button').filter({ hasText: 'Primary room' }).click();
  await expect(composer).toHaveValue('First room draft');
  await expect(target).toHaveValue('agent_b');
  await expect(composer).toBeFocused();

  await page.reload();
  await expect(composer).toHaveValue('First room draft');
  await expect(target).toHaveValue('agent_b');
  await expect(composer).toBeFocused();

  await composer.press('Enter');
  await expect.poll(() => observerMessages.length).toBe(1);
  expect(observerMessages[0]).toEqual({ target: 'agent_b', content: 'First room draft' });
  await expect(composer).toHaveValue('');
  await expect(composer).toBeFocused();

  const storedDrafts = await page.evaluate(({ firstId, secondId }) => ({
    first: localStorage.getItem(`codex-room:observer-draft:${firstId}`),
    second: localStorage.getItem(`codex-room:observer-draft:${secondId}`),
  }), { firstId: roomId, secondId: secondRoomId });
  expect(storedDrafts.first).toBeNull();
  expect(JSON.parse(storedDrafts.second)).toEqual({ content: 'Second room draft', target: 'agent_c' });

  await page.locator('#room-list button').filter({ hasText: 'Second room' }).click();
  await expect(composer).toHaveValue('Second room draft');
  await expect(target).toHaveValue('agent_c');
  await expect(composer).toBeFocused();
});

test('private principal consultation renders an isolated reply flow', async ({ page }) => {
  const consultation = makeEvent(1, {
    source: 'agent_c',
    event_type: 'principal_message',
    event_class: 'conversation',
    destination: 'observer',
    content: 'Should I take the conservative interpretation?',
    metadata: {
      private: true,
      principal_channel: true,
      awaiting_principal_reply: true,
      assignment_id: 'assignment_private_consult',
    },
  });
  const observerMessages = await openFixture(page, makeRoom([consultation]));
  const node = page.locator(`[data-event-id="${consultation.id}"]`);

  await expect(node.locator('.event-badge.private')).toHaveText('private · Agent C → you');
  await expect(node.locator('.principal-reply-form')).toHaveCount(1);
  const reply = node.locator('.principal-reply-form textarea');
  await reply.fill('Use the conservative interpretation.');
  await reply.press('Enter');

  await expect.poll(() => observerMessages.principalReplies.length).toBe(1);
  expect(observerMessages.principalReplies[0]).toEqual({
    consultation_event_id: consultation.id,
    content: 'Use the conservative interpretation.',
  });
  expect(observerMessages).toHaveLength(0);
  await expect(node.locator('.principal-reply-form')).toHaveCount(0);
  await expect(node.locator('.principal-reply-status')).toHaveText('Private reply sent');
});

test('answered private principal consultation does not offer a second reply form', async ({ page }) => {
  const consultation = makeEvent(1, {
    source: 'agent_c',
    event_type: 'principal_message',
    event_class: 'conversation',
    destination: 'observer',
    content: 'Choose alpha or beta.',
    metadata: {
      private: true,
      principal_channel: true,
      awaiting_principal_reply: true,
      assignment_id: 'assignment_private_consult',
    },
  });
  const reply = makeEvent(2, {
    source: 'observer',
    event_type: 'principal_reply',
    event_class: 'conversation',
    destination: 'agent_c',
    content: 'Choose beta.',
    related_event_id: consultation.id,
    metadata: {
      private: true,
      principal_channel: true,
      consultation_event_id: consultation.id,
      assignment_id: 'assignment_private_consult',
    },
  });

  await openFixture(page, makeRoom([consultation, reply]));
  const consultationNode = page.locator(`[data-event-id="${consultation.id}"]`);
  const replyNode = page.locator(`[data-event-id="${reply.id}"]`);
  await expect(consultationNode.locator('.principal-reply-form')).toHaveCount(0);
  await expect(consultationNode.locator('.principal-reply-status')).toHaveText('Private reply recorded');
  await expect(replyNode.locator('.event-badge.private')).toHaveText('private · you → Agent C');
});

test('status bursts and reconnect preserve a scrolled-up large transcript without DOM churn', async ({ page }) => {
  const events = Array.from({ length: 864 }, (_, index) => makeEvent(index + 1));
  const room = makeRoom(events);
  await openFixture(page, room);
  await page.locator('#transcript').evaluate((element) => {
    element.scrollTop = Math.floor(element.scrollHeight * 0.37);
    element.dispatchEvent(new Event('scroll'));
  });
  const before = await transcriptState(page);
  expect(before.scrollHeight).toBeGreaterThan(50000);
  await startTranscriptAudit(page);

  for (let update = 0; update < 60; update += 1) {
    const letter = ['a', 'b', 'c'][update % 3];
    const agents = room.agents.map((agent) => agent.agent_key === `agent_${letter}` ? {
      ...agent,
      status: update % 2 ? 'running' : 'idle',
      execution: {
        phase: update % 2 ? 'invoking' : 'idle',
        health: update % 2 ? 'progress_unobservable' : 'healthy',
        reason: `Fixture update ${update}`,
      },
    } : agent);
    await emit(page, { kind: 'state', room: { ...room, agents, events: undefined } });
  }
  await page.waitForTimeout(50);
  const afterStatus = await transcriptState(page);
  expect(afterStatus.count).toBe(864);
  expect(afterStatus.ids).toEqual(events.map((event) => event.id));
  expect(afterStatus.scrollTop).toBe(before.scrollTop);
  expect(afterStatus.audit).toEqual({ records: 0, additions: 0, removals: 0, becameEmpty: false });

  await page.evaluate(() => window.__roomSockets[0].drop());
  await expect.poll(() => page.evaluate(() => window.__roomSockets.length), { timeout: 3000 }).toBe(2);
  await emit(page, { kind: 'snapshot', room: { ...room, events: [] } });
  await page.waitForTimeout(50);
  const afterEmptySnapshot = await transcriptState(page);
  expect(afterEmptySnapshot.count).toBe(864);
  expect(afterEmptySnapshot.ids).toEqual(events.map((event) => event.id));
  expect(afterEmptySnapshot.scrollTop).toBe(before.scrollTop);
  expect(afterEmptySnapshot.audit).toEqual({ records: 0, additions: 0, removals: 0, becameEmpty: false });

  await emit(page, { kind: 'snapshot', room });
  await page.waitForTimeout(50);
  const afterReconcile = await transcriptState(page);
  expect(afterReconcile.count).toBe(864);
  expect(afterReconcile.ids).toEqual(events.map((event) => event.id));
  expect(afterReconcile.scrollTop).toBe(before.scrollTop);
  expect(afterReconcile.audit).toEqual({ records: 0, additions: 0, removals: 0, becameEmpty: false });
});

test('conversation updates preserve an upward reader, remain unique and ordered, and follow near bottom', async ({ page }) => {
  const events = Array.from({ length: 864 }, (_, index) => makeEvent(index + 1));
  const room = makeRoom(events);
  await openFixture(page, room);
  await page.locator('#transcript').evaluate((element) => {
    element.scrollTop = Math.floor(element.scrollHeight * 0.41);
    element.dispatchEvent(new Event('scroll'));
  });
  await startTranscriptAudit(page);
  const before = await transcriptState(page);
  const next = makeEvent(865, { source: 'agent_c' });
  await emit(page, { kind: 'event', event: next });
  await emit(page, { kind: 'event', event: next });
  await page.waitForTimeout(50);
  const afterUpwardAppend = await transcriptState(page);
  expect(afterUpwardAppend.count).toBe(865);
  expect(afterUpwardAppend.scrollTop).toBe(before.scrollTop);
  expect(afterUpwardAppend.audit.removals).toBe(0);
  expect(afterUpwardAppend.audit.becameEmpty).toBe(false);
  expect(afterUpwardAppend.ids).toEqual([...events.map((event) => event.id), next.id]);
  expect(new Set(afterUpwardAppend.ids).size).toBe(afterUpwardAppend.ids.length);

  await page.locator('#transcript').evaluate((element) => {
    element.scrollTop = element.scrollHeight;
    element.dispatchEvent(new Event('scroll'));
  });
  const following = makeEvent(866, { source: 'agent_a' });
  await emit(page, { kind: 'event', event: following });
  await page.waitForTimeout(50);
  const afterFollowing = await transcriptState(page);
  expect(afterFollowing.scrollHeight - afterFollowing.scrollTop - afterFollowing.clientHeight).toBeLessThan(5);
  expect(afterFollowing.ids.at(-1)).toBe(following.id);

  const event867 = makeEvent(867, { source: 'agent_b' });
  const event868 = makeEvent(868, { source: 'agent_c' });
  await emit(page, {
    kind: 'snapshot',
    room: { ...room, events: [...events, event868, next, event867, following, event867] },
  });
  await page.waitForTimeout(50);
  const final = await transcriptState(page);
  const expectedIds = Array.from({ length: 868 }, (_, index) => makeEvent(index + 1).id);
  expect(final.ids).toEqual(expectedIds);
  expect(new Set(final.ids).size).toBe(final.ids.length);
  expect(final.audit.removals).toBe(0);
  expect(final.audit.becameEmpty).toBe(false);
  expect(final.scrollHeight - final.scrollTop - final.clientHeight).toBeLessThan(5);
});

test('retry warnings, successful recovery, and terminal failure are visually distinct', async ({ page }) => {
  const warning = makeEvent(1, {
    source: 'agent_a', event_type: 'agent_error', event_class: 'mechanical',
    content: 'Agent A attempt interrupted — retrying: transient interruption',
    metadata: { will_retry: true, operator_state: 'recovered' },
  });
  const recovered = makeEvent(2, {
    source: 'agent_a', event_type: 'agent_pass', event_class: 'conversation', content: '',
    metadata: {
      retry_recovery: { status: 'recovered', attempt_failure_count: 2 },
    },
  });
  const terminal = makeEvent(3, {
    source: 'agent_b', event_type: 'agent_error', event_class: 'mechanical',
    content: 'Agent B agent error — recovery failed: terminal interruption',
    metadata: { will_retry: false, operator_state: 'terminal_failure' },
  });
  await openFixture(page, makeRoom([warning, recovered, terminal]));

  const warningNode = page.locator(`[data-event-id="${warning.id}"]`);
  await expect(warningNode).toHaveClass(/attempt-warning/);
  await expect(warningNode.locator('.event-badge').first()).toHaveText('attempt warning');
  await expect(warningNode.locator('.event-badge.recovered')).toHaveText('recovered');

  const recoveredNode = page.locator(`[data-event-id="${recovered.id}"]`);
  await expect(recoveredNode).toHaveClass(/recovered/);
  await expect(recoveredNode.locator('.event-badge.recovered')).toHaveText(
    'recovered after 2 retries',
  );

  const terminalNode = page.locator(`[data-event-id="${terminal.id}"]`);
  await expect(terminalNode).toHaveClass(/terminal-error/);
  await expect(terminalNode.locator('.event-badge').first()).toHaveText(
    'agent error · recovery failed',
  );
});
