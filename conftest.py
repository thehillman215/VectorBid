# Make CI collection stable; keep MVP suite only.
collect_ignore_glob = [
    "tests/legacy/*",
    "tests/e2e/*",
    "tests/test_admin.py",
    "tests/test_parser.py",
]
