from app.pbs.lint import lint_artifact


def test_lint_shadowing() -> None:
    artifact = {
        "layers": [
            {
                "n": 1,
                "filters": [{"type": "PairingId", "op": "IN", "values": ["A"]}],
                "prefer": "YES",
            },
            {
                "n": 2,
                "filters": [{"type": "PairingId", "op": "IN", "values": ["A"]}],
                "prefer": "YES",
            },
        ]
    }
    result = lint_artifact(artifact)
    msg = next(w for w in result["warnings"] if w["code"] == "LAYER_SHADOWING")
    assert msg["fix"] == "remove layer 2"


def test_mutually_exclusive_filters() -> None:
    artifact = {
        "layers": [
            {
                "n": 1,
                "filters": [
                    {"type": "PairingId", "op": "IN", "values": ["A"]},
                    {"type": "PairingId", "op": "IN", "values": ["B"]},
                ],
                "prefer": "YES",
            }
        ]
    }
    result = lint_artifact(artifact)
    assert any(e["code"] == "FILTERS_EXCLUSIVE" for e in result["errors"])


def test_unreachable_layer() -> None:
    artifact = {
        "layers": [
            {
                "n": 1,
                "filters": [
                    {"type": "PairingId", "op": "IN", "values": ["A", "B"]}
                ],
                "prefer": "YES",
            },
            {
                "n": 2,
                "filters": [
                    {"type": "PairingId", "op": "IN", "values": ["A"]}
                ],
                "prefer": "YES",
            },
        ]
    }
    result = lint_artifact(artifact)
    assert any(w["code"] == "LAYER_UNREACHABLE" for w in result["warnings"])

