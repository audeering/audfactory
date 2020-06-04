import pytest
import uuid

import audfactory


pytest.GROUP_ID = f'com.audeering.audfactory.{str(uuid.uuid1())}'
pytest.NAME = 'audfactory'
pytest.REPOSITORY = 'unittests-public-local'
pytest.VERSION = '1.0.0'


def cleanup():
    url = audfactory.server_url(
        pytest.GROUP_ID,
        repository=pytest.REPOSITORY,
    )
    path = audfactory.artifactory_path(url)
    if path.exists():
        path.rmdir()


@pytest.fixture(scope='session', autouse=True)
def cleanup_session():
    cleanup()
    yield


@pytest.fixture(scope='module', autouse=True)
def cleanup_test():
    yield
    cleanup()
