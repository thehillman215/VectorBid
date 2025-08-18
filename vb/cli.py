from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.rules.models import RulePack


def _cmd_validate(args: argparse.Namespace) -> int:
    """Validate a rule pack file."""
    try:
        data = yaml.safe_load(Path(args.path).read_text()) or {}
        RulePack.model_validate(data)
        print("OK")
        return 0
    except (OSError, ValidationError) as e:  # pragma: no cover - CLI errors
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def _cmd_list(args: argparse.Namespace) -> int:
    base = Path("rule_packs")
    target = base / args.airline if args.airline else base
    for path in sorted(target.glob("**/*.yml")):
        print(path.as_posix())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vb")
    sub = parser.add_subparsers(dest="command")

    rules = sub.add_parser("rules")
    rules_sub = rules.add_subparsers(dest="rules_cmd")

    p_validate = rules_sub.add_parser("validate")
    p_validate.add_argument("path")
    p_validate.set_defaults(func=_cmd_validate)

    p_list = rules_sub.add_parser("list")
    p_list.add_argument("--airline")
    p_list.set_defaults(func=_cmd_list)

    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        return int(args.func(args))
    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
