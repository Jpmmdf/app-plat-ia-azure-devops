import importlib

from fastapi.testclient import TestClient

from server import app


client = TestClient(app)


def test_create_epics_runtime_error_without_message_returns_non_empty_detail(monkeypatch) -> None:
    monkeypatch.setenv("AZDO_ORG", "org-test")
    monkeypatch.setenv("AZDO_PROJECT", "project-test")
    monkeypatch.setenv("AZDO_PAT", "pat-test")
    monkeypatch.setenv("GATEWAY_API_KEY", "key-test")

    app_module = importlib.import_module("ops_plat_azure_devops_gateway.app")

    async def fake_create_items_batch(*args, **kwargs):
        raise RuntimeError()

    monkeypatch.setattr(app_module, "create_items_batch", fake_create_items_batch)

    response = client.post(
        "/v1/backlog/epics",
        headers={"X-API-Key": "key-test"},
        json={"epics": [{"title": "epic teste"}]},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "RuntimeError sem detalhe"}
