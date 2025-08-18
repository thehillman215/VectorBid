from pathlib import Path


def pytest_ignore_collect(collection_path, config):
    p = Path(str(path))
    s = str(p).replace("\\", "/")
    return any(
        seg in s
        for seg in (
            "tests/legacy/",
            "tests/e2e/",
            "tests/test_admin.py",
            "tests/test_parser.py",
        )
    )
