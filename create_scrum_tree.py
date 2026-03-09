#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth


API_VERSION = "7.1"
ACCEPTANCE_CRITERIA_FIELD = "Microsoft.VSTS.Common.AcceptanceCriteria"
MARKDOWN_FORMAT_VALUE = "Markdown"


# Aliases comuns (se seu agente gerar "PBI", a gente traduz pro nome real no Scrum)
WIT_ALIASES = {
    "EPIC": "Epic",
    "FEATURE": "Feature",
    "PBI": "Product Backlog Item",
    "PRODUCTBACKLOGITEM": "Product Backlog Item",
    "TASK": "Task",
}


def ado_api_url(org: str, project: str, path: str) -> str:
    return f"https://dev.azure.com/{org}/{project}/_apis/{path}"


def req(
    method: str,
    url: str,
    pat: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Any = None,
    timeout: int = 30,
) -> Any:
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)

    r = requests.request(
        method=method,
        url=url,
        headers=h,
        params=params,
        json=json_body,
        auth=HTTPBasicAuth("", pat),
        timeout=timeout,
    )

    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"HTTP {r.status_code} - {url}\n{detail}")

    if not r.text:
        return None

    content_type = (r.headers.get("content-type") or "").lower()
    if "application/json" not in content_type:
        snippet = r.text[:400].strip().replace("\n", " ")
        raise RuntimeError(f"HTTP {r.status_code} - {url}\nResposta nao JSON do Azure DevOps: {snippet}")

    try:
        return r.json()
    except ValueError as ex:
        snippet = r.text[:400].strip().replace("\n", " ")
        raise RuntimeError(f"HTTP {r.status_code} - {url}\nJSON invalido do Azure DevOps: {snippet}") from ex


def list_project_work_item_types(org: str, project: str, pat: str) -> List[str]:
    # Lista tipos de Work Item do projeto (útil pra validar se Epic/Feature/PBI/Task existem)
    # GET .../{project}/_apis/wit/workitemtypes?api-version=7.1
    url = ado_api_url(org, project, "wit/workitemtypes")
    data = req("GET", url, pat, params={"api-version": API_VERSION})
    return sorted([x["name"] for x in data.get("value", [])])


def normalize_wit_name(name: str) -> str:
    if not name:
        return name
    key = name.strip().replace(" ", "").upper()
    return WIT_ALIASES.get(key, name.strip())


def normalize_parent_id(parent_id: Any) -> Optional[int]:
    if parent_id is None or parent_id == "":
        return None
    try:
        return int(parent_id)
    except (TypeError, ValueError) as ex:
        raise ValueError(f"parent_id inválido: {parent_id}") from ex


def required_wits_from_tree(data: Dict[str, Any]) -> Set[str]:
    required: Set[str] = set()
    for epic in data.get("epics", []) or []:
        required.add("Epic")
        for feature in epic.get("features", []) or []:
            required.add("Feature")
            for pbi in feature.get("pbis", []) or []:
                pbi_type = normalize_wit_name(pbi.get("type", "Product Backlog Item"))
                if not pbi_type:
                    raise ValueError("Campo inválido: pbi.type não pode ser vazio.")
                required.add(pbi_type)
                if pbi.get("tasks"):
                    required.add("Task")
    return required


def required_wits_from_items(items: List[Dict[str, Any]]) -> Set[str]:
    required: Set[str] = set()
    for index, item in enumerate(items):
        wit_name = normalize_wit_name(str(item.get("type", "")).strip())
        if not wit_name:
            raise ValueError(f"items[{index}].type é obrigatório.")
        required.add(wit_name)
    return required


def validate_required_wits(required_wits: Set[str], project_wits: Set[str]) -> None:
    missing = sorted(list(required_wits - project_wits))
    if not missing:
        return

    raise RuntimeError(
        "⚠️ Seu projeto não tem alguns WITs esperados: "
        + ", ".join(missing)
        + "\nTipos disponíveis no projeto: "
        + ", ".join(sorted(project_wits))
        + "\nDica: pode ser outro processo (Agile/Basic) ou WITs customizados."
    )


def normalize_acceptance_criteria(acceptance_criteria: Optional[Union[str, List[str]]]) -> List[str]:
    if acceptance_criteria is None:
        return []

    if isinstance(acceptance_criteria, str):
        raw_items = [line.strip() for line in acceptance_criteria.splitlines() if line.strip()]
    else:
        raw_items = [str(item).strip() for item in acceptance_criteria if str(item).strip()]

    normalized: List[str] = []
    seen = set()
    for item in raw_items:
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


def work_item_type_supports_field(
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
    try:
        data = req("GET", url, pat, params={"api-version": API_VERSION})
        supported = any(
            isinstance(field, dict) and field.get("referenceName") == field_reference_name
            for field in (data or {}).get("value", [])
        )
    except RuntimeError:
        supported = False
    cache[cache_key] = supported
    return supported


def build_patch_ops(
    title: str,
    description: Optional[str] = None,
    acceptance_criteria: Optional[Union[str, List[str]]] = None,
    acceptance_field_supported: bool = False,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
    tags: Optional[str] = None,
    parent_id: Optional[int] = None,
    org: Optional[str] = None,
    project: Optional[str] = None,
) -> List[Dict[str, Any]]:
    criteria_items = normalize_acceptance_criteria(acceptance_criteria)
    description_value = description
    if criteria_items and not acceptance_field_supported:
        description_value = append_acceptance_criteria_to_description(description, criteria_items)

    ops: List[Dict[str, Any]] = [
        {"op": "add", "path": "/fields/System.Title", "value": title},
    ]

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
        normalized = "; ".join([t.strip() for t in tags.replace(",", ";").split(";") if t.strip()])
        ops.append({"op": "add", "path": "/fields/System.Tags", "value": normalized})

    # Link hierárquico: no CHILD, adicionar relação apontando para o PARENT.
    # rel: System.LinkTypes.Hierarchy-Reverse
    if parent_id is not None:
        if not org or not project:
            raise ValueError("org/project são obrigatórios para criar relações de hierarquia.")
        parent_url = ado_api_url(org, project, f"wit/workItems/{parent_id}")
        ops.append(
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": parent_url,
                },
            }
        )

    return ops


def create_work_item(
    org: str,
    project: str,
    pat: str,
    wit_type: str,
    patch_ops: List[Dict[str, Any]],
    validate_only: bool = False,
) -> Dict[str, Any]:
    # POST .../_apis/wit/workitems/$Type?api-version=7.1
    # Content-Type: application/json-patch+json
    url = ado_api_url(org, project, f"wit/workitems/${wit_type}")
    headers = {"Content-Type": "application/json-patch+json"}

    params = {"api-version": API_VERSION}
    if validate_only:
        params["validateOnly"] = "true"

    return req("POST", url, pat, headers=headers, params=params, json_body=patch_ops)


def get_with_defaults(node: Dict[str, Any], defaults: Dict[str, Any], key: str) -> Optional[str]:
    v = node.get(key)
    if v is None:
        v = defaults.get(key)
    return v


def create_independent_item(
    org: str,
    project: str,
    pat: str,
    defaults: Dict[str, Any],
    item: Dict[str, Any],
    acceptance_field_cache: Dict[str, bool],
    validate_only: bool,
) -> Dict[str, Any]:
    wit_name = normalize_wit_name(str(item.get("type", "")).strip())
    if not wit_name:
        raise ValueError("Campo obrigatório ausente: type.")

    title = str(item.get("title", "")).strip()
    if not title:
        raise ValueError(f"Campo obrigatório ausente: title (type={wit_name}).")

    parent_id = normalize_parent_id(item.get("parent_id"))
    acceptance_supported = work_item_type_supports_field(
        org,
        project,
        pat,
        wit_name,
        ACCEPTANCE_CRITERIA_FIELD,
        acceptance_field_cache,
    )

    patch = build_patch_ops(
        title=title,
        description=item.get("description"),
        acceptance_criteria=item.get("acceptance_criteria"),
        acceptance_field_supported=acceptance_supported,
        area_path=get_with_defaults(item, defaults, "area_path"),
        iteration_path=get_with_defaults(item, defaults, "iteration_path"),
        tags=get_with_defaults(item, defaults, "tags"),
        parent_id=parent_id,
        org=org,
        project=project,
    )
    wi = create_work_item(org, project, pat, wit_name, patch, validate_only=validate_only)
    wi_id = wi.get("id")
    return {"id": int(wi_id) if wi_id is not None else None, "type": wit_name, "title": title}


def print_created_item(org: str, project: str, created: Dict[str, Any], index: Optional[int] = None) -> None:
    index_prefix = f"[{index}] " if index is not None else ""
    wi_id = created["id"]
    if wi_id is None:
        print(f"✅ {index_prefix}{created['type']} validado: {created['title']}")
        return
    print(f"✅ {index_prefix}{created['type']} #{wi_id}: {created['title']}")
    print(f"   UI: https://dev.azure.com/{org}/{project}/_workitems/edit/{wi_id}/")


def create_task(
    org: str,
    project: str,
    pat: str,
    defaults: Dict[str, Any],
    task: Dict[str, Any],
    parent_pbi_id: int,
    acceptance_field_cache: Dict[str, bool],
    validate_only: bool,
) -> int:
    title = task["title"]
    acceptance_supported = work_item_type_supports_field(
        org,
        project,
        pat,
        "Task",
        ACCEPTANCE_CRITERIA_FIELD,
        acceptance_field_cache,
    )
    patch = build_patch_ops(
        title=title,
        description=task.get("description"),
        acceptance_criteria=task.get("acceptance_criteria"),
        acceptance_field_supported=acceptance_supported,
        area_path=get_with_defaults(task, defaults, "area_path"),
        iteration_path=get_with_defaults(task, defaults, "iteration_path"),
        tags=get_with_defaults(task, defaults, "tags"),
        parent_id=parent_pbi_id,
        org=org,
        project=project,
    )
    wi = create_work_item(org, project, pat, "Task", patch, validate_only=validate_only)
    return int(wi["id"])


def create_pbi(
    org: str,
    project: str,
    pat: str,
    defaults: Dict[str, Any],
    pbi: Dict[str, Any],
    parent_feature_id: int,
    acceptance_field_cache: Dict[str, bool],
    validate_only: bool,
) -> int:
    wit_name = normalize_wit_name(pbi.get("type", "Product Backlog Item"))
    title = pbi["title"]
    acceptance_supported = work_item_type_supports_field(
        org,
        project,
        pat,
        wit_name,
        ACCEPTANCE_CRITERIA_FIELD,
        acceptance_field_cache,
    )
    patch = build_patch_ops(
        title=title,
        description=pbi.get("description"),
        acceptance_criteria=pbi.get("acceptance_criteria"),
        acceptance_field_supported=acceptance_supported,
        area_path=get_with_defaults(pbi, defaults, "area_path"),
        iteration_path=get_with_defaults(pbi, defaults, "iteration_path"),
        tags=get_with_defaults(pbi, defaults, "tags"),
        parent_id=parent_feature_id,
        org=org,
        project=project,
    )
    wi = create_work_item(org, project, pat, wit_name, patch, validate_only=validate_only)
    pbi_id = int(wi["id"])

    for t in pbi.get("tasks", []) or []:
        tid = create_task(
            org,
            project,
            pat,
            defaults,
            t,
            parent_pbi_id=pbi_id,
            acceptance_field_cache=acceptance_field_cache,
            validate_only=validate_only,
        )
        print(f"    ✅ Task #{tid}: {t['title']}")

    return pbi_id


def create_feature(
    org: str,
    project: str,
    pat: str,
    defaults: Dict[str, Any],
    feature: Dict[str, Any],
    parent_epic_id: int,
    acceptance_field_cache: Dict[str, bool],
    validate_only: bool,
) -> int:
    title = feature["title"]
    acceptance_supported = work_item_type_supports_field(
        org,
        project,
        pat,
        "Feature",
        ACCEPTANCE_CRITERIA_FIELD,
        acceptance_field_cache,
    )
    patch = build_patch_ops(
        title=title,
        description=feature.get("description"),
        acceptance_criteria=feature.get("acceptance_criteria"),
        acceptance_field_supported=acceptance_supported,
        area_path=get_with_defaults(feature, defaults, "area_path"),
        iteration_path=get_with_defaults(feature, defaults, "iteration_path"),
        tags=get_with_defaults(feature, defaults, "tags"),
        parent_id=parent_epic_id,
        org=org,
        project=project,
    )
    wi = create_work_item(org, project, pat, "Feature", patch, validate_only=validate_only)
    feature_id = int(wi["id"])

    for pbi in feature.get("pbis", []) or []:
        pid = create_pbi(
            org,
            project,
            pat,
            defaults,
            pbi,
            parent_feature_id=feature_id,
            acceptance_field_cache=acceptance_field_cache,
            validate_only=validate_only,
        )
        print(f"  ✅ PBI #{pid}: {pbi['title']}")

    return feature_id


def create_epic(
    org: str,
    project: str,
    pat: str,
    defaults: Dict[str, Any],
    epic: Dict[str, Any],
    acceptance_field_cache: Dict[str, bool],
    validate_only: bool,
) -> int:
    title = epic["title"]
    acceptance_supported = work_item_type_supports_field(
        org,
        project,
        pat,
        "Epic",
        ACCEPTANCE_CRITERIA_FIELD,
        acceptance_field_cache,
    )
    patch = build_patch_ops(
        title=title,
        description=epic.get("description"),
        acceptance_criteria=epic.get("acceptance_criteria"),
        acceptance_field_supported=acceptance_supported,
        area_path=get_with_defaults(epic, defaults, "area_path"),
        iteration_path=get_with_defaults(epic, defaults, "iteration_path"),
        tags=get_with_defaults(epic, defaults, "tags"),
    )
    wi = create_work_item(org, project, pat, "Epic", patch, validate_only=validate_only)
    epic_id = int(wi["id"])

    for f in epic.get("features", []) or []:
        fid = create_feature(
            org,
            project,
            pat,
            defaults,
            f,
            parent_epic_id=epic_id,
            acceptance_field_cache=acceptance_field_cache,
            validate_only=validate_only,
        )
        print(f"✅ Feature #{fid}: {f['title']}")

    return epic_id


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Cria Work Items no Azure Boards. "
            "Suporta hierarquia Scrum (Epic -> Feature -> PBI -> Task) "
            "e criação independente de qualquer tipo."
        )
    )
    parser.add_argument("plan", nargs="?", help="Caminho do plan.json (modo árvore ou items)")
    parser.add_argument("--org", default=os.getenv("AZDO_ORG"), help="Org (ex: minha-org)")
    parser.add_argument("--project", default=os.getenv("AZDO_PROJECT"), help="Project (ex: JCLOUD)")
    parser.add_argument("--pat", default=os.getenv("AZDO_PAT") or os.getenv("AZDO_AT"), help="PAT")
    parser.add_argument("--validate-only", action="store_true", help="Valida sem criar (validateOnly=true)")
    parser.add_argument("--list-types", action="store_true", help="Lista os WITs disponíveis no projeto e encerra")

    # Modo criação independente de 1 item via CLI
    parser.add_argument("--type", dest="single_type", help="Tipo do item (Epic, Feature, PBI, Task, etc.)")
    parser.add_argument("--title", dest="single_title", help="Título do item no modo --type")
    parser.add_argument("--description", dest="single_description", help="Descrição do item no modo --type")
    parser.add_argument(
        "--acceptance-criteria",
        dest="single_acceptance_criteria",
        help="Critérios de aceite no modo --type (quebra de linha para múltiplos critérios).",
    )
    parser.add_argument("--area-path", dest="single_area_path", help="System.AreaPath no modo --type")
    parser.add_argument("--iteration-path", dest="single_iteration_path", help="System.IterationPath no modo --type")
    parser.add_argument("--tags", dest="single_tags", help="Tags no modo --type")
    parser.add_argument("--parent-id", dest="single_parent_id", type=int, help="ID do pai no modo --type")

    args = parser.parse_args()

    if not args.org or not args.project or not args.pat:
        print("Faltam AZDO_ORG / AZDO_PROJECT / AZDO_PAT (ou AZDO_AT).", file=sys.stderr)
        return 2

    try:
        project_wits = set(list_project_work_item_types(args.org, args.project, args.pat))
        acceptance_field_cache: Dict[str, bool] = {}

        if args.list_types:
            print("Tipos disponíveis no projeto:")
            for wit in sorted(project_wits):
                print(f"- {wit}")
            return 0

        # Modo de criação independente de um único item via CLI
        if args.single_type:
            if not args.single_title:
                print("Quando usar --type, o --title é obrigatório.", file=sys.stderr)
                return 2

            required_wit = normalize_wit_name(args.single_type)
            if not required_wit:
                print("Campo inválido: --type não pode ser vazio.", file=sys.stderr)
                return 2
            validate_required_wits({required_wit}, project_wits)

            defaults = {
                "area_path": args.single_area_path,
                "iteration_path": args.single_iteration_path,
                "tags": args.single_tags,
            }
            item = {
                "type": args.single_type,
                "title": args.single_title,
                "description": args.single_description,
                "acceptance_criteria": args.single_acceptance_criteria,
                "parent_id": args.single_parent_id,
                "area_path": args.single_area_path,
                "iteration_path": args.single_iteration_path,
                "tags": args.single_tags,
            }
            created = create_independent_item(
                args.org,
                args.project,
                args.pat,
                defaults,
                item,
                acceptance_field_cache=acceptance_field_cache,
                validate_only=args.validate_only,
            )
            print_created_item(args.org, args.project, created)
            return 0

        if not args.plan:
            print("Informe plan.json ou use --type/--title para criação independente.", file=sys.stderr)
            return 2

        with open(args.plan, "r", encoding="utf-8") as f:
            data = json.load(f)

        defaults = data.get("defaults", {}) or {}

        # Modo novo: lista de itens independentes
        if "items" in data:
            items = data.get("items") or []
            if not isinstance(items, list):
                print("Campo inválido: 'items' deve ser uma lista.", file=sys.stderr)
                return 2

            required = required_wits_from_items(items)
            validate_required_wits(required, project_wits)

            if not items:
                print("Nenhum item informado em 'items'.")
                return 0

            for idx, item in enumerate(items, start=1):
                created = create_independent_item(
                    args.org,
                    args.project,
                    args.pat,
                    defaults,
                    item,
                    acceptance_field_cache=acceptance_field_cache,
                    validate_only=args.validate_only,
                )
                print_created_item(args.org, args.project, created, index=idx)
                print()
            return 0

        # Modo legado: árvore Epic -> Feature -> PBI -> Task
        required = required_wits_from_tree(data)
        validate_required_wits(required, project_wits)

        epics = data.get("epics", []) or []
        if not epics:
            print("Nenhum epic informado em 'epics'.")
            return 0

        for epic in epics:
            eid = create_epic(
                args.org,
                args.project,
                args.pat,
                defaults,
                epic,
                acceptance_field_cache=acceptance_field_cache,
                validate_only=args.validate_only,
            )
            print(f"🎯 Epic #{eid}: {epic['title']}")
            print(f"   UI: https://dev.azure.com/{args.org}/{args.project}/_workitems/edit/{eid}/")
            print()
    except (RuntimeError, ValueError, KeyError, OSError, json.JSONDecodeError) as ex:
        print(str(ex), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
