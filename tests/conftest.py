import os
import pytest
import uuid

import audfactory


pytest.SERVER = 'https://audeering.jfrog.io/artifactory'
pytest.GROUP_ID = f'com.audeering.audfactory.{str(uuid.uuid1())}'
pytest.NAME = 'audfactory'
pytest.REPOSITORY = 'unittests-public'
pytest.VERSION = '1.0.0'


def cleanup():
    url = audfactory.url(
        pytest.SERVER,
        group_id=pytest.GROUP_ID,
        repository=pytest.REPOSITORY,
    )
    path = audfactory.path(url)
    if path.exists():
        path.rmdir()
    cleanup_files = [
        'db-1.1.0.yaml',
    ]
    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)


@pytest.fixture(scope='session', autouse=True)
def cleanup_session():
    cleanup()
    yield


@pytest.fixture(scope='module', autouse=True)
def cleanup_test():
    yield
    cleanup()
