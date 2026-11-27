const find = (id) => document.getElementById(id);
const names = ['X1', 'Y', 'Z'];
const axisLabel = (name) => name === 'X1' ? 'X' : name;
const receivedTime = new Intl.DateTimeFormat('ko-KR', {timeStyle: 'medium', hour12: false});
const rows = new Map();
let snapshot;
let lastFrame = 0;
let lastReceivedAt;
let fresh = false;
let hold;

for (const name of names) {
  const label = axisLabel(name);
  const row = document.createElement('tr');
  row.innerHTML = `<th scope="row"><label><input class="selected" type="checkbox" aria-label="${label} 선택"> ${label}</label></th>
    <td class="pos">—</td><td class="vel">—</td><td class="status">—</td>
    <td><input class="target" aria-label="${label} 목표 위치" type="number" step="any"></td>
    <td><div class="actions"><button type="button" data-motion="enable" disabled>On</button>
    <button type="button" data-motion="disable" disabled>Off</button>
    <button type="button" data-motion="home" disabled>Home</button>
    <button type="button" data-jog="negative" disabled>Jog −</button>
    <button type="button" data-jog="positive" disabled>Jog +</button></div></td>`;
  find('axes').append(row);
  rows.set(name, row);
  row.querySelector('.selected').onchange = render;
  row.querySelector('.target').oninput = render;
  for (const button of row.querySelectorAll('[data-motion]')) {
    button.onclick = () => send(button.dataset.motion, {axes: [name]});
  }
  for (const button of row.querySelectorAll('[data-jog]')) {
    button.addEventListener('pointerdown', (event) => {
      if (event.button !== 0) return;
      button.setPointerCapture(event.pointerId);
      startJog(name, button.dataset.jog);
    });
    for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) {
      button.addEventListener(event, release);
    }
    button.addEventListener('keydown', (event) => {
      if ([' ', 'Enter'].includes(event.key)) {
        event.preventDefault();
        if (!event.repeat) startJog(name, button.dataset.jog);
      }
    });
    button.addEventListener('keyup', release);
  }
}

async function post(path, body) {
  const response = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  });
  const answer = await response.json();
  if (!response.ok) throw new Error(answer.reason || '잘못된 요청');
}

async function send(action, fields = {}) {
  try {
    await post('/api/command', {action, ...fields});
    find('notice').textContent = '요청 접수';
    return true;
  } catch (error) {
    find('notice').textContent = error instanceof TypeError ? '접수 여부 미확인' : error.message;
    return false;
  }
}

function render() {
  if (!snapshot) return;
  const hmi = snapshot.source === 'HMI';
  const ready = fresh && snapshot.connected && snapshot.state === 'Ready' && !snapshot.activity;
  const allowed = ready && hmi && snapshot.authority;
  find('connection').textContent = !fresh
    ? `상태 갱신 중단 · 마지막 값 · ${receivedTime.format(lastReceivedAt)} 수신`
    : snapshot.connected ? 'Motion Server 연결' : 'Motion Server 연결 끊김';
  find('state').textContent = snapshot.state;
  find('source').textContent = snapshot.source;
  find('authority').textContent = snapshot.authority ? '보유' : '없음';
  find('pendant').textContent = snapshot.pendant_connected ? '연결' : '연결 안 됨';
  find('fault').textContent = snapshot.fault || '';
  if (snapshot.notice) find('notice').textContent = snapshot.notice;
  find('pendant-mode').value = snapshot.pendant_mode;
  find('pendant-axis').value = snapshot.pendant_axis;
  find('pendant-mode').disabled = !ready;
  find('pendant-axis').disabled = !ready || snapshot.pendant_mode === 'Multi';
  const entries = Object.entries(snapshot.pv);
  find('pv').hidden = !entries.length;
  find('pv').textContent = entries.map(([name, s]) =>
    axisLabel(name) + ' PV ' + s.requested.toFixed(1) + ' → ' + s.commanded.toFixed(1) + ' mm/s').join(' · ');

  for (const [name, row] of rows) {
    const axis = snapshot.virtual[name];
    row.querySelector('.pos').textContent = axis ? axis.position.toFixed(3) : '—';
    row.querySelector('.vel').textContent = axis ? axis.velocity.toFixed(3) : '—';
    row.querySelector('.status').textContent = axis
      ? (axis.enabled ? 'On' : 'Off') + (axis.moving ? ' · 이동' : ' · 정지') : '—';
    for (const button of row.querySelectorAll('[data-motion]')) {
      button.disabled = !allowed || !axis || (button.dataset.motion !== 'enable' && !axis.enabled);
    }
    for (const button of row.querySelectorAll('[data-jog]')) {
      button.disabled = !hold && (!allowed || !axis?.enabled);
    }
  }
  const loader = snapshot.loader;
  find('loader-panel').hidden = !loader;
  if (loader) {
    const feedback = loader.feedback;
    for (const signal of ['initial_sensor', 'opposite_sensor', 'initial_output', 'opposite_output']) {
      find('loader-' + signal.replace('_', '-')).textContent = feedback ? (feedback[signal] ? 'ON' : 'OFF') : '—';
    }
    const endpointLabels = {initial: 'Unload', opposite: 'Load'};
    if (!feedback) {
      find('loader-endpoint').textContent = '—';
    } else if (feedback.initial_sensor && feedback.opposite_sensor) {
      find('loader-endpoint').textContent = '양단 센서 동시 ON';
    } else {
      find('loader-endpoint').textContent = endpointLabels[feedback.endpoint] || '끝단 미감지';
    }
    const stopLabels = {pending: '확인 중', confirmed: '확인됨', unconfirmed: '미확인'};
    find('loader-stop').textContent = stopLabels[loader.stop_confirmation] || '요청 없음';
    for (const button of document.querySelectorAll('[data-loader]')) {
      button.disabled = !allowed || !feedback || feedback.conflicting || !loader.endpoint_hold_verified;
    }
  }
  const selection = selectedTargets();
  find('pp').disabled = !allowed || !selection.length ||
    selection.some(([name, position]) => !snapshot.virtual[name]?.enabled || !Number.isFinite(position));
  find('enable-all').disabled = !allowed || names.some((name) => !snapshot.virtual[name]);
  for (const button of document.querySelectorAll('[data-source]')) button.disabled = !ready;
  const changeAuthority = fresh && snapshot.connected && !snapshot.activity &&
    ['Ready', 'Fault'].includes(snapshot.state);
  find('claim').disabled = !changeAuthority || snapshot.authority;
  find('release').disabled = !changeAuthority || !snapshot.authority;
  find('recover').disabled = !fresh || snapshot.state !== 'Fault' || Boolean(snapshot.activity);
}

function selectedTargets() {
  return [...rows].filter(([, row]) => row.querySelector('.selected').checked)
    .map(([name, row]) => [name, row.querySelector('.target').valueAsNumber]);
}

function connect() {
  const socket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/api/state');
  socket.onmessage = ({data}) => {
    snapshot = JSON.parse(data);
    lastFrame = performance.now();
    lastReceivedAt = Date.now();
    fresh = true;
    render();
  };
  socket.onclose = () => {
    fresh = false;
    release();
    render();
    setTimeout(connect, 500);
  };
}

async function startJog(name, direction) {
  if (hold || !fresh) return;
  const id = Array.from(crypto.getRandomValues(new Uint8Array(16)),
    (byte) => byte.toString(16).padStart(2, '0')).join('');
  const current = {id, started: false, timer: null};
  hold = current;
  if (!await send('jog', {axes: [name], direction, hold: current.id})) {
    if (hold === current) hold = null;
    render();
    return;
  }
  current.started = true;
  if (hold !== current) {
    post('/api/hold', {hold: current.id, pressed: false}).catch(() => {});
    return;
  }
  current.timer = setInterval(() => {
    if (hold !== current || !fresh) return;
    post('/api/hold', {hold: current.id, pressed: true}).catch(release);
  }, 100);
}

function release() {
  if (!hold) return;
  const current = hold;
  hold = null;
  clearInterval(current.timer);
  if (current.started) post('/api/hold', {hold: current.id, pressed: false}).catch(() => {});
  render();
}

window.addEventListener('blur', release);
document.addEventListener('visibilitychange', () => { if (document.hidden) release(); });
for (const button of document.querySelectorAll('[data-source]')) {
  button.onclick = () => send('source', {source: button.dataset.source});
}
for (const button of document.querySelectorAll('[data-loader]')) {
  button.onclick = () => send('loader', {loader_direction: button.dataset.loader});
}
find('claim').onclick = () => send('authority', {enabled: true});
find('release').onclick = () => send('authority', {enabled: false});
find('enable-all').onclick = () => send('enable', {axes: names});
find('disable').onclick = () => send('disable', {axes: names});
find('stop').onclick = () => { release(); send('stop'); };
find('recover').onclick = () => send('recover');
find('pendant-mode').onchange = (event) => send('pendant_setup', {pendant_mode: event.target.value});
find('pendant-axis').onchange = (event) => send('pendant_setup', {pendant_axis: event.target.value});
find('move').onsubmit = (event) => {
  event.preventDefault();
  if (fresh && !find('pp').disabled) send('pp', {positions: Object.fromEntries(selectedTargets())});
};
setInterval(() => {
  if (fresh && performance.now() - lastFrame >= snapshot.period_ms * snapshot.missed_frames) {
    fresh = false;
    release();
    render();
  }
}, 50);
connect();
