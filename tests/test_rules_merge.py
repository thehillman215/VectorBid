import textwrap

from app.rules.engine import load_rule_pack


def test_nested_far117_and_union_rules_merge(tmp_path):
    base_yaml = tmp_path / "base.yml"
    overlay_yaml = tmp_path / "overlay.yml"

    base_yaml.write_text(
        textwrap.dedent(
            """
            hard:
              FAR117:
                min_rest: 8
                duty_limit: 14
              union:
                max_trip: 3
                nested:
                  days_off: 2
            """
        )
    )

    overlay_yaml.write_text(
        textwrap.dedent(
            """
            hard:
              FAR117:
                min_rest: 10
              union:
                nested:
                  days_off: 4
            """
        )
    )

    merged = load_rule_pack([str(base_yaml), str(overlay_yaml)])

    assert merged["hard"]["FAR117"]["min_rest"] == 10
    assert merged["hard"]["FAR117"]["duty_limit"] == 14
    assert merged["hard"]["union"]["max_trip"] == 3
    assert merged["hard"]["union"]["nested"]["days_off"] == 4
