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


def test_create_tasks_batch_limit_exceeded_returns_400(monkeypatch) -> None:
    monkeypatch.setenv("AZDO_ORG", "org-test")
    monkeypatch.setenv("AZDO_PROJECT", "project-test")
    monkeypatch.setenv("AZDO_PAT", "pat-test")
    monkeypatch.setenv("GATEWAY_API_KEY", "key-test")

    tasks = [{"title": f"task-{i}", "parent_id": 1} for i in range(26)]
    response = client.post(
        "/v1/backlog/tasks",
        headers={"X-API-Key": "key-test"},
        json={"tasks": tasks},
    )

    assert response.status_code == 400
    assert "Limite por requisicao excedido" in response.json()["detail"]
    assert "maximo 25" in response.json()["detail"]


def test_create_epics_returns_failed_items_without_aborting_batch(monkeypatch) -> None:
    monkeypatch.setenv("AZDO_ORG", "org-test")
    monkeypatch.setenv("AZDO_PROJECT", "project-test")
    monkeypatch.setenv("AZDO_PAT", "pat-test")
    monkeypatch.setenv("GATEWAY_API_KEY", "key-test")

    app_module = importlib.import_module("ops_plat_azure_devops_gateway.app")

    async def fake_create_items_batch(*args, **kwargs):
        return (
            [
                app_module.CreatedItemOut(
                    id=999,
                    type="Epic",
                    title="Epic OK",
                    url="https://dev.azure.com/org/project/_workitems/edit/999/",
                    parent_id=None,
                )
            ],
            [
                app_module.FailedItemOut(
                    type="Epic",
                    title="Epic com falha",
                    parent_id=None,
                    error="Azure DevOps HTTP 400 - erro simulado",
                )
            ],
        )

    monkeypatch.setattr(app_module, "create_items_batch", fake_create_items_batch)

    response = client.post(
        "/v1/backlog/epics",
        headers={"X-API-Key": "key-test"},
        json={"epics": [{"title": "Epic OK"}, {"title": "Epic com falha"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["created"]) == 1
    assert len(body["failed"]) == 1
    assert body["failed"][0]["title"] == "Epic com falha"
