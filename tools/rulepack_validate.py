from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]
from jsonschema import Draft7Validator

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "app" / "rules" / "schema.json"


def load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open() as f:
        return cast(dict[str, Any], json.load(f))


def _collect_ids(obj: Any) -> list[str]:
    ids: list[str] = []
    if isinstance(obj, dict):
        maybe_id = obj.get("id")
        if isinstance(maybe_id, str):
            ids.append(maybe_id)
        for value in obj.values():
            ids.extend(_collect_ids(value))
    elif isinstance(obj, list):
        for item in obj:
            ids.extend(_collect_ids(item))
    return ids


def validate_data(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft7Validator(schema)
    errors = [e.message for e in validator.iter_errors(data)]
    ids = _collect_ids(data)
    duplicates = [i for i, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate ids: {', '.join(sorted(duplicates))}")
    return errors


def validate_file(path: Path, schema: dict[str, Any] | None = None) -> list[str]:
    if schema is None:
        schema = load_schema()
    with path.open() as f:
        data = yaml.safe_load(f)
    return validate_data(data, schema)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate rulepack YAML files")
    parser.add_argument("paths", nargs="+", help="Glob paths to rulepack files")
    args = parser.parse_args(argv)

    schema = load_schema()
    errors_found = False
    for pattern in args.paths:
        for filename in sorted(glob.glob(pattern)):
            path = Path(filename)
            errors = validate_file(path, schema)
            if errors:
                errors_found = True
                for err in errors:
                    print(f"{path}: {err}", file=sys.stderr)
    return 1 if errors_found else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
