from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "openapi.yaml"
ALLOWED_ROOT_OPENAPI = {"openapi.yaml"}
BANNED_TERMS = ("OpenAI", "Custom GPT", "GPT Actions", "ChatGPT")
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "trace"}
SCHEMA_TYPES = {"string", "number", "integer", "object", "array", "boolean", "null"}


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: UniqueKeyLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate mapping key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping)


def _scan_refs(value: Any, refs: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "$ref" and isinstance(item, str):
                refs.add(item)
            else:
                _scan_refs(item, refs)
    elif isinstance(value, list):
        for item in value:
            _scan_refs(item, refs)


def _validate_schema_node(node: Any, path: str, errors: list[str]) -> None:
    if isinstance(node, bool):
        return
    if not isinstance(node, dict):
        errors.append(f"{path}: schema node must be a mapping or boolean")
        return

    schema_type = node.get("type")
    if isinstance(schema_type, str):
        if schema_type not in SCHEMA_TYPES:
            errors.append(f"{path}: invalid schema type {schema_type!r}")
    elif isinstance(schema_type, list):
        if not schema_type:
            errors.append(f"{path}: type list cannot be empty")
        for item in schema_type:
            if not isinstance(item, str) or item not in SCHEMA_TYPES:
                errors.append(f"{path}: invalid schema type entry {item!r}")
    elif schema_type is not None:
        errors.append(f"{path}: type must be a string or list of strings")

    required = node.get("required")
    if required is not None and (not isinstance(required, list) or any(not isinstance(item, str) for item in required)):
        errors.append(f"{path}: required must be a list of strings")

    enum = node.get("enum")
    if enum is not None:
        if not isinstance(enum, list):
            errors.append(f"{path}: enum must be a list")
        elif len(enum) != len(set(enum)):
            errors.append(f"{path}: enum values must be unique")

    additional_properties = node.get("additionalProperties")
    if additional_properties is not None and not isinstance(additional_properties, (bool, dict)):
        errors.append(f"{path}: additionalProperties must be a boolean or schema mapping")
    if isinstance(additional_properties, dict):
        _validate_schema_node(additional_properties, f"{path}.additionalProperties", errors)

    properties = node.get("properties")
    if properties is not None:
        if not isinstance(properties, dict):
            errors.append(f"{path}: properties must be a mapping")
        else:
            for prop_name, prop_schema in properties.items():
                _validate_schema_node(prop_schema, f"{path}.properties.{prop_name}", errors)

    items = node.get("items")
    if items is not None:
        if isinstance(items, dict):
            _validate_schema_node(items, f"{path}.items", errors)
        elif isinstance(items, list):
            for index, item in enumerate(items):
                _validate_schema_node(item, f"{path}.items[{index}]", errors)
        elif not isinstance(items, bool):
            errors.append(f"{path}: items must be a schema mapping, list, or boolean")

    for keyword in ("allOf", "anyOf", "oneOf", "prefixItems"):
        subschemas = node.get(keyword)
        if subschemas is None:
            continue
        if not isinstance(subschemas, list):
            errors.append(f"{path}: {keyword} must be a list")
            continue
        for index, item in enumerate(subschemas):
            _validate_schema_node(item, f"{path}.{keyword}[{index}]", errors)

    for keyword in ("not", "contains", "if", "then", "else"):
        subschema = node.get(keyword)
        if isinstance(subschema, dict) or isinstance(subschema, bool):
            _validate_schema_node(subschema, f"{path}.{keyword}", errors)
        elif subschema is not None:
            errors.append(f"{path}: {keyword} must be a schema mapping or boolean")


def _resolve_internal_ref(spec: dict[str, Any], ref: str) -> tuple[bool, str | None]:
    if not ref.startswith("#/"):
        return False, "external refs are not allowed in this contract"
    cursor: Any = spec
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(cursor, dict) and part in cursor:
            cursor = cursor[part]
        else:
            return False, f"unresolved ref target: {ref}"
    return True, None


def collect_openapi_report(root: Path = ROOT) -> dict[str, Any]:
    path = root / "openapi.yaml"
    report: dict[str, Any] = {
        "ok": False,
        "path": str(path),
        "location": "root" if path.exists() else "missing",
        "errors": [],
        "warnings": [],
        "vendor_term_counts": {},
    }
    if not path.exists():
        report["errors"].append("openapi.yaml is missing from repository root")
        return report

    raw = path.read_text(encoding="utf-8")
    try:
        spec = yaml.load(raw, Loader=UniqueKeyLoader)
    except Exception as exc:  # pragma: no cover - exercised by validation failure paths
        report["errors"].append(f"yaml parse failed: {type(exc).__name__}: {exc}")
        return report

    if not isinstance(spec, dict):
        report["errors"].append("top-level OpenAPI document must be a mapping")
        return report

    if path.name not in ALLOWED_ROOT_OPENAPI:
        report["errors"].append("openapi.yaml must remain the canonical root contract file")

    openapi_version = str(spec.get("openapi", ""))
    if not openapi_version.startswith("3.1"):
        report["errors"].append(f"expected OpenAPI 3.1.x, found {openapi_version!r}")

    info = spec.get("info") if isinstance(spec.get("info"), dict) else {}
    paths = spec.get("paths") if isinstance(spec.get("paths"), dict) else {}
    components = spec.get("components") if isinstance(spec.get("components"), dict) else {}
    schemas = components.get("schemas") if isinstance(components.get("schemas"), dict) else {}

    vendor_counts = {term: len(re.findall(re.escape(term), raw)) for term in BANNED_TERMS}
    vendor_hits = {term: count for term, count in vendor_counts.items() if count}
    if vendor_hits:
        report["errors"].append(
            "vendor-specific terminology remains in openapi.yaml: "
            + ", ".join(f"{term}={count}" for term, count in sorted(vendor_hits.items()))
        )
    report["vendor_term_counts"] = vendor_counts

    operation_ids: list[str] = []
    invalid_operations: list[str] = []
    for path_key, path_item in paths.items():
        if not isinstance(path_item, dict):
            invalid_operations.append(f"{path_key}: path item must be a mapping")
            continue
        for method, operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                invalid_operations.append(f"{path_key} {method}: operation must be a mapping")
                continue
            operation_id = operation.get("operationId")
            if isinstance(operation_id, str):
                operation_ids.append(operation_id)
            else:
                invalid_operations.append(f"{path_key} {method}: missing operationId")

    duplicate_operation_ids = sorted(name for name, count in Counter(operation_ids).items() if count > 1)
    if duplicate_operation_ids:
        report["errors"].append("duplicate operationId values: " + ", ".join(duplicate_operation_ids))
    if invalid_operations:
        report["errors"].extend(invalid_operations)

    schema_errors: list[str] = []
    for schema_name, schema in schemas.items():
        _validate_schema_node(schema, f"components.schemas.{schema_name}", schema_errors)
    if schema_errors:
        report["errors"].extend(schema_errors)

    refs: set[str] = set()
    _scan_refs(spec, refs)
    unresolved_refs: list[str] = []
    for ref in sorted(refs):
        ok, message = _resolve_internal_ref(spec, ref)
        if not ok:
            unresolved_refs.append(message or ref)
    if unresolved_refs:
        report["errors"].extend(unresolved_refs)

    report.update(
        {
            "openapi_version": openapi_version,
            "info_version": info.get("version"),
            "title": info.get("title"),
            "description": info.get("description"),
            "path_count": len(paths),
            "operation_count": len(operation_ids),
            "schema_count": len(schemas),
            "duplicate_operation_ids": duplicate_operation_ids,
            "unresolved_refs": unresolved_refs,
            "operation_ids": operation_ids,
        }
    )
    report["ok"] = not report["errors"]
    return report


def _render_text(report: dict[str, Any]) -> str:
    lines = [
        f"openapi_contract: {'ok' if report.get('ok') else 'fail'}",
        f"path: {report.get('path')}",
        f"location: {report.get('location')}",
        f"openapi_version: {report.get('openapi_version')}",
        f"info_version: {report.get('info_version')}",
        f"title: {report.get('title')}",
        f"paths: {report.get('path_count')}",
        f"operations: {report.get('operation_count')}",
        f"schemas: {report.get('schema_count')}",
        "vendor_term_counts:",
    ]
    for term, count in report.get("vendor_term_counts", {}).items():
        lines.append(f"  {term}: {count}")
    if report.get("duplicate_operation_ids"):
        lines.append("duplicate_operation_ids:")
        for name in report["duplicate_operation_ids"]:
            lines.append(f"  - {name}")
    if report.get("unresolved_refs"):
        lines.append("unresolved_refs:")
        for item in report["unresolved_refs"]:
            lines.append(f"  - {item}")
    if report.get("errors"):
        lines.append("errors:")
        for item in report["errors"]:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the checked-in OpenAPI contract.")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    report = collect_openapi_report(ROOT)
    if args.output == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_text(report))
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
