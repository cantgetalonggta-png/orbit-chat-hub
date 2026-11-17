const $ = (s) => document.querySelector(s);
const hub = () => ($('#hubBase').value || 'http://127.0.0.1:8787').replace(/\/$/, '');

async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(hub() + path, opts);
  const text = await res.text();
  let json; try { json = JSON.parse(text); } catch { json = text; }
  return { status: res.status, json };
}

function show(el, data) {
  $(el).textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
}

document.querySelectorAll('.nav button').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    $('#tab-' + btn.dataset.tab).classList.add('active');
  };
});

$('#btnHealth').onclick = async () => {
  const r = await api('GET', '/health');
  show('#healthOut', r);
  const b = $('#hub-badge');
  if (r.status === 200 && r.json && r.json.ok) {
    b.textContent = 'hub UP'; b.className = 'badge ok';
    if (r.json.routes) {
      $('#routeList').innerHTML = r.json.routes.map(x => `<li><code>${x}</code></li>`).join('');
    }
  } else {
    b.textContent = 'hub DOWN'; b.className = 'badge bad';
  }
};
$('#btnRoot').onclick = async () => show('#rootOut', await api('GET', '/debug/session_root'));
$('#btnAuthCfg').onclick = async () => show('#authOut', await api('GET', '/auth/config'));
$('#btnLogin').onclick = async () => {
  const r = await api('GET', '/auth/login?state=orbit');
  show('#authOut', r);
  if (r.json && r.json.authorize_url) {
    const a = $('#loginLink'); a.href = r.json.authorize_url; a.style.display = 'inline-block';
  }
};
$('#btnLogout').onclick = async () => show('#authOut', await api('GET', '/auth/logout'));
$('#btnToken').onclick = async () => {
  const body = { code: $('#oauthCode').value };
  if ($('#redirectUri').value) body.redirect_uri = $('#redirectUri').value;
  show('#tokenOut', await api('POST', '/auth/token', body));
};
$('#btnStoreCookie').onclick = async () => show('#sessOut', await api('POST', '/session/cookie', {
  session_cookie: $('#sessCookie').value,
  session_id: $('#sessId').value || undefined,
  user_id: $('#userId').value || undefined,
  sign_in_method: $('#signIn').value,
}));
$('#btnGetSession').onclick = async () => show('#sessOut', await api('GET', '/session'));
$('#btnGetSessionRaw').onclick = async () => show('#sessOut', await api('GET', '/session?raw=1'));
$('#btnClearSession').onclick = async () => show('#sessOut', await api('DELETE', '/session'));
$('#btnHeaders').onclick = async () => show('#gwOut', await api('GET', '/gateway/headers'));
$('#btnHeadersRaw').onclick = async () => show('#gwOut', await api('GET', '/gateway/headers?raw=1'));
$('#btnAppCfgDry').onclick = async () => show('#gwOut', await api('POST', '/gateway/app_config', {}));
$('#btnAppCfgProxy').onclick = async () => show('#gwOut', await api('POST', '/gateway/app_config', { proxy: true }));
$('#btnLkDry').onclick = async () => {
  const id = $('#convId').value || crypto.randomUUID();
  show('#lkOut', await api('GET', `/livekit/token/dry-run?conversation_id=${encodeURIComponent(id)}&agent_name=${encodeURIComponent($('#agentName').value)}`));
};
$('#btnLkPost').onclick = async () => show('#lkOut', await api('POST', '/livekit/token', {
  conversation_id: $('#convId').value || crypto.randomUUID(),
  agent_name: $('#agentName').value,
  proxy: false,
}));
$('#btnLkProxy').onclick = async () => show('#lkOut', await api('POST', '/livekit/token', {
  conversation_id: $('#convId').value || crypto.randomUUID(),
  agent_name: $('#agentName').value,
  proxy: true,
}));
$('#btnSimGet').onclick = async () => show('#simOut', await api('GET', '/create_session/sim'));
$('#btnSimPost').onclick = async () => show('#simOut', await api('POST', '/create_session/sim', {
  email: $('#simEmail').value,
  sign_in_method: 'EMAIL_PASSWORD',
}));
$('#btnDebugState').onclick = async () => show('#dbgOut', await api('GET', '/debug/state'));
$('#btnMissingCode').onclick = async () => show('#dbgOut', await api('POST', '/auth/token', {}));
$('#btnMissingCookie').onclick = async () => show('#dbgOut', await api('POST', '/session/cookie', {}));
$('#btn404').onclick = async () => show('#dbgOut', await api('GET', '/no-such-route'));
$('#btnStress').onclick = async () => {
  const paths = ['/health', '/debug/session_root', '/auth/config', '/session/headers', '/create_session/sim', '/livekit/token/dry-run'];
  const out = [];
  for (const p of paths) out.push(await api('GET', p));
  out.push(await api('POST', '/auth/token', {}));
  out.push(await api('POST', '/session/cookie', {}));
  show('#dbgOut', out.map(x => ({ status: x.status, path: x.json && x.json.path, ok: x.json && x.json.ok })));
};

// boot
$('#convId').value = crypto.randomUUID();
$('#btnHealth').click();


// Production extensions: CloudAgent + dispatch + stress
async function loadAgentSim() {
  const r = await api('GET', '/livekit/agent/sim');
  show('#agentOut', r);
}
async function loadDispatchSim() {
  const r = await api('GET', '/livekit/dispatch/sim');
  show('#dispatchOut', r);
}
async function runStress() {
  const n = Number($('#stressN')?.value || 32);
  const t0 = performance.now();
  const jobs = Array.from({length: n}, (_, i) => api('GET', `/stress/ping?n=${i}`));
  const res = await Promise.all(jobs);
  const ok = res.filter(x => x.status === 200).length;
  show('#stressOut', {n, ok, ms: Math.round(performance.now()-t0), sample: res.slice(0,3)});
}
document.getElementById('btnAgent')?.addEventListener('click', loadAgentSim);
document.getElementById('btnDispatch')?.addEventListener('click', loadDispatchSim);
document.getElementById('btnStress')?.addEventListener('click', runStress);


// LOOP2: voice map + agents + sandbox
async function loadVoiceMap() {
  const r = await api('GET', '/livekit/voice/map');
  show('#voiceMapOut', r.json);
}
async function loadAgents() {
  const r = await api('GET', '/agents/registry');
  show('#agentsOut', r.json);
}
async function loadSandbox() {
  const r = await api('GET', '/sandbox/agent/sim');
  show('#sandboxOut', r.json);
}
document.getElementById('btnVoiceMap')?.addEventListener('click', loadVoiceMap);
document.getElementById('btnAgents')?.addEventListener('click', loadAgents);
document.getElementById('btnSandbox')?.addEventListener('click', loadSandbox);
