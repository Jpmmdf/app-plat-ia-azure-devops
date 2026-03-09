#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cria um Epic (Work Item) no Azure DevOps.

Requisitos:
  pip install requests

Autenticação:
  Use um PAT (Personal Access Token) com permissão para criar Work Items
  (escopo equivalente a vso.work_write / Work Items Read & write). :contentReference[oaicite:1]{index=1}
"""

import argparse
import os
import sys
from typing import List, Dict, Any, Optional, Union
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth

ACCEPTANCE_CRITERIA_FIELD = "Microsoft.VSTS.Common.AcceptanceCriteria"
MARKDOWN_FORMAT_VALUE = "Markdown"


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
    wi_type: str,
    field_reference_name: str,
) -> bool:
    encoded_type = quote(wi_type, safe="")
    url = (
        f"https://dev.azure.com/{org}/{project}"
        f"/_apis/wit/workitemtypes/{encoded_type}/fields"
        f"?api-version=7.1"
    )
    resp = requests.get(url, auth=HTTPBasicAuth("", pat), headers={"Accept": "application/json"}, timeout=30)
    if resp.status_code >= 400:
        return False

    try:
        payload = resp.json()
    except Exception:
        return False

    return any(
        isinstance(field, dict) and field.get("referenceName") == field_reference_name
        for field in payload.get("value", [])
    )


def build_patch_ops(
    title: str,
    description: Optional[str] = None,
    acceptance_criteria: Optional[Union[str, List[str]]] = None,
    acceptance_field_supported: bool = False,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
    assigned_to: Optional[str] = None,
    tags: Optional[str] = None,
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

    if assigned_to:
        ops.append({"op": "add", "path": "/fields/System.AssignedTo", "value": assigned_to})

    if tags:
        # Azure DevOps usa tags como string separada por ; (ponto e vírgula)
        normalized = "; ".join([t.strip() for t in tags.replace(",", ";").split(";") if t.strip()])
        ops.append({"op": "add", "path": "/fields/System.Tags", "value": normalized})

    return ops


def create_work_item(
    org: str,
    project: str,
    pat: str,
    wi_type: str,
    patch_ops: List[Dict[str, Any]],
    bypass_rules: bool = False,
    suppress_notifications: bool = False,
) -> Dict[str, Any]:
    # type na URL é no formato $Epic, $Task, etc. :contentReference[oaicite:2]{index=2}
    type_part = wi_type if wi_type.startswith("$") else f"${wi_type}"

    url = (
        f"https://dev.azure.com/{org}/{project}"
        f"/_apis/wit/workitems/{type_part}"
        f"?api-version=7.1"
        f"&bypassRules={'true' if bypass_rules else 'false'}"
        f"&suppressNotifications={'true' if suppress_notifications else 'false'}"
    )

    headers = {
        "Content-Type": "application/json-patch+json",
        "Accept": "application/json",
    }

    # Basic Auth: username pode ser vazio, PAT como senha
    resp = requests.post(
        url,
        headers=headers,
        json=patch_ops,
        auth=HTTPBasicAuth("", pat),
        timeout=30,
    )

    if resp.status_code >= 400:
        try:
            details = resp.json()
        except Exception:
            details = resp.text
        raise RuntimeError(f"Erro ao criar Work Item ({resp.status_code}): {details}")

    if not resp.text:
        return {}

    content_type = (resp.headers.get("content-type") or "").lower()
    if "application/json" not in content_type:
        snippet = resp.text[:400].strip().replace("\n", " ")
        raise RuntimeError(
            f"Erro ao criar Work Item ({resp.status_code}): resposta nao JSON do Azure DevOps: {snippet}"
        )

    try:
        return resp.json()
    except ValueError as ex:
        snippet = resp.text[:400].strip().replace("\n", " ")
        raise RuntimeError(
            f"Erro ao criar Work Item ({resp.status_code}): JSON invalido do Azure DevOps: {snippet}"
        ) from ex


def main() -> int:
    parser = argparse.ArgumentParser(description="Cria um Epic no Azure DevOps (Azure Boards).")
    parser.add_argument("--org", default=os.getenv("AZDO_ORG"), help="Organização (ex: minha-org)")
    parser.add_argument("--project", default=os.getenv("AZDO_PROJECT"), help="Projeto (nome ou ID)")
    parser.add_argument(
        "--pat",
        default=os.getenv("AZDO_PAT") or os.getenv("AZDO_AT"),
        help="Personal Access Token (PAT)",
    )

    parser.add_argument("--type", default="Epic", help="Tipo do Work Item (default: Epic)")
    parser.add_argument("--title", required=True, help="Título do Epic")

    parser.add_argument("--description", help="Descrição (HTML/Markdown, conforme processo)")
    parser.add_argument(
        "--acceptance-criteria",
        help="Critérios de aceite (quebra de linha para múltiplos critérios).",
    )
    parser.add_argument("--area-path", help="System.AreaPath (ex: MeuProjeto\\Time A)")
    parser.add_argument("--iteration-path", help="System.IterationPath (ex: MeuProjeto\\Sprint 1)")
    parser.add_argument("--assigned-to", help="E-mail ou nome do usuário (System.AssignedTo)")
    parser.add_argument("--tags", help="Tags separadas por vírgula ou ponto e vírgula")

    parser.add_argument("--bypass-rules", action="store_true", help="Ignorar regras do tipo (cuidado)")
    parser.add_argument("--suppress-notifications", action="store_true", help="Suprimir notificações")

    args = parser.parse_args()

    if not args.org or not args.project or not args.pat:
        print(
            "Faltam credenciais/parâmetros. Use flags --org/--project/--pat "
            "ou defina as envs AZDO_ORG, AZDO_PROJECT, AZDO_PAT (ou AZDO_AT).",
            file=sys.stderr,
        )
        return 2

    acceptance_supported = work_item_type_supports_field(
        org=args.org,
        project=args.project,
        pat=args.pat,
        wi_type=args.type,
        field_reference_name=ACCEPTANCE_CRITERIA_FIELD,
    )

    patch_ops = build_patch_ops(
        title=args.title,
        description=args.description,
        acceptance_criteria=args.acceptance_criteria,
        acceptance_field_supported=acceptance_supported,
        area_path=args.area_path,
        iteration_path=args.iteration_path,
        assigned_to=args.assigned_to,
        tags=args.tags,
    )

    try:
        wi = create_work_item(
            org=args.org,
            project=args.project,
            pat=args.pat,
            wi_type=args.type,
            patch_ops=patch_ops,
            bypass_rules=args.bypass_rules,
            suppress_notifications=args.suppress_notifications,
        )
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1

    wi_id = wi.get("id")
    wi_url = wi.get("url")
    title = (wi.get("fields") or {}).get("System.Title")

    print("✅ Epic criado com sucesso!")
    print(f"ID: {wi_id}")
    print(f"Título: {title}")
    print(f"URL API: {wi_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
