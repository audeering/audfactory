import copy
import os
import uuid

import pytest

import audeer
import audfactory


SERVER = pytest.SERVER
REPOSITORY = pytest.REPOSITORY
GROUP_ID = pytest.GROUP_ID
GROUP_ID_URL = audfactory.group_id_to_path(GROUP_ID)
NAME = pytest.NAME
VERSION = pytest.VERSION
FILENAME = f'{NAME}-{VERSION}'
CONTENT = 'hello-artifact'


@pytest.fixture(
    scope='module',
    autouse=True,
)
def fixture_publish_artifact():
    url = audfactory.url(
        SERVER,
        repository=REPOSITORY,
        group_id=GROUP_ID,
        name=NAME,
        version=VERSION,
    )
    path = audfactory.path(url)
    if path.exists():
        path.unlink()
    # create local file
    with open(f'{FILENAME}.txt', 'w') as fp:
        fp.write(CONTENT)
    audeer.create_archive('.', f'{FILENAME}.txt', f'{FILENAME}.zip')
    # upload artifact
    url = f'{url}/{FILENAME}.zip'
    audfactory.deploy(f'{FILENAME}.zip', url)
    # clean up
    os.remove(f'{FILENAME}.txt')
    os.remove(f'{FILENAME}.zip')


@pytest.mark.parametrize(
    'url,expected_urls',
    [
        (
            f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}',
            [
                f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}/{NAME}'
            ],
        ),
        (
            f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}/{NAME}/{VERSION}',
            [
                (
                    f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}/{NAME}/{VERSION}/'
                    f'{FILENAME}.zip'
                )
            ],
        ),
    ],
)
def test_path(url, expected_urls):
    path = audfactory.path(url)
    urls = [str(u) for u in path]
    assert expected_urls == urls


def test_checksum(tmpdir):

    with pytest.raises(RuntimeError, match=r'File not found:'):
        audfactory.checksum('file-not-found.txt')
    with pytest.raises(RuntimeError, match=r'File not found:'):
        url = f'{SERVER}/{REPOSITORY}/file-not-found.txt'
        audfactory.checksum(url)

    url = (
        f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}/'
        f'{NAME}/{VERSION}/{FILENAME}.zip'
    )
    cache = str(tmpdir.mkdir('audfactory'))
    destination = audeer.safe_path(cache)
    path = audfactory.download(url, destination)

    assert audfactory.checksum(url, type='md5') == \
        audfactory.checksum(path, type='md5')
    assert audfactory.checksum(url, type='sha1') == \
        audfactory.checksum(path, type='sha1')
    assert audfactory.checksum(url, type='sha256') == \
        audfactory.checksum(path, type='sha256')


@pytest.mark.parametrize(
    'filename,content,expected_versions',
    [
        (
            'audfactory.txt',
            'hello\nartifact',
            ['1.0.0'],
        ),
        # filename different from pytest.NAME
        (
            'foo.txt',
            'hello\nartifact',
            ['1.0.0'],
        ),
        # 'file-not-found.txt' will not create a local file
        pytest.param(
            'file-not-found.txt',
            'hello\nartifact',
            [],
            marks=pytest.mark.xfail(raises=FileNotFoundError),
        ),
    ]
)
def test_deploy(filename, content, expected_versions):
    # Use random name to ensure parallel running
    # Remove existing path to trigger new creation
    url = audfactory.url(
        SERVER,
        group_id=GROUP_ID,
        repository=REPOSITORY,
        name=NAME,
        version=VERSION,
    )
    # Add version to filename
    name, ext = os.path.splitext(os.path.basename(filename))
    url = f'{url}/{name}-{VERSION}{ext}'
    # create local file
    if filename != 'file-not-found.txt':
        with open(filename, 'w') as fp:
            fp.write(content)
    # upload artifact
    returned_url = audfactory.deploy(filename, url)
    # clean up
    os.remove(filename)
    # check url
    assert url == returned_url
    assert audfactory.path(url).exists()

    # download artifact
    path = audfactory.download(url, filename)
    # check content
    with open(path, 'r') as fp:
        lines = [line.strip() for line in fp.readlines()]
        assert content == '\n'.join(lines)
    # clean up
    os.remove(path)
    # check version
    versions = audfactory.versions(
        SERVER,
        REPOSITORY,
        GROUP_ID,
        NAME,
    )
    assert expected_versions == versions


@pytest.mark.parametrize(
    'url,destination,force_download,expected_path',
    [
        (
            '',
            '.',
            False,
            '',
        ),
        (
            (
                f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}/'
                f'{NAME}/{VERSION}/{FILENAME}.zip'
            ),
            '.',
            False,
            f'{FILENAME}.zip',
        ),
        (
            (
                f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}/'
                f'{NAME}/{VERSION}/{FILENAME}.zip'
            ),
            '.',
            True,
            f'{FILENAME}.zip',
        ),
        (
            (
                f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}/'
                f'{NAME}/{VERSION}/{FILENAME}.zip'
            ),
            'test2.zip',
            False,
            'test2.zip',
        ),
        # Access non-existng local folder
        pytest.param(
            (
                f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}/'
                f'{NAME}/{VERSION}/{FILENAME}.zip'
            ),
            'test-folder/test.zip',
            False,
            'test.zip',
            marks=pytest.mark.xfail(raises=FileNotFoundError),
        ),
        # 404, access non-existing SERVER
        pytest.param(
            (
                f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}/'
                f'{NAME}/{VERSION}/non-existing.txt'
            ),
            'non-existing.txt',
            False,
            'non-existing.txt',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ],
)
def test_download(
        tmpdir,
        url,
        destination,
        force_download,
        expected_path,
):
    cache = str(tmpdir.mkdir('audfactory'))
    destination = audeer.safe_path(
        os.path.join(cache, destination)
    )
    path = audfactory.download(
        url,
        destination,
        chunk=4 * 1024,
        force_download=force_download,
        verbose=False,
    )
    assert os.path.exists(path)
    assert os.path.basename(path) == expected_path


@pytest.mark.parametrize(
    'group_id,expected_path',
    [
        (
            'com.audeering.data.raw',
            'com/audeering/data/raw',
        ),
        (
            'de.bilderbar.emodb',
            'de/bilderbar/emodb',
        ),
    ],
)
def test_group_id_to_path(group_id, expected_path):
    path = audfactory.group_id_to_path(group_id)
    assert path == expected_path


@pytest.mark.parametrize(
    'path,expected_group_id',
    [
        (
            'com/audeering/data/raw',
            'com.audeering.data.raw',
        ),
        (
            'de/bilderbar/emodb',
            'de.bilderbar.emodb',
        ),
    ],
)
def test_path_to_group_id(path, expected_group_id):
    group_id = audfactory.path_to_group_id(path)
    assert group_id == expected_group_id


@pytest.mark.parametrize(
    'url,expected_text',
    [
        (
            (
                f'{SERVER}/{REPOSITORY}/{GROUP_ID_URL}/{NAME}/{VERSION}/'
                f'{FILENAME}.zip!/{FILENAME}.txt'
            ),
            CONTENT,
        ),
    ],
)
def test_rest_api_get(url, expected_text):
    r = audfactory.rest_api_get(url)
    assert r.status_code == 200
    assert r.text == expected_text


@pytest.mark.parametrize(
    'group_id,name,repository,version,expected_url',
    [
        (
            'group_id',
            'name',
            None,
            '1.0.0',
            SERVER,
        ),
        (
            'group_id',
            'name',
            '',
            '1.0.0',
            SERVER,
        ),
        (
            None,
            None,
            'maven',
            None,
            f'{SERVER}/maven',
        ),
        (
            '',
            '',
            'maven',
            '',
            f'{SERVER}/maven',
        ),
        (
            'com.audeering.data',
            None,
            'maven',
            None,
            f'{SERVER}/maven/com/audeering/data',
        ),
        (
            'com.audeering.data',
            'database',
            'data-public',
            None,
            f'{SERVER}/data-public/com/audeering/data/database',
        ),
        (
            'com.audeering.data',
            'database',
            'maven',
            '1.1.0',
            (
                f'{SERVER}/maven/'
                f'com/audeering/data/database/1.1.0'
            ),
        ),
    ],
)
def test_url(group_id, name, version, repository, expected_url):
    url = audfactory.url(
        SERVER,
        group_id=group_id,
        name=name,
        repository=repository,
        version=version,
    )
    assert url == expected_url


@pytest.mark.parametrize(
    'group_id,name,expected_versions',
    [
        (
            GROUP_ID,
            NAME,
            [
                VERSION,
            ],
        ),
        (
            'non-existing-group-id',
            'non-existing-name',
            [],
        ),
    ]
)
def test_versions(group_id, name, expected_versions):
    versions = audfactory.versions(
        SERVER,
        REPOSITORY,
        group_id,
        name,
    )
    assert versions == expected_versions
