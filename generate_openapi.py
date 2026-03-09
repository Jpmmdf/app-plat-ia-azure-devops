#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path

from fastapi.openapi.utils import get_openapi

from server import app


def build_openapi_schema(openapi_version: str) -> dict:
    return get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=openapi_version,
        description=app.description,
        routes=app.routes,
    )


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
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_format = args.format or infer_format_from_output(output_path)
    schema = build_openapi_schema(args.openapi_version)

    if output_format == "yaml":
        write_yaml(schema, output_path)
    else:
        write_json(schema, output_path)

    print(f"OpenAPI ({args.openapi_version}) gerado em: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
