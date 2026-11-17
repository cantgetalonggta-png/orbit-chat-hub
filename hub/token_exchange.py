#!/usr/bin/env python3
"""Orbit Chat Hub — Cognito token exchange + session_cookie + LiveKit bridge."""
from __future__ import annotations
# Public mirror — set GROK_X_API_KEY / COGNITO_CLIENT_SECRET via env.
# Full production source lives in workspace; this is the deployable scrubbed copy.
import json, os, sys, time, urllib.parse, urllib.request, urllib.error, hashlib, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / 'cognito_config.json').read_text()) if (ROOT / 'cognito_config.json').exists() else {}
CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET', '')
DEFAULT_REDIRECT = os.environ.get('COGNITO_REDIRECT_URI', 'http://127.0.0.1:8787/auth/callback/')
SESSION_FILE = ROOT / 'session_store.json'
STATE_FILE = ROOT / 'state.json'
DEFAULT_API_KEY = os.environ.get('GROK_X_API_KEY', 'SET_VIA_GROK_X_API_KEY_ENV')
LIVEKIT_TOKEN_URLS = [
  'https://grok.com/rest/livekit/tokens',
  'https://grok-v2.x.ai/rest/livekit/tokens',
  'https://grok-api.gcp.mouseion.dev/rest/livekit/tokens',
]
APP_CONFIG_URL = 'https://grok.com/_data/v1/app_config'

def _load_session():
  if SESSION_FILE.exists():
    try: return json.loads(SESSION_FILE.read_text())
    except Exception: return {}
  return {}

def _save_session(data):
  data = dict(data); data['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
  SESSION_FILE.write_text(json.dumps(data, indent=2))

def gateway_headers(sess=None, extra=None):
  sess = sess or _load_session()
  h = {'Content-Type':'application/json','x-request-id':str(uuid.uuid4()),'x-api-key':sess.get('x_api_key') or DEFAULT_API_KEY,'x-os-name':'Android','x-user-language':sess.get('x_user_language') or 'en','x-user-locale':sess.get('x_user_locale') or 'en-US'}
  if sess.get('session_cookie'): h['Cookie']=sess['session_cookie']; h['x-session-cookie']=sess['session_cookie']
  if sess.get('access_token'): h['Authorization']=f"Bearer {sess['access_token']}"
  if extra: h.update(extra)
  return h

def livekit_token_body(body):
  return {'conversation_id': body.get('conversation_id') or str(uuid.uuid4()), 'agent_name': body.get('agent_name') or 'grok-voice', 'session_payload': body.get('session_payload') or {}, 'request_agent_dispatch': bool(body.get('request_agent_dispatch', True)), 'livekit_url': body.get('livekit_url'), 'params': body.get('params') or {}}

ROUTES = ['/health','/auth/login','/auth/token','/auth/logout','/auth/config','/session','/session/cookie','/session/headers','/gateway/headers','/gateway/app_config','/livekit/token','/livekit/token/dry-run','/debug/state','/debug/session_root','/create_session/sim','/livekit/agent/sim','/livekit/dispatch/sim','/stress/ping','/app','/app/index.html']

class Handler(BaseHTTPRequestHandler):
  def _json(self, code, obj):
    payload=json.dumps(obj).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(payload))); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers(); self.wfile.write(payload)
  def do_OPTIONS(self):
    self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS,DELETE'); self.send_header('Access-Control-Allow-Headers','Content-Type, Cookie, X-Session-Cookie, Authorization'); self.end_headers()
  def do_GET(self):
    path=urllib.parse.urlparse(self.path).path.rstrip('/') or '/'
    if path in ('/','/health'): return self._json(200,{'ok':True,'service':'orbit-hub-token-exchange','routes':ROUTES})
    if path=='/auth/config': return self._json(200,{k:CFG[k] for k in ('region','user_pool_id','client_id','domain_url','auth_url','token_url') if k in CFG})
    if path=='/session/cookie':
      sess=_load_session(); return self._json(200,{'ok':True,'has_cookie':bool(sess.get('session_cookie')),'session_id':sess.get('session_id'),'user_id':sess.get('user_id')})
    if path=='/gateway/headers' or path=='/session/headers': return self._json(200,{'headers':{k:('***' if k.lower() in ('authorization','cookie','x-api-key','x-session-cookie') else v) for k,v in gateway_headers().items()}})
    if path=='/livekit/token/dry-run': return self._json(200,{'dry_run':True,'request_body':livekit_token_body({}),'candidate_urls':LIVEKIT_TOKEN_URLS})
    if path=='/livekit/agent/sim': return self._json(200,{'proto':'livekit.LivekitCloudAgent.CreateAgentRequest','fields':['agentName_','secrets_','cpuReq_','regions_','replicas_','maxReplicas_'],'ops':['CreateAgent','DeployAgent','UpdateAgent','RestartAgent','ListAgents','RollbackAgent'],'live_session_triggers':['CreateTokenRequest.request_agent_dispatch=true','LivekitAgentDispatch','WorkerMessage JobAssignment']})
    if path=='/livekit/dispatch/sim': return self._json(200,{'background_agent':True,'background_synchronization':'Li/h SharedFlow + Li/s coroutines','not_sandbox':True})
    if path=='/stress/ping': return self._json(200,{'ok':True,'ts':time.time()})
    if path=='/create_session/sim': return self._json(200,{'CreateSessionRequest':{'EmailAndPasswordRequest':{'email':'user@example.com'}},'sign_in_method_enum':['EMAIL_PASSWORD','GOOGLE_OAUTH2','X_OAUTH2','APPLE_OAUTH2']})
    if path=='/debug/session_root': return self._json(200,{'primary_session':'211e2cba-1b23-5ce8-945a-d5e158b037a2','locked':True})
    if path.startswith('/app'): return self._json(200,{'hint':'serve static SPA from frontend/ or full hub binary'})
    return self._json(404,{'error':'not_found','path':path})
  def do_POST(self):
    path=urllib.parse.urlparse(self.path).path.rstrip('/') or '/'
    length=int(self.headers.get('Content-Length') or 0); raw=self.rfile.read(length) if length else b'{}'
    try: body=json.loads(raw.decode() or '{}')
    except Exception: body={}
    if path=='/session/cookie':
      cookie=body.get('session_cookie') or body.get('cookie')
      if not cookie: return self._json(400,{'error':'missing_session_cookie'})
      sess=_load_session(); sess['session_cookie']=cookie; sess['session_id']=body.get('session_id'); sess['user_id']=body.get('user_id'); _save_session(sess)
      return self._json(200,{'ok':True,'stored':True})
    if path=='/livekit/token':
      req=livekit_token_body(body)
      if not body.get('proxy'): return self._json(200,{'dry_run':True,'request_body':req,'hint':'set proxy=true to forward'})
      return self._json(200,{'forwarded':False,'hint':'configure session_cookie + GROK_X_API_KEY for live forward'})
    return self._json(404,{'error':'not_found'})
  def log_message(self, fmt, *args): sys.stderr.write('[hub-token] '+(fmt%args)+'\n')

def main():
  port=int(os.environ.get('HUB_PORT','8787'))
  if '--self-test' in sys.argv:
    print(json.dumps({'routes':ROUTES,'livekit_urls':LIVEKIT_TOKEN_URLS},indent=2)); return
  print(json.dumps({'listening':f'0.0.0.0:{port}','routes':ROUTES}))
  HTTPServer(('0.0.0.0',port), Handler).serve_forever()
if __name__=='__main__': main()
