const $ = (s) => document.querySelector(s);
const hub = () => ($('#hubBase')?.value || 'http://127.0.0.1:8787').replace(/\/$/, '');

async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  try {
    const res = await fetch(hub() + path, opts);
    const text = await res.text();
    let json; try { json = JSON.parse(text); } catch { json = text; }
    return { status: res.status, json };
  } catch (e) {
    return { status: 0, json: { error: String(e) } };
  }
}

function show(el, data) {
  const node = $(el);
  if (!node) return;
  node.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
}

document.querySelectorAll('.nav button').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    const id = 'tab-' + btn.dataset.tab;
    document.getElementById(id)?.classList.add('active');
  };
});

async function pingHealth() {
  const r = await api('GET', '/health');
  show('#healthOut', r);
  const badge = $('#hub-badge');
  if (badge) badge.textContent = r.status === 200 ? 'hub OK' : 'hub DOWN';
}
async function loadRoot() { show('#rootOut', await api('GET', '/debug/session_root')); }
async function loadAuthCfg() { show('#authOut', await api('GET', '/auth/config')); }
async function loadLogin() { show('#authOut', await api('GET', '/auth/login')); }
async function loadSess() { show('#sessOut', await api('GET', '/session')); }
async function loadSessCookie() { show('#sessOut', await api('GET', '/session/cookie')); }
async function loadGw() { show('#gwOut', await api('GET', '/gateway/headers')); }
async function loadLiveDry() { show('#liveDryOut', await api('GET', '/livekit/token/dry-run')); }
async function loadCS() { show('#csOut', await api('GET', '/create_session/sim')); }
async function loadDbg() { show('#dbgOut', await api('GET', '/debug/state')); }
async function loadAgentSim() { show('#agentOut', await api('GET', '/livekit/agent/sim')); }
async function loadDispatchSim() { show('#dispatchOut', await api('GET', '/livekit/dispatch/sim')); }
async function runStress() {
  const n = Number($('#stressN')?.value || 32);
  const t0 = performance.now();
  const jobs = Array.from({length: n}, (_, i) => api('GET', `/stress/ping?n=${i}`));
  const res = await Promise.all(jobs);
  const ok = res.filter(x => x.status === 200).length;
  show('#stressOut', {n, ok, ms: Math.round(performance.now()-t0), sample: res.slice(0,3)});
}

['btnHealth','btnRoot','btnAuthCfg','btnLogin','btnSess','btnSessCookie','btnGw','btnLiveDry','btnCS','btnDbg','btnAgent','btnDispatch','btnStress'].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  const map = {btnHealth:pingHealth,btnRoot:loadRoot,btnAuthCfg:loadAuthCfg,btnLogin:loadLogin,btnSess:loadSess,btnSessCookie:loadSessCookie,btnGw:loadGw,btnLiveDry:loadLiveDry,btnCS:loadCS,btnDbg:loadDbg,btnAgent:loadAgentSim,btnDispatch:loadDispatchSim,btnStress:runStress};
  el.addEventListener('click', map[id]);
});
pingHealth();
