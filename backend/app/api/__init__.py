"""HTTP layer.

Thin routers that translate between FastAPI and the harness. Domain logic
belongs in skills, not here. The convention going forward:

- /health           — public, liveness probe
- /sessions         — auth-protected, drives the harness AgentLoop

Routers register themselves via app.api.routers (see app/main.py).
"""
