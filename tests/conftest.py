import os
import uuid

import pytest

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


@pytest.fixture(scope='function', autouse=False)
def no_artifactory_access_rights():
    current_username = os.environ.get('ARTIFACTORY_USERNAME', False)
    current_api_key = os.environ.get('ARTIFACTORY_API_KEY', False)
    os.environ['ARTIFACTORY_USERNAME'] = 'non-existing-user'
    os.environ['ARTIFACTORY_API_KEY'] = 'non-existing-password'
    yield
    if current_username:
        os.environ["ARTIFACTORY_USERNAME"] = current_username
    else:
        del os.environ['ARTIFACTORY_USERNAME']
    if current_api_key:
        os.environ['ARTIFACTORY_API_KEY'] = current_api_key
    else:
        del os.environ['ARTIFACTORY_API_KEY']
