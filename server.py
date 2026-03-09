#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

import httpx
from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

try:
    import asgi
    from workers import WorkerEntrypoint
except Exception:
    asgi = None
    WorkerEntrypoint = None

API_VERSION = "7.1"
DEFAULT_AZDO_ORG = None
DEFAULT_AZDO_PROJECT = None
ACCEPTANCE_CRITERIA_FIELD = "Microsoft.VSTS.Common.AcceptanceCriteria"
SCRUM_WIT_TYPES = ("Epic", "Feature", "Product Backlog Item", "Task")
AcceptanceCriteriaInput = Optional[Union[str, List[str]]]
MARKDOWN_FORMAT_VALUE = "Markdown"


# ---------- Modelos ----------
class TaskIn(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: AcceptanceCriteriaInput = None


class PbiIn(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: AcceptanceCriteriaInput = None
    tasks: List[TaskIn] = Field(default_factory=list)


class FeatureIn(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: AcceptanceCriteriaInput = None
    pbis: List[PbiIn] = Field(default_factory=list)


class EpicIn(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: AcceptanceCriteriaInput = None
    features: List[FeatureIn] = Field(default_factory=list)


class DefaultsIn(BaseModel):
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    tags: Optional[str] = None


class PlanIn(BaseModel):
    defaults: DefaultsIn = Field(default_factory=DefaultsIn)
    epics: List[EpicIn] = Field(default_factory=list)


class ExecuteResponse(BaseModel):
    org: str
    project: str
    created: Dict[str, Any]


# ---------- Helpers Azure DevOps ----------
def ado_api_url(org: str, project: str, path: str) -> str:
    return f"https://dev.azure.com/{org}/{project}/_apis/{path}"


def env_get(env_obj: Any, key: str, default: Optional[str] = None) -> Optional[str]:
    if env_obj is None:
        return os.getenv(key, default)

    value = getattr(env_obj, key, None)
    if value is not None:
        return value

    if isinstance(env_obj, dict):
        return env_obj.get(key, default)

    getter = getattr(env_obj, "get", None)
    if callable(getter):
        try:
            value = getter(key, default)
            if value is not None:
                return value
        except TypeError:
            pass

    return os.getenv(key, default)


async def req(method: str, url: str, pat: str, headers=None, params=None, json_body=None, timeout=30):
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)

    async with httpx.AsyncClient(timeout=timeout, auth=httpx.BasicAuth("", pat)) as client:
        r = await client.request(
            method=method,
            url=url,
            headers=h,
            params=params,
            json=json_body,
        )

    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"HTTP {r.status_code} - {detail}")

    if not r.text:
        return None

    content_type = (r.headers.get("content-type") or "").lower()
    if "application/json" not in content_type:
        snippet = r.text[:400].strip().replace("\n", " ")
        raise RuntimeError(f"HTTP {r.status_code} - Resposta nao JSON do Azure DevOps: {snippet}")

    try:
        return r.json()
    except ValueError as ex:
        snippet = r.text[:400].strip().replace("\n", " ")
        raise RuntimeError(f"HTTP {r.status_code} - JSON invalido do Azure DevOps: {snippet}") from ex


def normalize_tags(tags: Optional[str]) -> Optional[str]:
    if not tags:
        return None
    return "; ".join([t.strip() for t in tags.replace(",", ";").split(";") if t.strip()])


def normalize_acceptance_criteria(acceptance_criteria: AcceptanceCriteriaInput) -> List[str]:
    if acceptance_criteria is None:
        return []

    if isinstance(acceptance_criteria, str):
        candidates = [line.strip() for line in acceptance_criteria.splitlines() if line.strip()]
    else:
        candidates = [str(item).strip() for item in acceptance_criteria if str(item).strip()]

    normalized: List[str] = []
    seen = set()
    for item in candidates:
        cleaned = item
        if cleaned.startswith("- [ ] "):
            cleaned = cleaned[6:]
        elif cleaned.startswith("- [x] ") or cleaned.startswith("- [X] "):
            cleaned = cleaned[6:]
        elif cleaned.startswith("- "):
            cleaned = cleaned[2:]
        elif cleaned.startswith("* "):
            cleaned = cleaned[2:]

        cleaned = cleaned.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)

    return normalized


def render_acceptance_criteria_markdown(criteria_items: List[str]) -> str:
    return "\n".join([f"- [ ] {item}" for item in criteria_items])


def append_acceptance_criteria_to_description(
    description: Optional[str],
    criteria_items: List[str],
) -> str:
    criteria_block = "## Critérios de Aceite\n" + render_acceptance_criteria_markdown(criteria_items)
    if description and description.strip():
        return f"{description.rstrip()}\n\n{criteria_block}"
    return criteria_block


def add_markdown_format_op(ops: List[Dict[str, Any]], field_reference_name: str) -> None:
    ops.append(
        {
            "op": "add",
            "path": f"/multilineFieldsFormat/{field_reference_name}",
            "value": MARKDOWN_FORMAT_VALUE,
        }
    )


async def work_item_type_supports_field(
    org: str,
    project: str,
    pat: str,
    wit_type: str,
    field_reference_name: str,
    cache: Dict[str, bool],
) -> bool:
    cache_key = f"{wit_type}::{field_reference_name}"
    if cache_key in cache:
        return cache[cache_key]

    encoded_wit_type = quote(wit_type, safe="")
    url = ado_api_url(org, project, f"wit/workitemtypes/{encoded_wit_type}/fields")
    data = await req("GET", url, pat, params={"api-version": API_VERSION})
    supported = any(
        isinstance(field, dict) and field.get("referenceName") == field_reference_name
        for field in (data or {}).get("value", [])
    )
    cache[cache_key] = supported
    return supported


def build_patch_ops(
    title: str,
    description: Optional[str],
    acceptance_criteria: AcceptanceCriteriaInput,
    acceptance_field_supported: bool,
    area_path: Optional[str],
    iteration_path: Optional[str],
    tags: Optional[str],
    parent_id: Optional[int],
    org: str,
    project: str,
) -> List[Dict[str, Any]]:
    criteria_items = normalize_acceptance_criteria(acceptance_criteria)
    description_value = description
    if criteria_items and not acceptance_field_supported:
        description_value = append_acceptance_criteria_to_description(description, criteria_items)

    ops: List[Dict[str, Any]] = [{"op": "add", "path": "/fields/System.Title", "value": title}]
    if description_value:
        ops.append({"op": "add", "path": "/fields/System.Description", "value": description_value})
        add_markdown_format_op(ops, "System.Description")
    if criteria_items and acceptance_field_supported:
        ops.append(
            {
                "op": "add",
                "path": f"/fields/{ACCEPTANCE_CRITERIA_FIELD}",
                "value": render_acceptance_criteria_markdown(criteria_items),
            }
        )
        add_markdown_format_op(ops, ACCEPTANCE_CRITERIA_FIELD)
    if area_path:
        ops.append({"op": "add", "path": "/fields/System.AreaPath", "value": area_path})
    if iteration_path:
        ops.append({"op": "add", "path": "/fields/System.IterationPath", "value": iteration_path})
    if tags:
        ops.append({"op": "add", "path": "/fields/System.Tags", "value": normalize_tags(tags)})

    # Hierarquia: no FILHO, adiciona relação apontando para o PAI
    # rel: System.LinkTypes.Hierarchy-Reverse :contentReference[oaicite:2]{index=2}
    if parent_id is not None:
        parent_url = ado_api_url(org, project, f"wit/workItems/{parent_id}")
        ops.append(
            {
                "op": "add",
                "path": "/relations/-",
                "value": {"rel": "System.LinkTypes.Hierarchy-Reverse", "url": parent_url},
            }
        )
    return ops


async def create_work_item(org: str, project: str, pat: str, wit_type: str, patch_ops: List[Dict[str, Any]]):
    url = ado_api_url(org, project, f"wit/workitems/${wit_type}")
    return await req(
        "POST",
        url,
        pat,
        headers={"Content-Type": "application/json-patch+json"},
        params={"api-version": API_VERSION},
        json_body=patch_ops,
    )


def ui_link(org: str, project: str, wi_id: int) -> str:
    return f"https://dev.azure.com/{org}/{project}/_workitems/edit/{wi_id}/"


# ---------- App ----------
app = FastAPI(title="ADO Scrum Bootstrap Gateway", version="1.0.0")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def auth_or_401(x_api_key: Optional[str], gateway_api_key: Optional[str]):
    if not gateway_api_key:
        raise HTTPException(status_code=500, detail="GATEWAY_API_KEY não configurada no servidor.")
    if not x_api_key or x_api_key != gateway_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/v1/scrum/execute", response_model=ExecuteResponse)
async def execute_scrum(
    plan: PlanIn,
    request: Request,
    x_api_key: Optional[str] = Security(api_key_header),
):
    env_obj = request.scope.get("env")
    azdo_org = env_get(env_obj, "AZDO_ORG", DEFAULT_AZDO_ORG) or DEFAULT_AZDO_ORG
    azdo_project = env_get(env_obj, "AZDO_PROJECT", DEFAULT_AZDO_PROJECT) or DEFAULT_AZDO_PROJECT
    azdo_pat = env_get(env_obj, "AZDO_PAT") or env_get(env_obj, "AZDO_AT")
    gateway_api_key = env_get(env_obj, "GATEWAY_API_KEY")

    auth_or_401(x_api_key, gateway_api_key)

    if not azdo_org or not azdo_project:
        raise HTTPException(status_code=500, detail="AZDO_ORG e AZDO_PROJECT devem estar configurados.")

    if not azdo_pat:
        raise HTTPException(status_code=500, detail="AZDO_PAT (ou AZDO_AT) não configurado no servidor.")

    defaults = plan.defaults
    area = defaults.area_path or azdo_project
    iteration = defaults.iteration_path or azdo_project
    tags = defaults.tags

    result: Dict[str, Any] = {"epics": []}
    acceptance_field_cache: Dict[str, bool] = {}
    acceptance_field_support: Dict[str, bool] = {}
    for wit_type in SCRUM_WIT_TYPES:
        try:
            acceptance_field_support[wit_type] = await work_item_type_supports_field(
                azdo_org,
                azdo_project,
                azdo_pat,
                wit_type,
                ACCEPTANCE_CRITERIA_FIELD,
                acceptance_field_cache,
            )
        except RuntimeError:
            acceptance_field_support[wit_type] = False

    try:
        for e in plan.epics:
            epic = await create_work_item(
                azdo_org,
                azdo_project,
                azdo_pat,
                "Epic",
                build_patch_ops(
                    e.title,
                    e.description,
                    e.acceptance_criteria,
                    acceptance_field_support.get("Epic", False),
                    area,
                    iteration,
                    tags,
                    None,
                    azdo_org,
                    azdo_project,
                ),
            )
            epic_id = int(epic["id"])
            epic_out = {"id": epic_id, "title": e.title, "url": ui_link(azdo_org, azdo_project, epic_id), "features": []}

            for f in e.features:
                feature = await create_work_item(
                    azdo_org,
                    azdo_project,
                    azdo_pat,
                    "Feature",
                    build_patch_ops(
                        f.title,
                        f.description,
                        f.acceptance_criteria,
                        acceptance_field_support.get("Feature", False),
                        area,
                        iteration,
                        tags,
                        epic_id,
                        azdo_org,
                        azdo_project,
                    ),
                )
                feature_id = int(feature["id"])
                feat_out = {"id": feature_id, "title": f.title, "url": ui_link(azdo_org, azdo_project, feature_id), "pbis": []}

                for p in f.pbis:
                    pbi = await create_work_item(
                        azdo_org,
                        azdo_project,
                        azdo_pat,
                        "Product Backlog Item",
                        build_patch_ops(
                            p.title,
                            p.description,
                            p.acceptance_criteria,
                            acceptance_field_support.get("Product Backlog Item", False),
                            area,
                            iteration,
                            tags,
                            feature_id,
                            azdo_org,
                            azdo_project,
                        ),
                    )
                    pbi_id = int(pbi["id"])
                    pbi_out = {"id": pbi_id, "title": p.title, "url": ui_link(azdo_org, azdo_project, pbi_id), "tasks": []}

                    for t in p.tasks:
                        task = await create_work_item(
                            azdo_org,
                            azdo_project,
                            azdo_pat,
                            "Task",
                            build_patch_ops(
                                t.title,
                                t.description,
                                t.acceptance_criteria,
                                acceptance_field_support.get("Task", False),
                                area,
                                iteration,
                                tags,
                                pbi_id,
                                azdo_org,
                                azdo_project,
                            ),
                        )
                        task_id = int(task["id"])
                        pbi_out["tasks"].append({"id": task_id, "title": t.title, "url": ui_link(azdo_org, azdo_project, task_id)})

                    feat_out["pbis"].append(pbi_out)

                epic_out["features"].append(feat_out)

            result["epics"].append(epic_out)

    except RuntimeError as ex:
        raise HTTPException(status_code=400, detail=str(ex)) from ex

    return ExecuteResponse(org=azdo_org, project=azdo_project, created=result)


if asgi is not None and WorkerEntrypoint is not None:
    class Default(WorkerEntrypoint):
        async def fetch(self, request):
            return await asgi.fetch(app, request, self.env)
