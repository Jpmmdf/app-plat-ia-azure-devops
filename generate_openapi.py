#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
from pathlib import Path

from fastapi.openapi.utils import get_openapi

from server import app

DEFAULT_SERVER_URL = "https://ops-plat-azure-devops-gateway.pedro-milhome.workers.dev"


def build_openapi_schema(openapi_version: str, server_url: str | None, server_description: str) -> dict:
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=openapi_version,
        description=app.description,
        routes=app.routes,
    )
    if server_url:
        schema["servers"] = [{"url": server_url, "description": server_description}]
    return schema


def write_json(schema: dict, output_path: Path) -> None:
    output_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


def write_yaml(schema: dict, output_path: Path) -> None:
    try:
        import yaml
    except ModuleNotFoundError as ex:
        raise RuntimeError(
            "PyYAML nao encontrado. Instale com: ./.venv/bin/pip install pyyaml"
        ) from ex

    output_path.write_text(
        yaml.safe_dump(schema, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def infer_format_from_output(output_path: Path) -> str:
    ext = output_path.suffix.lower()
    if ext in {".yaml", ".yml"}:
        return "yaml"
    return "json"


def main() -> int:
    default_openapi_version = app.openapi_version
    default_server_url = os.getenv("OPENAPI_SERVER_URL", DEFAULT_SERVER_URL)
    parser = argparse.ArgumentParser(
        description="Gera o OpenAPI a partir do app FastAPI em server.py."
    )
    parser.add_argument(
        "--output",
        default="openapi.yaml",
        help="Caminho do arquivo de saida (default: openapi.yaml).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default=None,
        help="Formato de saida. Se omitido, infere pela extensao de --output.",
    )
    parser.add_argument(
        "--openapi-version",
        default=default_openapi_version,
        help=f"Versao do OpenAPI a ser gerada (default: {default_openapi_version}).",
    )
    parser.add_argument(
        "--server-url",
        default=default_server_url,
        help=f"Base URL a ser registrada em servers.url (default: {default_server_url}).",
    )
    parser.add_argument(
        "--server-description",
        default="Cloudflare Worker (production)",
        help="Descricao para o server no OpenAPI.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_format = args.format or infer_format_from_output(output_path)
    schema = build_openapi_schema(args.openapi_version, args.server_url, args.server_description)

    if output_format == "yaml":
        write_yaml(schema, output_path)
    else:
        write_json(schema, output_path)

    print(f"OpenAPI ({args.openapi_version}) gerado em: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
