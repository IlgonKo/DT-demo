const find = (id) => document.getElementById(id);
let snapshot;
let lastFrame = 0;
let fresh = false;
let socket;
let hold;

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
  const axis = snapshot.virtual.X1;
  const hmi = snapshot.source === 'HMI';
  const ready = fresh && snapshot.connected && snapshot.state === 'Ready' && !snapshot.activity;
  find('connection').textContent = !fresh ? '상태 갱신 중단 · 마지막 값'
    : snapshot.connected ? 'Motion Server 연결' : 'Motion Server 연결 끊김';
  find('state').textContent = snapshot.state;
  find('source').textContent = snapshot.source;
  find('authority').textContent = snapshot.authority ? '보유' : '없음';
  find('pendant').textContent = snapshot.pendant_connected ? '연결' : '연결 안 됨';
  find('position').textContent = axis ? axis.position.toFixed(3) + ' mm' : '—';
  find('velocity').textContent = axis ? axis.velocity.toFixed(3) + ' mm/s' : '—';
  find('servo').textContent = axis && axis.enabled ? 'On' : 'Off';
  find('moving').textContent = axis ? (axis.moving ? '이동 중' : '정지') : '—';
  find('fault').textContent = snapshot.fault || '';
  if (snapshot.notice) find('notice').textContent = snapshot.notice;
  const controllable = ready && hmi && snapshot.authority && axis;
  for (const button of document.querySelectorAll('[data-motion]')) {
    button.disabled = !controllable || (button.dataset.motion !== 'enable' && !axis?.enabled);
  }
  for (const button of document.querySelectorAll('[data-jog]')) {
    button.disabled = !hold && (!controllable || !axis?.enabled);
  }
  for (const button of document.querySelectorAll('[data-source]')) button.disabled = !ready;
  const changeAuthority = fresh && snapshot.connected && !snapshot.activity &&
    ['Ready', 'Fault'].includes(snapshot.state);
  find('claim').disabled = !changeAuthority || snapshot.authority;
  find('release').disabled = !changeAuthority || !snapshot.authority;
  find('recover').disabled = !fresh || snapshot.state !== 'Fault' || Boolean(snapshot.activity);
}

function connect() {
  socket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/api/state');
  socket.onmessage = ({data}) => {
    snapshot = JSON.parse(data);
    lastFrame = performance.now();
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

async function startJog(direction) {
  if (hold || !fresh) return;
  const id = Array.from(crypto.getRandomValues(new Uint8Array(16)),
    (byte) => byte.toString(16).padStart(2, '0')).join('');
  const current = {id, started: false, timer: null};
  hold = current;
  if (!await send('jog', {direction, hold: current.id})) {
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

for (const button of document.querySelectorAll('[data-jog]')) {
  button.addEventListener('pointerdown', (event) => {
    if (event.button !== 0) return;
    button.setPointerCapture(event.pointerId);
    startJog(button.dataset.jog);
  });
  for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) {
    button.addEventListener(name, release);
  }
  button.addEventListener('keydown', (event) => {
    if ([' ', 'Enter'].includes(event.key)) {
      event.preventDefault();
      if (!event.repeat) startJog(button.dataset.jog);
    }
  });
  button.addEventListener('keyup', release);
}
window.addEventListener('blur', release);
document.addEventListener('visibilitychange', () => { if (document.hidden) release(); });
for (const button of document.querySelectorAll('[data-source]')) {
  button.onclick = () => send('source', {source: button.dataset.source});
}
for (const action of ['enable', 'home']) findButton(action).onclick = () => send(action);
function findButton(action) { return document.querySelector('[data-motion=' + action + ']'); }
find('claim').onclick = () => send('authority', {enabled: true});
find('release').onclick = () => send('authority', {enabled: false});
for (const action of ['stop', 'disable', 'recover']) find(action).onclick = () => send(action);
find('move').onsubmit = (event) => {
  event.preventDefault();
  if (fresh && !findButton('pp').disabled) send('pp', {position: find('target').valueAsNumber});
};
setInterval(() => {
  if (fresh && performance.now() - lastFrame >= snapshot.period_ms * snapshot.missed_frames) {
    fresh = false;
    release();
    render();
  }
}, 50);
connect();
