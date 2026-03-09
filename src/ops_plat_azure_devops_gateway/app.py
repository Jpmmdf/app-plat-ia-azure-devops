#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, urlencode

import httpx
from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

try:
    import asgi
    from workers import WorkerEntrypoint, fetch as workers_fetch
except Exception:
    asgi = None
    WorkerEntrypoint = None
    workers_fetch = None

API_VERSION = "7.1"
DEFAULT_AZDO_ORG = None
DEFAULT_AZDO_PROJECT = None
ACCEPTANCE_CRITERIA_FIELD = "Microsoft.VSTS.Common.AcceptanceCriteria"
MARKDOWN_FORMAT_VALUE = "Markdown"
EPIC_WIT_NAME = "Epic"
FEATURE_WIT_NAME = "Feature"
PBI_WIT_NAME = "Product Backlog Item"
TASK_WIT_NAME = "Task"
AcceptanceCriteriaInput = Optional[Union[str, List[str]]]
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger("ops_plat_azure_devops_gateway")


# ---------- Models ----------
class DefaultsIn(BaseModel):
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    tags: Optional[str] = None


class BaseBacklogItemIn(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: AcceptanceCriteriaInput = None
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    tags: Optional[str] = None


class EpicCreateIn(BaseBacklogItemIn):
    pass


class FeatureCreateIn(BaseBacklogItemIn):
    parent_id: int


class PbiCreateIn(BaseBacklogItemIn):
    parent_id: int


class TaskCreateIn(BaseBacklogItemIn):
    parent_id: int


class FeatureCreateChildIn(BaseBacklogItemIn):
    pass


class PbiCreateChildIn(BaseBacklogItemIn):
    pass


class TaskCreateChildIn(BaseBacklogItemIn):
    pass


class CreateEpicsIn(BaseModel):
    defaults: DefaultsIn = Field(default_factory=DefaultsIn)
    epics: List[EpicCreateIn] = Field(default_factory=list)


class CreateFeaturesIn(BaseModel):
    defaults: DefaultsIn = Field(default_factory=DefaultsIn)
    features: List[FeatureCreateIn] = Field(default_factory=list)


class CreatePbisIn(BaseModel):
    defaults: DefaultsIn = Field(default_factory=DefaultsIn)
    pbis: List[PbiCreateIn] = Field(default_factory=list)


class CreateTasksIn(BaseModel):
    defaults: DefaultsIn = Field(default_factory=DefaultsIn)
    tasks: List[TaskCreateIn] = Field(default_factory=list)


class CreateFeaturesForEpicIn(BaseModel):
    defaults: DefaultsIn = Field(default_factory=DefaultsIn)
    features: List[FeatureCreateChildIn] = Field(default_factory=list)


class CreatePbisForFeatureIn(BaseModel):
    defaults: DefaultsIn = Field(default_factory=DefaultsIn)
    product_backlog_items: List[PbiCreateChildIn] = Field(default_factory=list)


class CreateTasksForPbiIn(BaseModel):
    defaults: DefaultsIn = Field(default_factory=DefaultsIn)
    tasks: List[TaskCreateChildIn] = Field(default_factory=list)


class CreatedItemOut(BaseModel):
    id: int
    type: str
    title: str
    url: str
    parent_id: Optional[int] = None


class BatchCreateResponse(BaseModel):
    org: str
    project: str
    created: List[CreatedItemOut]


class WorkItemOut(BaseModel):
    org: str
    project: str
    id: int
    type: str
    title: str
    url: str
    state: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    tags: Optional[str] = None
    parent_id: Optional[int] = None
    child_ids: List[int] = Field(default_factory=list)


# ---------- Azure DevOps helpers ----------
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


def _json_log(level: int, event: str, **fields: Any) -> None:
    safe_fields = {k: v for k, v in fields.items() if v is not None}
    logger.log(level, json.dumps({"event": event, **safe_fields}, ensure_ascii=True))


def _request_log_context(request: Request) -> Dict[str, Any]:
    return {
        "method": request.method,
        "path": request.url.path,
        "cf_ray": request.headers.get("cf-ray"),
        "user_agent": request.headers.get("user-agent"),
    }


def _compact_text(value: Any, *, limit: int = 800) -> str:
    if isinstance(value, str):
        text = value.strip()
    else:
        try:
            text = json.dumps(value, ensure_ascii=True)
        except Exception:
            text = str(value).strip()
    if not text:
        return "<empty>"
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"


def _runtime_error_detail(ex: Exception) -> str:
    detail = str(ex).strip()
    if detail:
        return detail
    return f"{ex.__class__.__name__} sem detalhe"


def _basic_auth_header(pat: str) -> str:
    # Azure DevOps PAT uses basic auth with empty username.
    token = f":{pat}".encode("utf-8")
    encoded = base64.b64encode(token).decode("ascii")
    return f"Basic {encoded}"


def _url_with_query_params(url: str, params: Optional[Dict[str, Any]]) -> str:
    if not params:
        return url
    pairs: List[tuple[str, str]] = []
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            for item in value:
                pairs.append((str(key), str(item)))
        else:
            pairs.append((str(key), str(value)))
    if not pairs:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{urlencode(pairs)}"


async def req(method: str, url: str, pat: str, headers=None, params=None, json_body=None, timeout=30):
    h = {
        "Accept": "application/json",
        "Authorization": _basic_auth_header(pat),
    }
    if headers:
        h.update(headers)

    try:
        if workers_fetch is not None:
            worker_url = _url_with_query_params(url, params)
            body = None if json_body is None else json.dumps(json_body, ensure_ascii=False)
            _json_log(
                logging.DEBUG,
                "azure_devops_request_dispatch",
                transport="workers_fetch",
                method=method,
                url=worker_url,
            )
            r = await workers_fetch(worker_url, method=method.upper(), headers=h, body=body)
            status_code = int(getattr(r, "status", 0))
            response_text = await r.text()
            content_type = ((r.headers.get("content-type") if getattr(r, "headers", None) else "") or "").lower()
            activity_id = (
                (r.headers.get("x-vss-e2eid") if getattr(r, "headers", None) else None)
                or (r.headers.get("activityid") if getattr(r, "headers", None) else None)
            )
        else:
            _json_log(
                logging.DEBUG,
                "azure_devops_request_dispatch",
                transport="httpx",
                method=method,
                url=url,
            )
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.request(
                    method=method,
                    url=url,
                    headers=h,
                    params=params,
                    json=json_body,
                )
            status_code = r.status_code
            response_text = r.text
            content_type = ((r.headers.get("content-type") or "")).lower()
            activity_id = r.headers.get("x-vss-e2eid") or r.headers.get("activityid")
    except Exception as ex:
        detail = _runtime_error_detail(ex)
        _json_log(
            logging.ERROR,
            "azure_devops_http_exception",
            method=method,
            url=url,
            params=params,
            detail=detail,
        )
        raise RuntimeError(f"Azure DevOps request exception - {detail}") from ex

    if status_code >= 400:
        try:
            detail = json.loads(response_text) if response_text else ""
        except Exception:
            detail = response_text
        detail_text = _compact_text(detail)
        _json_log(
            logging.ERROR,
            "azure_devops_http_error",
            method=method,
            url=url,
            params=params,
            status_code=status_code,
            content_type=content_type,
            activity_id=activity_id,
            detail=detail_text,
        )
        raise RuntimeError(f"Azure DevOps HTTP {status_code} - {detail_text}")

    if not response_text:
        return None

    if "application/json" not in content_type:
        snippet = _compact_text(response_text[:400].replace("\n", " "))
        _json_log(
            logging.ERROR,
            "azure_devops_non_json_response",
            method=method,
            url=url,
            params=params,
            status_code=status_code,
            content_type=content_type,
            snippet=snippet,
        )
        raise RuntimeError(f"Azure DevOps HTTP {status_code} - Resposta nao JSON: {snippet}")

    try:
        return json.loads(response_text)
    except ValueError as ex:
        snippet = _compact_text(response_text[:400].replace("\n", " "))
        _json_log(
            logging.ERROR,
            "azure_devops_invalid_json_response",
            method=method,
            url=url,
            params=params,
            status_code=status_code,
            content_type=content_type,
            snippet=snippet,
        )
        raise RuntimeError(f"Azure DevOps HTTP {status_code} - JSON invalido: {snippet}") from ex


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
    criteria_block = "## Criterios de Aceite\n" + render_acceptance_criteria_markdown(criteria_items)
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

    # On child items, create the relation pointing to the parent item.
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


def parse_work_item_id_from_relation_url(relation_url: str) -> Optional[int]:
    match = re.search(r"/workItems/(\d+)", relation_url)
    if not match:
        return None
    return int(match.group(1))


def extract_parent_and_children_ids(relations: Any) -> tuple[Optional[int], List[int]]:
    parent_id: Optional[int] = None
    child_ids: List[int] = []
    if not isinstance(relations, list):
        return parent_id, child_ids

    for rel in relations:
        if not isinstance(rel, dict):
            continue
        rel_type = rel.get("rel")
        rel_url = str(rel.get("url", ""))
        target_id = parse_work_item_id_from_relation_url(rel_url)
        if target_id is None:
            continue

        # Child -> Parent
        if rel_type == "System.LinkTypes.Hierarchy-Reverse":
            parent_id = target_id
        # Parent -> Child
        if rel_type == "System.LinkTypes.Hierarchy-Forward":
            child_ids.append(target_id)

    # Dedupe while preserving order.
    seen = set()
    deduped_child_ids: List[int] = []
    for child_id in child_ids:
        if child_id in seen:
            continue
        seen.add(child_id)
        deduped_child_ids.append(child_id)
    return parent_id, deduped_child_ids


async def get_work_item(
    org: str,
    project: str,
    pat: str,
    work_item_id: int,
    *,
    expand_relations: bool = True,
) -> Dict[str, Any]:
    url = ado_api_url(org, project, f"wit/workitems/{work_item_id}")
    params: Dict[str, str] = {"api-version": API_VERSION}
    if expand_relations:
        params["$expand"] = "relations"
    return await req("GET", url, pat, params=params)


def to_work_item_out(org: str, project: str, work_item: Dict[str, Any]) -> WorkItemOut:
    fields = work_item.get("fields", {}) if isinstance(work_item, dict) else {}
    wi_id = int(work_item.get("id"))
    parent_id, child_ids = extract_parent_and_children_ids(work_item.get("relations"))
    return WorkItemOut(
        org=org,
        project=project,
        id=wi_id,
        type=str(fields.get("System.WorkItemType") or ""),
        title=str(fields.get("System.Title") or ""),
        url=ui_link(org, project, wi_id),
        state=fields.get("System.State"),
        description=fields.get("System.Description"),
        acceptance_criteria=fields.get(ACCEPTANCE_CRITERIA_FIELD),
        area_path=fields.get("System.AreaPath"),
        iteration_path=fields.get("System.IterationPath"),
        tags=fields.get("System.Tags"),
        parent_id=parent_id,
        child_ids=child_ids,
    )


async def ensure_parent_work_item_type(
    org: str,
    project: str,
    pat: str,
    parent_id: int,
    expected_type: str,
) -> None:
    try:
        parent = await get_work_item(org, project, pat, parent_id, expand_relations=False)
    except RuntimeError as ex:
        detail = _runtime_error_detail(ex)
        if "HTTP 404" in detail:
            raise HTTPException(status_code=404, detail=f"Item pai {parent_id} nao encontrado.") from ex
        raise HTTPException(status_code=400, detail=detail) from ex

    fields = parent.get("fields", {}) if isinstance(parent, dict) else {}
    actual_type = fields.get("System.WorkItemType")
    if actual_type != expected_type:
        raise HTTPException(
            status_code=400,
            detail=f"Item pai {parent_id} deve ser do tipo '{expected_type}', mas foi '{actual_type}'.",
        )


def ui_link(org: str, project: str, wi_id: int) -> str:
    return f"https://dev.azure.com/{org}/{project}/_workitems/edit/{wi_id}/"


# ---------- App ----------
app = FastAPI(title="ADO Scrum Bootstrap Gateway", version="1.0.0")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def auth_or_401(x_api_key: Optional[str], gateway_api_key: Optional[str]):
    if not gateway_api_key:
        raise HTTPException(status_code=500, detail="GATEWAY_API_KEY nao configurada no servidor.")
    if not x_api_key or x_api_key != gateway_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


def resolve_item_field(item: BaseBacklogItemIn, defaults: DefaultsIn, key: str) -> Optional[str]:
    value = getattr(item, key, None)
    if value is not None:
        return value
    return getattr(defaults, key, None)


def ensure_non_empty(items: List[Any], field_name: str) -> None:
    if items:
        return
    raise HTTPException(status_code=400, detail=f"Informe ao menos um item em '{field_name}'.")


def _raise_http_400_with_log(ex: Exception, request: Request, operation: str) -> None:
    detail = _runtime_error_detail(ex)
    _json_log(logging.ERROR, "operation_failed", operation=operation, detail=detail, **_request_log_context(request))
    raise HTTPException(status_code=400, detail=detail) from ex


def runtime_context_or_500(request: Request, x_api_key: Optional[str]) -> Dict[str, str]:
    env_obj = request.scope.get("env")
    azdo_org = env_get(env_obj, "AZDO_ORG", DEFAULT_AZDO_ORG) or DEFAULT_AZDO_ORG
    azdo_project = env_get(env_obj, "AZDO_PROJECT", DEFAULT_AZDO_PROJECT) or DEFAULT_AZDO_PROJECT
    azdo_pat_env = env_get(env_obj, "AZDO_PAT")
    azdo_at_env = env_get(env_obj, "AZDO_AT")
    azdo_pat = azdo_pat_env or azdo_at_env
    gateway_api_key = env_get(env_obj, "GATEWAY_API_KEY")
    pat_source = "AZDO_PAT" if azdo_pat_env else "AZDO_AT" if azdo_at_env else "none"

    _json_log(
        logging.INFO,
        "runtime_context_resolved",
        azdo_org_set=bool(azdo_org),
        azdo_project_set=bool(azdo_project),
        azdo_pat_set=bool(azdo_pat),
        azdo_pat_source=pat_source,
        gateway_api_key_set=bool(gateway_api_key),
        **_request_log_context(request),
    )

    auth_or_401(x_api_key, gateway_api_key)

    if not azdo_org or not azdo_project:
        raise HTTPException(status_code=500, detail="AZDO_ORG e AZDO_PROJECT devem estar configurados.")

    if not azdo_pat:
        raise HTTPException(status_code=500, detail="AZDO_PAT (ou AZDO_AT) nao configurado no servidor.")

    return {"org": azdo_org, "project": azdo_project, "pat": azdo_pat}


async def resolve_acceptance_support(
    org: str,
    project: str,
    pat: str,
    wit_type: str,
    acceptance_field_cache: Dict[str, bool],
) -> bool:
    try:
        return await work_item_type_supports_field(
            org,
            project,
            pat,
            wit_type,
            ACCEPTANCE_CRITERIA_FIELD,
            acceptance_field_cache,
        )
    except RuntimeError as ex:
        _json_log(
            logging.WARNING,
            "acceptance_field_support_check_failed",
            org=org,
            project=project,
            wit_type=wit_type,
            detail=_runtime_error_detail(ex),
        )
        return False


async def create_items_batch(
    org: str,
    project: str,
    pat: str,
    defaults: DefaultsIn,
    items: List[BaseBacklogItemIn],
    wit_type: str,
    acceptance_field_cache: Dict[str, bool],
    forced_parent_id: Optional[int] = None,
) -> List[CreatedItemOut]:
    acceptance_supported = await resolve_acceptance_support(
        org,
        project,
        pat,
        wit_type,
        acceptance_field_cache,
    )
    created_items: List[CreatedItemOut] = []

    for item in items:
        area = resolve_item_field(item, defaults, "area_path") or project
        iteration = resolve_item_field(item, defaults, "iteration_path") or project
        tags = resolve_item_field(item, defaults, "tags")
        parent_id = forced_parent_id if forced_parent_id is not None else getattr(item, "parent_id", None)

        wi = await create_work_item(
            org,
            project,
            pat,
            wit_type,
            build_patch_ops(
                item.title,
                item.description,
                item.acceptance_criteria,
                acceptance_supported,
                area,
                iteration,
                tags,
                parent_id,
                org,
                project,
            ),
        )
        wi_id = int(wi["id"])
        created_items.append(
            CreatedItemOut(
                id=wi_id,
                type=wit_type,
                title=item.title,
                url=ui_link(org, project, wi_id),
                parent_id=parent_id,
            )
        )
    return created_items


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/v1/backlog/work-items/{work_item_id}", response_model=WorkItemOut)
async def get_backlog_work_item(
    work_item_id: int,
    request: Request,
    x_api_key: Optional[str] = Security(api_key_header),
):
    context = runtime_context_or_500(request, x_api_key)
    try:
        work_item = await get_work_item(
            context["org"],
            context["project"],
            context["pat"],
            work_item_id,
            expand_relations=True,
        )
    except RuntimeError as ex:
        detail = _runtime_error_detail(ex)
        if "HTTP 404" in detail:
            raise HTTPException(status_code=404, detail=f"Work Item {work_item_id} nao encontrado.") from ex
        _raise_http_400_with_log(ex, request, "get_backlog_work_item")
    return to_work_item_out(context["org"], context["project"], work_item)


@app.post("/v1/backlog/epics", response_model=BatchCreateResponse)
async def create_epics(
    payload: CreateEpicsIn,
    request: Request,
    x_api_key: Optional[str] = Security(api_key_header),
):
    context = runtime_context_or_500(request, x_api_key)
    ensure_non_empty(payload.epics, "epics")
    cache: Dict[str, bool] = {}
    try:
        created = await create_items_batch(
            context["org"],
            context["project"],
            context["pat"],
            payload.defaults,
            payload.epics,
            "Epic",
            cache,
        )
    except RuntimeError as ex:
        _raise_http_400_with_log(ex, request, "create_epics")
    return BatchCreateResponse(org=context["org"], project=context["project"], created=created)


@app.post("/v1/backlog/epics/{epic_id}/features", response_model=BatchCreateResponse)
async def create_features_for_epic(
    epic_id: int,
    payload: CreateFeaturesForEpicIn,
    request: Request,
    x_api_key: Optional[str] = Security(api_key_header),
):
    context = runtime_context_or_500(request, x_api_key)
    ensure_non_empty(payload.features, "features")
    await ensure_parent_work_item_type(
        context["org"],
        context["project"],
        context["pat"],
        epic_id,
        EPIC_WIT_NAME,
    )
    cache: Dict[str, bool] = {}
    try:
        created = await create_items_batch(
            context["org"],
            context["project"],
            context["pat"],
            payload.defaults,
            payload.features,
            FEATURE_WIT_NAME,
            cache,
            forced_parent_id=epic_id,
        )
    except RuntimeError as ex:
        _raise_http_400_with_log(ex, request, "create_features_for_epic")
    return BatchCreateResponse(org=context["org"], project=context["project"], created=created)


@app.post("/v1/backlog/features", response_model=BatchCreateResponse)
async def create_features(
    payload: CreateFeaturesIn,
    request: Request,
    x_api_key: Optional[str] = Security(api_key_header),
):
    context = runtime_context_or_500(request, x_api_key)
    ensure_non_empty(payload.features, "features")
    cache: Dict[str, bool] = {}
    try:
        created = await create_items_batch(
            context["org"],
            context["project"],
            context["pat"],
            payload.defaults,
            payload.features,
            "Feature",
            cache,
        )
    except RuntimeError as ex:
        _raise_http_400_with_log(ex, request, "create_features")
    return BatchCreateResponse(org=context["org"], project=context["project"], created=created)


@app.post("/v1/backlog/features/{feature_id}/product-backlog-items", response_model=BatchCreateResponse)
async def create_pbis_for_feature(
    feature_id: int,
    payload: CreatePbisForFeatureIn,
    request: Request,
    x_api_key: Optional[str] = Security(api_key_header),
):
    context = runtime_context_or_500(request, x_api_key)
    ensure_non_empty(payload.product_backlog_items, "product_backlog_items")
    await ensure_parent_work_item_type(
        context["org"],
        context["project"],
        context["pat"],
        feature_id,
        FEATURE_WIT_NAME,
    )
    cache: Dict[str, bool] = {}
    try:
        created = await create_items_batch(
            context["org"],
            context["project"],
            context["pat"],
            payload.defaults,
            payload.product_backlog_items,
            PBI_WIT_NAME,
            cache,
            forced_parent_id=feature_id,
        )
    except RuntimeError as ex:
        _raise_http_400_with_log(ex, request, "create_pbis_for_feature")
    return BatchCreateResponse(org=context["org"], project=context["project"], created=created)


@app.post("/v1/backlog/product-backlog-items", response_model=BatchCreateResponse)
async def create_pbis(
    payload: CreatePbisIn,
    request: Request,
    x_api_key: Optional[str] = Security(api_key_header),
):
    context = runtime_context_or_500(request, x_api_key)
    ensure_non_empty(payload.pbis, "pbis")
    cache: Dict[str, bool] = {}
    try:
        created = await create_items_batch(
            context["org"],
            context["project"],
            context["pat"],
            payload.defaults,
            payload.pbis,
            PBI_WIT_NAME,
            cache,
        )
    except RuntimeError as ex:
        _raise_http_400_with_log(ex, request, "create_pbis")
    return BatchCreateResponse(org=context["org"], project=context["project"], created=created)


@app.post("/v1/backlog/product-backlog-items/{product_backlog_item_id}/tasks", response_model=BatchCreateResponse)
async def create_tasks_for_pbi(
    product_backlog_item_id: int,
    payload: CreateTasksForPbiIn,
    request: Request,
    x_api_key: Optional[str] = Security(api_key_header),
):
    context = runtime_context_or_500(request, x_api_key)
    ensure_non_empty(payload.tasks, "tasks")
    await ensure_parent_work_item_type(
        context["org"],
        context["project"],
        context["pat"],
        product_backlog_item_id,
        PBI_WIT_NAME,
    )
    cache: Dict[str, bool] = {}
    try:
        created = await create_items_batch(
            context["org"],
            context["project"],
            context["pat"],
            payload.defaults,
            payload.tasks,
            TASK_WIT_NAME,
            cache,
            forced_parent_id=product_backlog_item_id,
        )
    except RuntimeError as ex:
        _raise_http_400_with_log(ex, request, "create_tasks_for_pbi")
    return BatchCreateResponse(org=context["org"], project=context["project"], created=created)


@app.post("/v1/backlog/tasks", response_model=BatchCreateResponse)
async def create_tasks(
    payload: CreateTasksIn,
    request: Request,
    x_api_key: Optional[str] = Security(api_key_header),
):
    context = runtime_context_or_500(request, x_api_key)
    ensure_non_empty(payload.tasks, "tasks")
    cache: Dict[str, bool] = {}
    try:
        created = await create_items_batch(
            context["org"],
            context["project"],
            context["pat"],
            payload.defaults,
            payload.tasks,
            TASK_WIT_NAME,
            cache,
        )
    except RuntimeError as ex:
        _raise_http_400_with_log(ex, request, "create_tasks")
    return BatchCreateResponse(org=context["org"], project=context["project"], created=created)


if asgi is not None and WorkerEntrypoint is not None:

    class Default(WorkerEntrypoint):
        async def fetch(self, request):
            return await asgi.fetch(app, request, self.env)
