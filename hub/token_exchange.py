#!/usr/bin/env python3
"""Orbit Chat Hub — Cognito token exchange + session_cookie + LiveKit bridge."""
from __future__ import annotations

import os
import json, os, sys, time, urllib.parse, urllib.request, urllib.error, hashlib, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "cognito_config.json").read_text())
CLIENT_SECRET = os.environ.get("COGNITO_CLIENT_SECRET", "")
DEFAULT_REDIRECT = os.environ.get(
    "COGNITO_REDIRECT_URI",
    (CFG.get("callback_urls") or ["http://127.0.0.1:8787/auth/callback/"])[0],
)
SESSION_FILE = ROOT / "session_store.json"
STATE_FILE = ROOT / "state.json"
DEBUG_LOG = ROOT / "logs" / "hub_debug.jsonl"

# From RE corpus (Li/p DataGatewayHeaderInterceptor + LiveKit hosts)
DEFAULT_API_KEY = os.environ.get(
    "GROK_X_API_KEY",
    "TBKF1sBrwJ634kqCXEuqEhIoKiwlVycX/lRj+tdG7gE=",
)
LIVEKIT_TOKEN_URLS = [
    "https://grok.com/rest/livekit/tokens",
    "https://grok-v2.x.ai/rest/livekit/tokens",
    "https://grok-api.gcp.mouseion.dev/rest/livekit/tokens",
]
APP_CONFIG_URL = "https://grok.com/_data/v1/app_config"
ANALYTICS_URL = "https://grok.com/_data/v1/analytics"


def _load_session() -> dict:
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_session(data: dict) -> None:
    data = dict(data)
    data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    SESSION_FILE.write_text(json.dumps(data, indent=2))


def _debug(event: str, payload: dict) -> None:
    DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **payload,
    }
    with DEBUG_LOG.open("a") as f:
        f.write(json.dumps(row) + "\n")


def authorize_url(state: str = "fuse", redirect_uri: str | None = None) -> str:
    redirect = redirect_uri or DEFAULT_REDIRECT
    q = {
        "client_id": CFG["client_id"],
        "response_type": "code",
        "scope": " ".join(CFG.get("oauth_scopes") or ["openid", "email", "profile"]),
        "redirect_uri": redirect,
        "state": state,
    }
    return CFG["auth_url"] + "?" + urllib.parse.urlencode(q)


def exchange_code(code: str, redirect_uri: str | None = None) -> dict:
    redirect = redirect_uri or DEFAULT_REDIRECT
    data = {
        "grant_type": "authorization_code",
        "client_id": CFG["client_id"],
        "code": code,
        "redirect_uri": redirect,
    }
    if CLIENT_SECRET:
        data["client_secret"] = CLIENT_SECRET
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        CFG["token_url"],
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        try:
            return {"error": True, "status": e.code, "body": json.loads(err)}
        except Exception:
            return {"error": True, "status": e.code, "body": err}


def logout_url(redirect_uri: str | None = None) -> str:
    logout_redirect = redirect_uri or (CFG.get("logout_urls") or [DEFAULT_REDIRECT])[0]
    q = {"client_id": CFG["client_id"], "logout_uri": logout_redirect}
    return CFG["logout_url"] + "?" + urllib.parse.urlencode(q)


def gateway_headers(sess: dict | None = None, extra: dict | None = None) -> dict:
    """Reconstruct Li/p DataGatewayHeaderInterceptor headers."""
    sess = sess or _load_session()
    rid = str(uuid.uuid4())
    h = {
        "Content-Type": "application/json",
        "x-request-id": rid,
        "x-api-key": sess.get("x_api_key") or DEFAULT_API_KEY,
        "x-os-name": "Android",
        "x-user-language": sess.get("x_user_language") or "en",
        "x-user-locale": sess.get("x_user_locale") or "en-US",
    }
    if sess.get("x_user_country"):
        h["x-user-country"] = sess["x_user_country"]
    if sess.get("session_cookie"):
        h["Cookie"] = sess["session_cookie"]
        h["x-session-cookie"] = sess["session_cookie"]
    if sess.get("access_token"):
        h["Authorization"] = f"Bearer {sess['access_token']}"
    if sess.get("id_token"):
        h["x-id-token"] = sess["id_token"]
    if extra:
        h.update(extra)
    return h


def livekit_token_body(body: dict) -> dict:
    """Build CreateTokenRequest-style REST body from RE (m2/g + LivekitCreateToken)."""
    return {
        "conversation_id": body.get("conversation_id") or body.get("conversationId") or str(uuid.uuid4()),
        "agent_name": body.get("agent_name") or body.get("agentName") or "grok-voice",
        "session_payload": body.get("session_payload") or body.get("sessionPayload") or {},
        "request_agent_dispatch": bool(body.get("request_agent_dispatch", body.get("requestAgentDispatch", True))),
        "livekit_url": body.get("livekit_url") or body.get("livekitUrl"),
        "params": body.get("params") or {},
        "model": body.get("model") or body.get("model_config") or "grok-voice",
    }


def http_json(method: str, url: str, headers: dict, payload: dict | None = None, timeout: int = 30) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            try:
                return {"ok": True, "status": resp.status, "url": url, "body": json.loads(raw)}
            except Exception:
                return {"ok": True, "status": resp.status, "url": url, "body_text": raw[:4000]}
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        try:
            body = json.loads(err)
        except Exception:
            body = err[:4000]
        return {"ok": False, "status": e.code, "url": url, "body": body}
    except Exception as e:
        return {"ok": False, "status": 0, "url": url, "error": str(e)}


ROUTES = [
    "/health", "/auth/login", "/auth/token", "/auth/logout", "/auth/config",
    "/session", "/session/cookie", "/session/headers",
    "/gateway/headers", "/gateway/app_config",
    "/livekit/token", "/livekit/token/dry-run",
    "/debug/state", "/debug/session_root",
    "/create_session/sim", "/livekit/agent/sim", "/livekit/dispatch/sim", "/livekit/voice/map",
    "/sandbox/agent/sim", "/agents/registry", "/api/grpc_catalog", "/api/clients", "/extract/1p6x", "/skills/registry", "/plugins/list", "/system/config", "/system/capabilities", "/providers/status", "/stress/ping", "/app", "/app/index.html",
]


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, obj: dict):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode() or "{}")
            if isinstance(body, dict):
                return body
        except Exception:
            pass
        parsed = urllib.parse.parse_qs(raw.decode())
        return {k: v[0] for k, v in parsed.items()}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Cookie, X-Session-Cookie, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = urllib.parse.parse_qs(parsed.query)
        if path in ("/", "/health"):
            return self._json(200, {
                "ok": True,
                "service": "orbit-hub-token-exchange",
                "pool": CFG.get("user_pool_id"),
                "primary_session": CFG.get("primary_session"),
                "project_id": CFG.get("project_id"),
                "routes": ROUTES,
            })
        if path == "/auth/config":
            pub = {k: CFG[k] for k in (
                "region", "user_pool_id", "client_id", "domain_url", "auth_url",
                "token_url", "jwks_url", "oauth_scopes",
            ) if k in CFG}
            pub["redirect_uri_default"] = DEFAULT_REDIRECT
            return self._json(200, pub)
        if path == "/auth/login":
            state = (qs.get("state") or ["fuse"])[0]
            redirect = (qs.get("redirect_uri") or [None])[0]
            return self._json(200, {"authorize_url": authorize_url(state, redirect)})
        if path == "/auth/logout":
            redirect = (qs.get("redirect_uri") or [None])[0]
            return self._json(200, {"logout_url": logout_url(redirect)})
        if path == "/session/cookie":
            # GET alias: return cookie status (POST still sets). Use ?raw=1 to unmask.
            sess = _load_session()
            out = {
                "ok": True,
                "method": "GET",
                "has_cookie": bool(sess.get("session_cookie")),
                "session_id": sess.get("session_id"),
                "user_id": sess.get("user_id"),
                "sign_in_method": sess.get("sign_in_method"),
                "session_cookie_source": sess.get("session_cookie_source"),
                "hint": "POST JSON {session_cookie,...} to store; ?raw=1 unmasks cookie",
            }
            if (qs.get("raw") or ["0"])[0] == "1" and sess.get("session_cookie"):
                out["session_cookie"] = sess["session_cookie"]
            elif sess.get("session_cookie"):
                c = sess["session_cookie"]
                out["session_cookie_preview"] = (c[:8] + "…" + c[-4:]) if len(c) > 16 else "***"
            return self._json(200, out)
        if path == "/session":
            sess = _load_session()
            out = dict(sess)
            if out.get("session_cookie"):
                c = out["session_cookie"]
                out["session_cookie_preview"] = (c[:8] + "…" + c[-4:]) if len(c) > 16 else "***"
                out["session_cookie_set"] = True
                if (qs.get("raw") or ["0"])[0] != "1":
                    out.pop("session_cookie", None)
            return self._json(200, out or {"empty": True})
        if path == "/session/headers" or path == "/gateway/headers":
            h = gateway_headers()
            # mask api key in response unless raw
            out_h = dict(h)
            if (qs.get("raw") or ["0"])[0] != "1" and "x-api-key" in out_h:
                k = out_h["x-api-key"]
                out_h["x-api-key"] = (k[:6] + "…" + k[-4:]) if len(k) > 12 else "***"
            return self._json(200, {"headers": out_h, "has_session_cookie": bool(_load_session().get("session_cookie"))})
        if path == "/debug/state":
            st = {}
            if STATE_FILE.exists():
                try:
                    st = json.loads(STATE_FILE.read_text())
                except Exception:
                    st = {}
            return self._json(200, {"state": st, "session_keys": list(_load_session().keys()), "routes": ROUTES})
        if path == "/debug/session_root":
            return self._json(200, {
                "primary_session": "211e2cba-1b23-5ce8-945a-d5e158b037a2",
                "project_id": CFG.get("project_id"),
                "org": "ECHO-EC69",
                "locked": True,
            })
        if path == "/livekit/token/dry-run":
            body = {k: (v[0] if v else None) for k, v in qs.items()}
            return self._json(200, {
                "dry_run": True,
                "request_body": livekit_token_body(body),
                "candidate_urls": LIVEKIT_TOKEN_URLS,
                "headers_preview": {k: ("***" if k.lower() in ("authorization", "cookie", "x-api-key", "x-session-cookie") else v)
                                    for k, v in gateway_headers().items()},
            })
        if path in ("/create_session/sim", "/create_session", "/auth/create_session/sim"):
            body = {
                "CreateSessionRequest": {
                    "EmailAndPasswordRequest": {
                        "email": "user@example.com",
                        "clear_text_password": "***",
                        "proto": "auth_mgmt.CreateSessionRequest.EmailAndPasswordRequest",
                    },
                    "OAuth2Response": {"oauth2_cookie": "<cookie>"},
                    "IdentityTokenResponse": {"identity_token": "<jwt>", "oauth2_cookie": "<cookie>"},
                    "AppleSignInResponse": {
                        "identity_token": "<jwt>",
                        "email": "",
                        "user_id": "",
                        "oauth2_cookie": "<cookie>",
                    },
                    "OAuthDataToken": {"oauth_data_token": "", "sso_selected_user_id": ""},
                    "AntiAbuseToken": {"turnstile_token": ""},
                },
                "CreateSessionResponse": {
                    "proto": "auth_mgmt.CreateSessionResponse",
                    "session": {
                        "proto": "prod_auth.Session",
                        "session_id": "sim-session",
                        "user_id": "sim-user",
                        "user_agent": "orbit-hub",
                        "sign_in_method": "EMAIL_PASSWORD",
                        "impersonation_user_id": None,
                    },
                    "session_cookie": "session=sim; Path=/; HttpOnly",
                    "one_time_link_tokens": [],
                },
                "CreateSessionV2Response": {
                    "proto": "auth_mgmt.CreateSessionV2Response",
                    "oneof": ["session", "existing_email_sign_in_methods"],
                    "ExistingEmailSignInMethods": {
                        "sign_in_methods": ["EMAIL_PASSWORD", "GOOGLE_OAUTH2"],
                        "users": [],
                        "oauth_data_token": "",
                    },
                },
                "sign_in_method_enum": ["EMAIL_PASSWORD", "GOOGLE_OAUTH2", "X_OAUTH2", "APPLE_OAUTH2"],
                "prod_auth.User_fields": [
                    "user_id", "email", "x_user_id", "x_username", "session_tier_id",
                    "email_confirmed", "email_domain", "vercel_email", "has_password",
                    "google_email", "email_subscribed",
                ],
                "feature_flags": {"android_data_gateway_config_enabled": True},
                "source": "RE f8/* + Yi/* + h/f smali",
            }
            return self._json(200, body)

        if path == "/livekit/agent/sim":
            return self._json(200, {
                "proto": "livekit.LivekitCloudAgent.CreateAgentRequest",
                "fields": ["agentName_", "secrets_", "cpuReq_", "regions_", "replicas_", "maxReplicas_"],
                "CreateAgentRequest": {
                    "agent_name": "orbit-voice-agent",
                    "cpu_req": "500m",
                    "replicas": 1,
                    "max_replicas": 3,
                    "regions": ["us-east-1"],
                    "secrets": [],
                },
                "ops": ["CreateAgent", "DeployAgent", "UpdateAgent", "RestartAgent", "ListAgents", "RollbackAgent"],
                "dispatch": {
                    "proto": "LivekitAgentDispatch.CreateAgentDispatchRequest",
                    "request_agent_dispatch": True,
                },
                "source": "RE smali/livekit/LivekitCloudAgent$CreateAgentRequest + m2/g CreateToken",
                "live_session_triggers": [
                    "CreateTokenRequest.request_agent_dispatch=true",
                    "LivekitAgentDispatch.CreateAgentDispatchRequest",
                    "WorkerMessage / JobAssignment background path",
                    "Firebase Remote Config flag gates",
                ],
            })
        if path == "/livekit/dispatch/sim":
            return self._json(200, {
                "CreateAgentDispatchRequest": {"agent_name": "grok-voice", "room": "orbit-room", "metadata": {}},
                "background_agent": True,
                "background_synchronization": "Li/h SharedFlow + Li/s coroutines mutex",
                "not_sandbox": True,
            })
        if path == "/stress/ping":
            n = int((qs.get("n") or ["1"])[0])
            return self._json(200, {"ok": True, "n": n, "ts": time.time(), "pid": os.getpid()})



        if path in ("/api/grpc_catalog", "/api/clients"):
            return self._json(200, {
                "source": "v1.2.57 smali Grpc*Client",
                "package": "ai.x.grok / grok_api",
                "Livekit": {
                    "service": "/grok_api.Livekit",
                    "methods": ["CreateToken"],
                    "path": "/grok_api.Livekit/CreateToken",
                    "CreateTokenRequest_fields": [
                        "conversation_id", "agent_name", "session_payload",
                        "request_agent_dispatch", "livekit_url", "params"
                    ],
                    "CreateTokenResponse_fields": ["token", "request_id"],
                },
                "AgentSandbox": {
                    "service": "/grok_api.AgentSandbox",
                    "methods": ["MintPreviewToken"],
                    "path": "/grok_api.AgentSandbox/MintPreviewToken",
                    "note": "not_sandbox preview token mint for agent jobs",
                },
                "Voice": {
                    "service": "/grok_api.Voice",
                    "methods": [
                        "AlignAudio","CreateGrokCast","CreatePassphrase","CreateShareLink",
                        "CreateVoice","DeleteVoice","EditVoiceApproval","GetGrokCast",
                        "GetPassphrase","GetVoice","ListGrokCasts","ListSavedVoices",
                        "ListTopVoices","ListVoiceShareLinks","ListVoices","ListVoicesAdmin",
                        "ResolveShareLink","RevokeShareLink","SaveVoice","SearchVoices",
                        "SpeechToText","Transcribe","UnsaveVoice","UpdateVoicePersonality",
                        "UpdateVoiceVisibility","VerifyPassphrase"
                    ],
                },
                "Chat": {
                    "service": "/grok_api.Chat",
                    "methods_sample": [
                        "CreateConversation","CreateConversationAndRespond","AddResponse",
                        "AddModelResponse","AddUserResponse","AddToolResponse",
                        "GetConversation","GetConversation_V2","ListConversations",
                        "DeleteConversation","CloneConversation","GenerateTitle",
                        "FetchMemoriesV2","GetQuickAnswer","DeployApp","ListImageGenerations"
                    ],
                    "streaming": ["AddResponse","CreateConversationAndRespond"],
                },
                "AuthManagement": {"client": "auth_mgmt.AuthManagementClient / GrpcAuthManagementClient"},
                "other_clients": [
                    "Skills.ListSkills","Tools.AddToolPermission/ListPermissions/RevokeToolPermission",
                    "Media","Models","Notifications","RateLimits","Settings",
                    "SuggestionService","UserSkills","VerifiedAge","Avatars","Finance",
                    "Automations","Attestation","GrokForTeams"
                ],
                "live_session_chain": [
                    "CreateSession → session_cookie",
                    "Chat.CreateConversation (optional)",
                    "Livekit.CreateToken(request_agent_dispatch=true)",
                    "RoomInteractor connect",
                    "AgentSandbox.MintPreviewToken (optional not_sandbox)",
                    "GrokVoiceService / Voice.* runtime",
                ],
            })

        
        
        
        
        if path == "/providers/status":
            st_path = Path("/workspace/artifacts/fuse/session_status.json")
            st = json.loads(st_path.read_text()) if st_path.exists() else {}
            # never expose secrets — only booleans + public ids
            return self._json(200, {
                "aws_configured": bool(os.environ.get("AWS_ACCESS_KEY_ID")),
                "hf_configured": bool(os.environ.get("HF_TOKEN")),
                "region": os.environ.get("AWS_DEFAULT_REGION",""),
                "fuse": st,
                "cognito": {
                    "pool_id": "us-east-1_yr5vuS7Kz",
                    "pool_name": "orbit-chat-hub",
                    "domain": "orbit-echo-ec69-1yr5vus7kz",
                    "client_name": "orbit-chat-hub-web",
                    "client_id": "1t94d90dg0lc6uiemlukj98p5u",
                },
                "note": "secrets only in .provider.env / .secrets.env (mode 600); not returned here",
            })

        if path == "/system/config":
            paths = [
                Path("/workspace/artifacts/permanent/system_config/config.yaml"),
                Path("/workspace/artifacts/project/config/config.yaml"),
                Path("/root/.grok/plugins/autonomous-fullstack-delivery/config.yaml"),
            ]
            primary = next((x for x in paths if x.exists()), None)
            text = primary.read_text() if primary else ""
            return self._json(200, {
                "editable_primary": str(paths[0]),
                "mirrors": [str(x) for x in paths],
                "exists": primary is not None,
                "bytes": len(text.encode()) if text else 0,
                "raw": text,
                "note": "Edit permanent/system_config/config.yaml then GET /system/config to verify",
            })
        if path == "/system/capabilities":
            srv = Path("/root/.grok/server-skills")
            plug = Path("/root/.grok/plugins")
            skills = sorted([d.name for d in srv.iterdir() if d.is_dir()]) if srv.exists() else []
            return self._json(200, {
                "session_id": "211e2cba-1b23-5ce8-945a-d5e158b037a2",
                "mode": "orbit-chat-hub + autonomous-fullstack-delivery plugin",
                "server_skills": len(skills),
                "skill_names_sample": skills[:40],
                "plugin_skills": sum(1 for _ in plug.rglob("SKILL.md")) if plug.exists() else 0,
                "hub_routes_hint": "see /health",
                "advanced_vs_basic": {
                    "basic_grok": [
                        "chat completion",
                        "single-turn tool use",
                        "generic web search",
                        "image/video generation",
                        "no persistent multi-agent swarm",
                        "no local production hub bridge",
                        "no Grok Android DataGateway RE corpus",
                        "no skill plugin install tree",
                    ],
                    "this_system": [
                        "orbit-hub token exchange on :8787 (Cognito OAuth, session_cookie, Li/p gateway headers, LiveKit token proxy)",
                        "55-skill autonomous-fullstack-delivery plugin + 100+ server skills",
                        "editable system config.yaml (workflow phases, autonomy, deploy gates)",
                        "Parallel stress/failure-injection production testing",
                        "Smali/DEX permanent extract workspace (Grok + mixed dumps)",
                        "live_session / LiveKit / AgentSandbox route sims",
                        "multi-agent tooling blueprints + master-run-command-center",
                        "connected tools: Drive, GitHub, (Vercel blocked by team 403 — skipped)",
                        "self-healing / auto-recovery / auto-deployment skill contracts",
                        "SPA operator dashboard with Skills/Plugins tabs",
                        "permanent FUSE drive_pull roots + install inventories",
                    ],
                },
            })

        if path == "/skills/registry":
            srv = Path("/root/.grok/server-skills")
            proj = Path("/workspace/artifacts/project/skills")
            plug = Path("/root/.grok/plugins")
            def skill_names(root):
                if not root.exists(): return []
                return sorted([d.name for d in root.iterdir() if d.is_dir() and (d/"SKILL.md").exists() or (d.is_dir() and any(d.rglob("SKILL.md")))])
            return self._json(200, {
                "server_skills": skill_names(srv),
                "project_skills": skill_names(proj),
                "plugins": [d.name for d in plug.iterdir() if d.is_dir()] if plug.exists() else [],
                "plugin_skill_mds": sum(1 for _ in plug.rglob("SKILL.md")) if plug.exists() else 0,
                "server_skill_mds": sum(1 for _ in srv.rglob("SKILL.md")) if srv.exists() else 0,
                "install_source": "1FBoEzYmyRVlgYE9GDQPK-htdnws7jvwB",
                "plugin_name": "autonomous-fullstack-delivery",
                "status": "INSTALLED",
            })
        if path == "/plugins/list":
            plug = Path("/root/.grok/plugins")
            items=[]
            if plug.exists():
                for d in sorted(plug.iterdir()):
                    if not d.is_dir(): continue
                    pj=d/"plugin.json"
                    meta=json.loads(pj.read_text()) if pj.exists() else {}
                    items.append({"name": d.name, "meta": meta, "skills": sum(1 for _ in d.rglob("SKILL.md"))})
            return self._json(200, {"plugins": items})

        if path == "/extract/1p6x":
            return self._json(200, {
                "folder_id": "1P6xBOj5SIeT2MhYQg9UWgopiVO6QHcNR",
                "raw": "/workspace/artifacts/project/drive_ingest/folder_1P6xBOj5SIeT2MhYQg9UWgopiVO6QHcNR/raw",
                "extracted": "/workspace/work/extracted_shards_1P6x",
                "shards_ok": 16,
                "files_extracted": 378825,
                "identity": {
                    "primary_arsc_package": "ai.perplexity.app.android",
                    "note": "Smali shards are heavily obfuscated; 15-extras contains grokbot linux port + x/grok bots + flutter assets",
                    "string_hits": {
                        "perplexity": 3897,
                        "Firebase": 3024,
                        "oauth": 203,
                        "Cognito": 26,
                        "x.ai": 44,
                        "grok.com": 3,
                        "background_agent": 2,
                        "CreateToken/Livekit/AgentSandbox": 0
                    }
                },
                "extras_dirs": ["www","assets","aur","scripts","x/grok","ai-presets",".github"],
                "status": "EXTRACT_COMPLETE",
            })

        if path == "/livekit/voice/map":
            return self._json(200, {
                "package": "ai.x.grok.voice",
                "version_source": "extracted_v1257 grok2/grok4 smali",
                "live_session_triggers": [
                    "CreateTokenRequest.request_agent_dispatch=true",
                    "LivekitAgentDispatch.CreateAgentDispatchRequest",
                    "RoomInteractor connect + Agent job assignment",
                    "GrokVoiceService foreground",
                    "AgentSandbox gRPC session (not_sandbox flag path)",
                ],
                "background_agent": [
                    "WorkerMessage / JobAssignment (LivekitAgent)",
                    "AgentSandboxClient / GrpcAgentSandboxClient",
                    "request_agent_dispatch Boolean on CreateTokenRequest",
                ],
                "background_synchronization": [
                    "Li/h SharedFlow cache + Li/s coroutine mutex (legacy)",
                    "RoomInteractor UpdateSession",
                    "MicWatchdog / NetworkStallException recovery",
                    "DEP-04 SYNC-BUS style heartbeat aggregation (operator)",
                ],
                "RoomInteractor_exceptions": [
                    "ConnectionFailedException", "UnexpectedDisconnectException",
                    "EnableCameraException", "EnableMicException",
                    "AgentQuitUnexpectedlyException", "VoiceLimitException",
                    "UpdateSessionException", "UnexpectedException",
                ],
                "services": [
                    "GrokVoiceService", "GrokVoiceInteractionService",
                    "GrokRecognitionService", "GrokVoiceInteractionSessionService",
                ],
                "CreateTokenRequest_fields": [
                    "conversation_id", "agent_name", "session_payload",
                    "request_agent_dispatch", "livekit_url", "params",
                ],
                "clients": [
                    "LivekitClient", "GrpcLivekitClient",
                    "AgentSandboxClient", "GrpcAgentSandboxClient",
                    "AuthManagementClient", "ChatClient", "AutomationsServiceClient",
                ],
            })
        if path == "/sandbox/agent/sim":
            return self._json(200, {
                "proto": "grok_api.AgentSandboxClient",
                "grpc": "GrpcAgentSandboxClient",
                "note": "not_sandbox / AgentSandbox path for cloud agent jobs",
                "ops": ["MintPreviewToken"], "grpc_path": "/grok_api.AgentSandbox/MintPreviewToken",
                "ties": ["request_agent_dispatch", "CreateAgentRequest", "JobAssignment"],
            })
        if path == "/agents/registry":
            return self._json(200, {
                "schema": "gta.grok.future_session_merge.v3",
                "primary_session": "211e2cba-1b23-5ce8-945a-d5e158b037a2",
                "agent_count": 23,
                "teams": {
                    "deployment": ["DEP-01 ORBIT-LEAD", "DEP-02 PULSE-HEALTH", "DEP-03 SHIP-GATE",
                                   "DEP-04 SYNC-BUS", "DEP-05 DEBUG-OPTS", "DEP-06 TASK-DAEMON"],
                    "frontend": ["FE-01 UI-SHELL", "FE-02 SWARM-VIEW", "FE-03 KPI-BOARD",
                                 "FE-04 ASSET-WIRE", "FE-05 A11Y-UX", "FE-06 EXPORT-IO"],
                    "research": ["RS-01 SCOUT-WEB", "RS-02 SOURCE-MAP", "RS-03 CLAIM-SPLIT",
                                 "RS-04 REPORT-ARCH", "RS-05 DIFF-WATCH", "RS-06 SCOPE-GUARD"],
                    "learning": ["LC-01 ONBOARD", "LC-02 SKILL-LIB", "LC-03 TOOLCHAIN",
                                 "LC-04 RUNBOOK", "LC-05 DRILL"],
                },
                "individuality_locked": True,
                "source": "06_AGENT_ROLES_AND_HIERARCHY.md + master-run-command-center skill",
            })

        # SERVE_FRONTEND static UI
        if path in ("/app", "/ui", "/dashboard"):
            path = "/app/index.html"
        if path.startswith("/app/"):
            rel = path[len("/app/"):] or "index.html"
            # prevent traversal
            rel = rel.replace("..", "")
            fp = ROOT / "frontend" / rel
            if not fp.exists() or not fp.is_file():
                return self._json(404, {"error": "static_not_found", "path": rel})
            data = fp.read_bytes()
            ctype = "text/html"
            if rel.endswith(".js"):
                ctype = "application/javascript"
            elif rel.endswith(".css"):
                ctype = "text/css"
            elif rel.endswith(".json"):
                ctype = "application/json"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
            return
        return self._json(404, {"error": "not_found", "path": path})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        body = self._read_json()
        if path == "/auth/token":
            code = body.get("code")
            if not code:
                return self._json(400, {"error": "missing_code"})
            result = exchange_code(code, body.get("redirect_uri"))
            if not result.get("error"):
                sess = _load_session()
                for k in ("access_token", "id_token", "refresh_token", "expires_in", "token_type"):
                    if k in result:
                        sess[k] = result[k]
                sess["source"] = "cognito_oauth"
                if body.get("session_cookie"):
                    sess["session_cookie"] = body["session_cookie"]
                    sess["session_cookie_source"] = "auth_token_merge"
                for k in ("session_id", "user_id", "sign_in_method"):
                    if body.get(k):
                        sess[k] = body[k]
                _save_session(sess)
                result["session_stored"] = True
                _debug("auth_token", {"ok": True, "user_id": sess.get("user_id")})
            return self._json(200 if not result.get("error") else 400, result)
        if path == "/session/cookie":
            cookie = body.get("session_cookie") or body.get("cookie")
            if not cookie:
                return self._json(400, {"error": "missing_session_cookie"})
            sess = _load_session()
            sess["session_cookie"] = cookie
            sess["session_cookie_source"] = body.get("source") or "create_session"
            for k in ("session_id", "user_id", "sign_in_method", "session_status", "one_time_link_tokens"):
                if body.get(k) is not None:
                    sess[k] = body[k]
            if isinstance(body.get("session"), dict):
                sess["session"] = body["session"]
                sess.setdefault("session_id", body["session"].get("session_id"))
                sess.setdefault("user_id", body["session"].get("user_id"))
            if isinstance(body.get("user"), dict):
                sess["user"] = body["user"]
            _save_session(sess)
            _debug("session_cookie", {"session_id": sess.get("session_id"), "user_id": sess.get("user_id")})
            return self._json(200, {
                "ok": True,
                "stored": True,
                "session_id": sess.get("session_id"),
                "user_id": sess.get("user_id"),
                "sign_in_method": sess.get("sign_in_method"),
            })
        if path == "/session":
            sess = _load_session()
            sess.update({k: v for k, v in body.items() if v is not None})
            _save_session(sess)
            return self._json(200, {"ok": True, "keys": list(sess.keys())})
        if path == "/create_session/sim":
            # Simulate CreateSession response shape for hub wiring tests
            sess_id = body.get("session_id") or f"sess_{uuid.uuid4().hex[:12]}"
            user_id = body.get("user_id") or f"user_{uuid.uuid4().hex[:10]}"
            cookie = body.get("session_cookie") or f"grok_session={uuid.uuid4().hex}; Path=/; HttpOnly"
            method = body.get("sign_in_method") or "EMAIL_PASSWORD"
            user = body.get("user") or {
                "user_id": user_id,
                "email": body.get("email") or "demo@example.com",
                "display_name": body.get("display_name") or "Demo User",
                "profile_image": None,
                "given_name": body.get("given_name"),
                "family_name": body.get("family_name"),
            }
            session_obj = {
                "session_id": sess_id,
                "user_id": user_id,
                "session_status": "CONFIRMED",
                "sign_in_method": method,
            }
            sess = _load_session()
            sess.update({
                "session_cookie": cookie,
                "session_cookie_source": "create_session_sim",
                "session_id": sess_id,
                "user_id": user_id,
                "sign_in_method": method,
                "session_status": "CONFIRMED",
                "user": user,
                "session": session_obj,
            })
            _save_session(sess)
            return self._json(200, {
                "ok": True,
                "session": session_obj,
                "user": user,
                "session_cookie": cookie,
                "stored": True,
            })
        if path == "/livekit/token":
            req_body = livekit_token_body(body)
            headers = gateway_headers(extra=body.get("headers") or {})
            # dry only unless proxy=1
            if not body.get("proxy"):
                return self._json(200, {
                    "dry_run": True,
                    "hint": "set proxy=true to forward (uses session cookie + x-api-key)",
                    "request_body": req_body,
                    "candidate_urls": LIVEKIT_TOKEN_URLS,
                    "headers_used_keys": list(headers.keys()),
                })
            results = []
            for url in LIVEKIT_TOKEN_URLS:
                r = http_json("POST", url, headers, req_body, timeout=20)
                results.append(r)
                _debug("livekit_token_attempt", {"url": url, "ok": r.get("ok"), "status": r.get("status")})
                if r.get("ok"):
                    return self._json(200, {"forwarded": True, "result": r, "attempts": results})
            return self._json(502, {"forwarded": False, "attempts": results})
        if path == "/gateway/app_config":
            headers = gateway_headers()
            if not body.get("proxy"):
                return self._json(200, {
                    "dry_run": True,
                    "url": APP_CONFIG_URL,
                    "method": "GET",
                    "headers_keys": list(headers.keys()),
                    "hint": "POST {\"proxy\":true} to fetch",
                })
            r = http_json("GET", APP_CONFIG_URL, headers)
            _debug("app_config", {"ok": r.get("ok"), "status": r.get("status")})
            return self._json(200 if r.get("ok") else 502, r)
        return self._json(404, {"error": "not_found", "path": path})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path in ("/session", "/session/cookie"):
            if SESSION_FILE.exists():
                SESSION_FILE.unlink()
            return self._json(200, {"ok": True, "cleared": True})
        return self._json(404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        sys.stderr.write("[hub-token] " + (fmt % args) + "\n")


def main():
    port = int(os.environ.get("HUB_PORT", "8787"))
    if "--self-test" in sys.argv:
        print(json.dumps({
            "authorize_url": authorize_url(),
            "logout_url": logout_url(),
            "token_url": CFG["token_url"],
            "has_client_secret": bool(CLIENT_SECRET),
            "redirect": DEFAULT_REDIRECT,
            "routes": ROUTES,
            "livekit_urls": LIVEKIT_TOKEN_URLS,
        }, indent=2))
        return
    # write state
    STATE_FILE.write_text(json.dumps({
        "service": "orbit-hub-token-exchange",
        "port": port,
        "status": "listening",
        "primary_session": "211e2cba-1b23-5ce8-945a-d5e158b037a2",
        "routes": ROUTES,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=2))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(json.dumps({"listening": f"0.0.0.0:{port}", "routes": ROUTES}))
    server.serve_forever()


if __name__ == "__main__":
    main()
