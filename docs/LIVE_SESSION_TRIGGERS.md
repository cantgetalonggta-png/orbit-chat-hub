# Live Session Triggers (decoded)

## APK
- package: `ai.x.grok` · version `1.2.57-release.01` (from drive manifest)

## CreateTokenRequest
conversation_id · agent_name · session_payload · **request_agent_dispatch** · livekit_url · params

## Trigger chain (not_sandbox)
1. Auth → CreateSession → session_cookie
2. POST LiveKit token with `request_agent_dispatch=true`
3. AgentDispatch / JobAssignment
4. RoomInteractor connects (exceptions cataloged)
5. Optional AgentSandbox gRPC job
6. GrokVoiceService holds session; UpdateSession syncs

## Hub debug
- `GET /livekit/voice/map`
- `GET /livekit/agent/sim` · `GET /livekit/dispatch/sim`
- `GET /sandbox/agent/sim`
- `POST /livekit/token` with `proxy=true` (needs real session_cookie)

## Operator swarm
`GET /agents/registry` — 23 agents future_session_merge v3
