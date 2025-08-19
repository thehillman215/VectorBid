from pathlib import Path

from tools.rulepack_validate import load_schema, validate_file

FIXTURES = Path(__file__).parent / "fixtures" / "rulepacks"
SCHEMA = load_schema()


def path(name: str) -> Path:
    return FIXTURES / name


def test_valid_rulepack() -> None:
    assert not validate_file(path("valid.yml"), SCHEMA)


def test_unknown_field() -> None:
    errors = validate_file(path("unknown_field.yml"), SCHEMA)
    assert any("additional properties" in e.lower() for e in errors)


def test_duplicate_ids() -> None:
    errors = validate_file(path("duplicate_id.yml"), SCHEMA)
    assert any("duplicate" in e for e in errors)


def test_missing_version() -> None:
    errors = validate_file(path("missing_version.yml"), SCHEMA)
    assert any("version" in e for e in errors)
