def pytest_ignore_collect(collection_path, config):
    # Do not ignore anything; rely on pytest.ini
    return False
