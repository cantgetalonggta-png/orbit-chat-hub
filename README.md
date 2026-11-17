# ORBIT Chat Hub / Bridge

Production-ready Cognito OAuth + session_cookie + LiveKit token bridge reverse-engineered from Grok Android (com.xai.grok).

- **Primary session:** `211e2cba-1b23-5ce8-945a-d5e158b037a2`
- **Team:** echo-ec69 / `team_kgQcPVmumwtmK3MdAGlxKJtg`
- **Hub:** Python `token_exchange.py` on `:8787` (see `hub/`)
- **Frontend SPA:** static files under `frontend/` (also served at hub `/app/`)

## Quick start
```bash
cd hub
export COGNITO_CLIENT_SECRET=...   # optional
export GROK_X_API_KEY=...          # optional override
python3 token_exchange.py --self-test
python3 token_exchange.py          # listens 0.0.0.0:8787
# open http://127.0.0.1:8787/app/
```

## Key routes
- `/auth/*` Cognito OAuth code exchange
- `/session/cookie` store CreateSession cookie
- `/gateway/headers` Li/p DataGateway header reconstruction
- `/livekit/token` CreateTokenRequest (+ `proxy=true`)
- `/livekit/agent/sim` CloudAgent CreateAgent fields
- `/create_session/sim` auth_mgmt oneof + prod_auth.User
- `/stress/ping` multi-worker stress

## RE map
DataGateway: credentials → Li/s retry → Li/v → Li/p → Li/a → Li/h → Li/o → Li/I  
Flag: `android_data_gateway_config_enabled`  
Live session triggers: `request_agent_dispatch` + AgentDispatch + WorkerMessage

See `manual/ORBIT_COMPLETE_OPERATOR_MANUAL.md`.
