# ORBIT Complete Operator Manual (Production)

Hub :8787 production-ready. SPA at /app/. See PRODUCTION_STATUS.json and README.

## Routes
GET /health, /auth/*, /session*, /gateway/*, /livekit/*, /create_session/sim, /stress/ping, /debug/*, /app/*

POST /auth/token, /session/cookie, /livekit/token (proxy=true), /gateway/app_config, /create_session/sim

## RE
DataGateway Li/s→Li/v→Li/p→Li/a→Li/h→Li/o→Li/I
CreateTokenRequest fields + CloudAgent CreateAgent + dispatch triggers
Flag android_data_gateway_config_enabled

## Stress
84/84 OK parallel 64 ~1.2s
