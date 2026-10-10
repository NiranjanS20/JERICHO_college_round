"""
AgentBreak Demo Runner.

Automatically loads the pre-computed demo campaign into the database
and boots the FastAPI backend server in offline demo mode with zero API calls.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uvicorn
from httpx import ASGITransport, AsyncClient

# Force demo mode
os.environ["DEMO_MODE"] = "true"

from app.main import app
from app.db import init_db


async def preseed_demo() -> None:
    """Preseed the SQLite database with the demo cache before starting uvicorn."""
    print("=" * 80)
    print("  Starting AgentBreak in Zero-Cost Cached Demo Mode")
    print("=" * 80)
    print("[*] Initializing SQLite database...")
    await init_db()

    print("[*] Ingesting pre-run campaign findings from demo_cache/campaign_001.json...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/demo/load")
        data = res.json()
        print(f"[✓] Demo campaign '{data.get('campaign_id')}' loaded ({data.get('attacks_loaded')} attacks, {data.get('eval_matrix_rows_loaded')} eval rows).")

    print("[*] Launching API server at http://localhost:8000 ...")
    print("    - OpenAPI Docs: http://localhost:8000/docs")
    print("    - React UI    : Run 'npm run dev' inside frontend/")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(preseed_demo())
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

