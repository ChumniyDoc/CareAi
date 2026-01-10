import base64

from fastapi.testclient import TestClient

from bot.config import Settings
from bot.db.session import create_engine, create_session_factory
from bot.web.app import create_app


def _auth_headers(user: str, password: str) -> dict:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_admin_endpoints(database_url):
    settings = Settings(
        bot_token="dummy",
        database_url=database_url,
        admin_user="admin",
        admin_password="admin",
        llm_enabled=False,
    )
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    scheduler = type("Scheduler", (), {"running": True, "get_jobs": lambda self: []})()
    app = create_app(session_factory, settings, scheduler=scheduler, llm_client=None)

    with TestClient(app) as client:
        root = client.get("/", allow_redirects=False)
        assert root.status_code in (302, 307)
        health = client.get("/healthz")
        assert health.status_code == 200
        ready = client.get("/readyz")
        assert ready.status_code == 200

        headers = _auth_headers("admin", "admin")
        admin = client.get("/admin", headers=headers)
        assert admin.status_code == 200
        stats = client.get("/admin/stats.json", headers=headers)
        assert stats.status_code == 200
        selftest = client.post("/admin/selftest", headers=headers)
        assert selftest.status_code == 200
