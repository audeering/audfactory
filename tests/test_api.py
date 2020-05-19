import copy
import os
import uuid

import pytest

import audeer
import audfactory

from example_poms import (
    emodb_pom,
    empty_pom,
    example_pom,
    pom_with_empty_deps,
)


def artifactory(path, repo='maven'):
    """Add artifactory URL in front of repo and path."""
    return f'https://artifactory.audeering.com/artifactory/{repo}/{path}'


@pytest.mark.parametrize(
    'url,expected_urls',
    [
        (
            'com/audeering/data/emodb/emodb-data/0.2.2/',
            [('com/audeering/data/emodb/emodb-data/0.2.2/'
              'emodb-data-0.2.2.pom')],
        ),

    ],
)
def test_artifactory_path(url, expected_urls):
    url = artifactory(url)
    expected_urls = [artifactory(u) for u in expected_urls]
    path = audfactory.artifactory_path(url)
    urls = [str(u) for u in path]
    assert expected_urls == urls


@pytest.mark.parametrize(
    'pom,expected_deps',
    [
        (
            example_pom,
            ['com.audeering.data.database:database-data:1.0.1',
             'com.audeering.data.database:database-metadata:2.1.0'],
        ),
        (
            empty_pom,
            [],
        ),
        (
            pom_with_empty_deps,
            [],
        ),
    ],
)
def test_dependencies(pom, expected_deps):
    deps = audfactory.dependencies(pom)
    assert len(deps) == len(expected_deps)
    assert deps == expected_deps


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
            ('com/audeering/data/emodb/emodb-metadata/0.2.2/'
             'emodb-metadata-0.2.2.zip'),
            '.',
            False,
            'emodb-metadata-0.2.2.zip',
        ),
        (
            ('com/audeering/data/emodb/emodb-metadata/0.2.2/'
             'emodb-metadata-0.2.2.zip'),
            '.',
            True,
            'emodb-metadata-0.2.2.zip',
        ),
        (
            ('com/audeering/data/emodb/emodb-metadata/0.2.2/'
             'emodb-metadata-0.2.2.zip'),
            'emodb.zip',
            False,
            'emodb.zip',
        ),
        # Access non-existng local folder
        pytest.param(
            ('com/audeering/data/emodb/emodb-metadata/0.2.2/'
             'emodb-metadata-0.2.2.zip'),
            'emodb-folder/emodb.zip',
            False,
            'emodb.zip',
            marks=pytest.mark.xfail(raises=FileNotFoundError),
        ),
        # 404, access non-existing URL
        pytest.param(
            ('com/audeering/data/emodb/emodb-metadata/0.0.2/'
             'emodb-metadata-0.0.2.zip'),
            'emodb-metadata-0.0.2.zip',
            False,
            'emodb-metadata-0.0.2.zip',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        # 403, no access rights for URL
        pytest.param(
            ('com/audeering/data/hipercom/hipercom-metadata/2.0.1/'
             'hipercom-metadata-2.0.1.zip'),
            'hipercom.zip',
            False,
            'hipercom.zip',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),

    ],
)
def test_download_artifact(
        tmpdir,
        url,
        destination,
        force_download,
        expected_path,
):
    url = artifactory(url)
    cache = str(tmpdir.mkdir('audfactory'))
    path = audfactory.download_artifact(
        url,
        os.path.join(cache, audeer.safe_path(destination)),
        chunk=4 * 1024,
        force_download=force_download,
        verbose=False,
    )
    assert os.path.exists(path)
    assert os.path.basename(path) == expected_path


@pytest.mark.parametrize(
    'pom_url,expected_description,expected_license,expected_packaging',
    [
        (
            'com/audeering/data/testdata/testdata/1.2.1/testdata-1.2.1.pom',
            'Test data set with 100 WAV files.',
            'CC0 1.0',
            'pom',
        ),
        # 404 error, path not found
        pytest.param(
            'edu/upenn/ldc/timit/0.0.3/timit-0.0.3.pom',
            '',
            '',
            '',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        # 403 error, no access rights
        pytest.param(
            'com/audeering/data/hipercom/hipercom/2.0.1/hipercom-2.0.1.pom',
            'Call center conversations in Swiss German',
            'Proprietary',
            'pom',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        # No valid POM
        pytest.param(
            'edu/upenn/ldc/timit/1.0.1/',
            '',
            '',
            '',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ],
)
def test_download_pom(
        pom_url,
        expected_description,
        expected_license,
        expected_packaging,
):
    pom_url = artifactory(pom_url)
    pom = audfactory.download_pom(pom_url)
    description = pom['project']['description']
    license = pom['project']['licenses']['license']['name']
    packaging = pom['project']['packaging']
    assert description == expected_description
    assert license == expected_license
    assert packaging == expected_packaging


@pytest.mark.parametrize(
    'deps,pattern,expected_deps',
    [
        (
            {},
            '',
            {},
        ),
        (
            {'a': 0},
            'a',
            {},
        ),
        (
            {'a': 0, 'b': 0},
            'c',
            {'a': 0, 'b': 0},
        ),
        (
            {'a': 0, 'b': 0},
            'a',
            {'b': 0},
        ),
        (
            {'a': {'b': 1, 'c': 1}},
            'a',
            {},
        ),
        (
            {'a': {'b': 1, 'c': 1}},
            'd',
            {'a': {'b': 1, 'c': 1}},
        ),
        (
            {'a': {'b': 1, 'c': 1}},
            'c',
            {'a': {'b': 1}},
        ),
        (
            {'a': {'a1': 1, 'a2': {'b1': 2, 'b2': 2, 'b3': 2}}},
            r'b[1-2]',
            {'a': {'a1': 1, 'a2': {'b3': 2}}},
        ),
    ],
)
def test_exclude_dependencies(deps, pattern, expected_deps):
    deps = audfactory.exclude_dependencies(deps, pattern)
    assert deps == expected_deps


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
    'deps,pattern,expected_deps',
    [
        (
            {},
            '',
            {},
        ),
        (
            {'a': 0},
            'b',
            {},
        ),
        (
            {'a': 0, 'b': 0},
            'c',
            {},
        ),
        (
            {'a': 0, 'b': 0},
            'b',
            {'b': 0},
        ),
        (
            {'a': {'b': 1, 'c': 1}},
            'd',
            {},
        ),
        (
            {'a': {'b': 1, 'c': 1}},
            'a',
            {'a': {'b': 1, 'c': 1}},
        ),
        (
            {'a': {'b': 1, 'c': 1}},
            'b',
            {'a': {'b': 1}},
        ),
        (
            {'a': {'a1': 1, 'a2': {'b1': 2, 'b2': 2, 'b3': 2}}},
            r'b[1-2]',
            {'a': {'a2': {'b1': 2, 'b2': 2}}},
        ),
    ],
)
def test_include_dependencies(deps, pattern, expected_deps):
    deps = audfactory.include_dependencies(deps, pattern)
    assert deps == expected_deps


@pytest.mark.parametrize(
    'deps,expected_dep_list',
    [
        (
            {},
            [],
        ),
        (
            {
                'com.audeering.data.emodb:emodb-data:0.2.2':
                    {
                        'info.bilderbar.emodb:emodb:1.0.0': 'zip',
                        'com.audeering.data.emodb:emodb-metadata:0.2.2': 'zip',
                    },
            },
            [('com/audeering/data/emodb/emodb-metadata/0.2.2/'
              'emodb-metadata-0.2.2.zip'),
             'info/bilderbar/emodb/emodb/1.0.0/emodb-1.0.0.zip']
        ),
    ],
)
def test_list_artifacts(deps, expected_dep_list):
    dep_list = audfactory.list_artifacts(deps)
    expected_dep_list = [artifactory(d) for d in expected_dep_list]
    assert dep_list == expected_dep_list


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
                'maven/info/bilderbar/emodb/emodb/1.0.0/'
                'emodb-1.0.0.zip!/erklaerung.txt'
            ),
            (
                'In der Datei info.txt und info.xls sind jeweils die '
                'Dateinamen sowie die Erkennungsrate in Prozent und die '
                'Beurteilung der Natuerlichkeit in Prozent angegeben. '
                'Am Perzeptionstest haben 20 Versuchspersonen teilgenommen. '
                '\r\nDie Auswahl der Saetze erfolgt bei mind. 80% richtig '
                'erkannter Emotion (>=16 von 20 Hörern) und mind. 60% der '
                'Beurteilungen als natuerlich (>=12 von 20).'
            ),
        ),
    ],
)
def test_rest_api_get(url, expected_text):
    r = audfactory.rest_api_get(url)
    assert r.status_code == 200
    assert r.text == expected_text


@pytest.mark.parametrize(
    'pattern,expected_text',
    [
        (
            'latestVersion?g=edu.upenn.ldc&a=timit',
            '1.0.1',
        ),
    ],
)
def test_rest_api_search(pattern, expected_text):
    r = audfactory.rest_api_search(pattern)
    assert r.status_code == 200
    assert r.text == expected_text


@pytest.mark.parametrize(
    'group_id,name,version,repository,expected_url',
    [
        (
            'org.data.d1',
            'd1',
            '0.1.0',
            'maven',
            'org/data/d1/d1/0.1.0/d1-0.1.0.pom'
        ),
        (
            'de.dfki.mary',
            'dfkisemaine',
            '0.3.0-SNAPSHOT',
            'data-public-snapshot-local',
            ('de/dfki/mary/dfkisemaine/0.3.0-SNAPSHOT/'
             'dfkisemaine-0.3.0-SNAPSHOT.pom'),
        ),
        (
            'com.audeering.data.audbunittests',
            'audbunittests',
            '2.0.0-20200131.102728-2',
            'maven',
            ('com/audeering/data/audbunittests/audbunittests/2.0.0-SNAPSHOT/'
             'audbunittests-2.0.0-20200131.102728-2.pom'),
        ),
    ],
)
def test_server_pom_url(group_id, name, version, repository, expected_url):
    expected_url = artifactory(expected_url, repo=repository)
    url = audfactory.server_pom_url(
        group_id,
        name,
        version,
        repository=repository,
    )
    assert url == expected_url


@pytest.mark.parametrize(
    'versions,expeted_versions',
    [
        (
            ['0.1.1', '2.23.3', '3.0'],
            ['0.1.1', '2.23.3', '3.0'],
        ),
        (
            ['1.0.0', '1.0.0-SNASPHOT'],
            ['1.0.0-SNASPHOT', '1.0.0'],
        ),
        (
            ['1.0.0', '1.0.0-SNAPSHOT', '2.0.0'],
            ['1.0.0-SNAPSHOT', '1.0.0', '2.0.0'],
        ),
        (
            [
                '1.0.0-SNAPSHOT',
                '4.0.0-20200206.095424-2',
                '1.0.0',
                '2.0.0-20200131.102442-1',
                '3.0.0',
                '3.1.0',
                '4.0.0-20200206.095316-1',
                '3.2.0',
                '2.0.0-20200131.102728-2',
                '3.3.0',
                '3.4.0',
                '4.0.0-20200206.095534-3',
                '4.0.0',
            ],
            [
                '1.0.0-SNAPSHOT',
                '1.0.0',
                '2.0.0-20200131.102442-1',
                '2.0.0-20200131.102728-2',
                '3.0.0',
                '3.1.0',
                '3.2.0',
                '3.3.0',
                '3.4.0',
                '4.0.0-20200206.095316-1',
                '4.0.0-20200206.095424-2',
                '4.0.0-20200206.095534-3',
                '4.0.0',
            ],
        ),
    ],
)
def test_sort_versions(versions, expeted_versions):
    versions = audfactory.sort_versions(versions)
    assert versions == expeted_versions


@pytest.mark.parametrize(
    'group_id,name,repository,version,expected_url',
    [
        (
            '',
            None,
            'maven',
            None,
            '',
        ),
        (
            'com.audeering.data',
            None,
            'maven',
            None,
            'com/audeering/data',
        ),
        (
            'com.audeering.data',
            'database',
            'data-public-release-local',
            None,
            'com/audeering/data/database',
        ),
        (
            'com.audeering.data',
            'database',
            'maven',
            '1.1.0',
            'com/audeering/data/database/1.1.0',
        ),
    ],
)
def test_server_url(group_id, name, version, repository, expected_url):
    url = audfactory.server_url(
        group_id,
        name=name,
        repository=repository,
        version=version,
    )
    expected_url = artifactory(expected_url, repo=repository)
    assert url == expected_url


@pytest.mark.parametrize(
    'pom,expected_deps',
    [
        (
            empty_pom,
            '',  # and not {} as package type is not pom for empty_pom
        ),
        (
            pom_with_empty_deps,
            {},
        ),
        (
            emodb_pom,
            {
                'com.audeering.data.emodb:emodb-data:0.2.2':
                    {'info.bilderbar.emodb:emodb:1.0.0': 'zip'},
                'com.audeering.data.emodb:emodb-metadata:0.2.2': 'zip',
            }
        ),
    ],
)
def test_transitive_dependencies(pom, expected_deps):
    deps = audfactory.transitive_dependencies(pom)
    assert deps == expected_deps


@pytest.mark.parametrize(
    'deps,expected_deps_string',
    [
        (
            {},
            '',
        ),
        (
            {
                'com.audeering.data.emodb:emodb-data:0.2.2':
                    {'info.bilderbar.emodb:emodb:1.0.0': 'zip'},
                'com.audeering.data.emodb:emodb-metadata:0.2.2': 'zip',
            },
            ('+-com.audeering.data.emodb:emodb-data:0.2.2\n'
             '| +-info.bilderbar.emodb:emodb:1.0.0 (zip)\n'
             '+-com.audeering.data.emodb:emodb-metadata:0.2.2 (zip)\n'),
        ),
    ],
)
def test_transitive_dependencies_as_string(deps, expected_deps_string):
    deps_string = audfactory.transitive_dependencies_as_string(deps)
    assert deps_string == expected_deps_string


@pytest.mark.parametrize(
    'filename,content,repository,group_id,name,version',
    [
        (
            'audfactory-1.0.0.txt',
            'hello\nartifact',
            'models-public-local',
            'com.audeering.models',
            'audfactory',
            '1.0.0',
        ),
        pytest.param(
            'foo-1.0.0.txt',
            'hello\nartifact',
            'models-public-local',
            'com.audeering.models',
            'audfactory',
            '1.0.0',
            marks=pytest.mark.xfail(raises=ValueError),
        ),
        pytest.param(
            'file-not-found.txt',
            'hello\nartifact',
            'models-public-local',
            'com.audeering.models',
            'audfactory',
            '1.0.0',
            marks=pytest.mark.xfail(raises=FileNotFoundError),
        ),
    ]
)
def test_upload_artifact(filename, content, repository, group_id, name,
                         version):
    # Use random name to ensure parallel running
    random_string = uuid.uuid1()
    name = f'{name}-{random_string}'
    # Remove existing path to trigger new creation
    url = audfactory.server_url(
        group_id,
        repository=repository,
        name=name,
        version=version,
    )
    path = audfactory.artifactory_path(url)
    if path.exists():
        path.unlink()
    # create local file
    if filename != 'file-not-found.txt':
        filename_parts = filename.split('-')
        filename = f'{filename_parts[0]}-{random_string}-{filename_parts[1]}'
        with open(filename, 'w') as fp:
            fp.write(content)
    # upload artifact
    url = audfactory.upload_artifact(filename, repository, group_id, name,
                                     version)
    # clean up
    os.remove(filename)
    # check url
    assert url == os.path.join(audfactory.server_url(group_id,
                                                     name=name,
                                                     repository=repository,
                                                     version=version),
                               os.path.basename(filename))
    # download artifact
    path = audfactory.download_artifact(url, filename)
    # check content
    with open(path, 'r') as fp:
        lines = [line.strip() for line in fp.readlines()]
        assert content == '\n'.join(lines)
    # clean up
    os.remove(path)
    # check version
    versions = audfactory.versions(group_id, name, repository=repository)
    assert version in versions


@pytest.mark.parametrize(
    'group_id,name,pattern,expected_versions',
    [
        (
            'com.audeering.data.audbunittests',
            'audbunittests',
            None,
            [
                '1.0.0-20200131.093409-1',
                '1.0.0',
                '2.0.0-20200131.102442-1',
                '2.0.0-20200131.102728-2',
                '3.0.0',
                '3.1.0',
                '3.2.0',
                '3.3.0',
                '3.4.0',
                '4.0.0-20200206.095316-1',
                '4.0.0-20200206.095424-2',
                '4.0.0-20200206.095534-3',
                '4.0.0',
            ],
        ),
        (
            'com.audeering.data.audbunittests',
            'audbunittests',
            '*',
            [
                '1.0.0-20200131.093409-1',
                '1.0.0',
                '2.0.0-20200131.102442-1',
                '2.0.0-20200131.102728-2',
                '3.0.0',
                '3.1.0',
                '3.2.0',
                '3.3.0',
                '3.4.0',
                '4.0.0-20200206.095316-1',
                '4.0.0-20200206.095424-2',
                '4.0.0-20200206.095534-3',
                '4.0.0',
            ],
        ),
        (
            'de.dfki.mary',
            'dfkisemaine',
            '0.3.0-SNAPSHOT',
            ['0.3.0-SNAPSHOT'],
        ),
        (
            'com.audeering.data.audbunittests',
            'audbunittests',
            '1.0.0-SNAPSHOT',
            ['1.0.0-20200131.093409-1'],
        ),
        (
            'com.audeering.data.audbunittests',
            'audbunittests',
            '1.0.*',
            ['1.0.0-20200131.093409-1', '1.0.0'],
        ),
        (
            'com.audeering.data.audbunittests',
            'audbunittests',
            '1.*',
            ['1.0.0-20200131.093409-1', '1.0.0'],
        ),
        (
            'com.audeering.data.audbunittests',
            'audbunittests',
            '5.*',
            [],
        ),
        pytest.param(
            'com.audeering.data.audbunittests',
            'audbunittests',
            '1.0.0',
            [],
            marks=pytest.mark.xfail(raises=ValueError),
        ),
        (
            'com.audeering.data.audbunittests',
            'audbunittests',
            '2.*',
            ['2.0.0-20200131.102442-1', '2.0.0-20200131.102728-2'],
        ),
        (
            'com.audeering.data.non-existent',
            'non-existent',
            '1.*',
            [],
        ),
    ]
)
def test_versions(group_id, name, pattern, expected_versions):
    versions = audfactory.versions(group_id, name, pattern=pattern)
    assert versions == expected_versions
