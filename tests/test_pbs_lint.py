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
    assert any("layer 2" in w and "shadowed" in w for w in result["warnings"])


def test_lint_unreachable() -> None:
    artifact = {
        "layers": [
            {
                "n": 1,
                "filters": [{"type": "PairingId", "op": "IN", "values": []}],
                "prefer": "YES",
            },
            {
                "n": 2,
                "filters": [{"type": "PairingId", "op": "IN", "values": ["A", "A"]}],
                "prefer": "YES",
            },
        ]
    }
    result = lint_artifact(artifact)
    assert any("layer 1" in w and "no values" in w for w in result["warnings"])
    assert any("layer 2" in w and "redundant equals" in w for w in result["warnings"])
