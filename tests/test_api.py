import copy
import os
import pytest

import audfactory

from example_poms import (
    emodb_pom,
    empty_pom,
    example_pom,
    pom_with_empty_deps,
)


def artifactory(path):
    """Add artifactory URL in front of path."""
    url = 'https://artifactory.audeering.com/artifactory/maven/'
    return url + path


@pytest.mark.parametrize(
    'url,expected_urls',
    [
        (
            'info/bilderbar/emodb/emodb/',
            ['info/bilderbar/emodb/emodb/maven-metadata.xml',
             'info/bilderbar/emodb/emodb/1.0.0',
             'info/bilderbar/emodb/emodb/1.1.0-SNAPSHOT'],
        ),
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
    'urls,force_download',
    [
        (
            [],
            False,
        ),
        (
            [('com/audeering/data/emodb/emodb-metadata/0.2.2/'
              'emodb-metadata-0.2.2.zip')],
            False,
        ),
        (
            [('com/audeering/data/emodb/emodb-metadata/0.2.2/'
              'emodb-metadata-0.2.2.zip')],
            False,
        ),
        (
            [('com/audeering/data/emodb/emodb-metadata/0.2.2/'
              'emodb-metadata-0.2.2.zip')],
            True,
        ),
        (
            [('com/audeering/data/emodb/emodb-metadata/0.2.2/'
              'emodb-metadata-0.2.2.zip'),
             ('com/audeering/data/testdata/testdata-metadata/1.2.1/'
              'testdata-metadata-1.2.1.zip')],
            False,
        ),
    ],
)
def test_download_artifacts(tmpdir, urls, force_download):
    artifact_urls = [artifactory(u) for u in urls]
    cache = str(tmpdir.mkdir('audfactory'))
    paths = audfactory.download_artifacts(
        artifact_urls,
        cache,
        chunk=4 * 1024,
        force_download=force_download,
        verbose=False,
    )
    for p in paths:
        assert os.path.exists(p)
    # Remove cache + / from returned paths
    paths = [p[len(cache) + 1:] for p in paths]
    assert paths == urls


@pytest.mark.parametrize(
    'pom_url,expected_description,expected_license,expected_packaging',
    [
        (
            'com/audeering/data/testdata/testdata/1.2.1/testdata-1.2.1.pom',
            'Test data set with 100 WAV files.',
            'CC0 1.0',
            'pom',
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
    'pattern,expected_text',
    [
        (
            'latestVersion?g=edu.upenn.ldc&a=timit',
            '1.0.1',
        ),
    ],
)
def test_rest_api_request(pattern, expected_text):
    r = audfactory.rest_api_request(pattern)
    assert r.status_code == 200
    assert r.text == expected_text


@pytest.mark.parametrize(
    'group_id,name,version,expected_url',
    [
        (
            'org.data.d1',
            'd1',
            '0.1.0',
            'org/data/d1/d1/0.1.0/d1-0.1.0.pom'
        ),
        (
            'de.dfki.mary',
            'dfkisemaine',
            '0.3.0-SNAPSHOT',
            ('de/dfki/mary/dfkisemaine/0.3.0-SNAPSHOT/'
             'dfkisemaine-0.3.0-SNAPSHOT.pom'),
        ),
        (
            'com.audeering.data.audbunittests',
            'audbunittests',
            '2.0.0-20200131.102728-2',
            ('com/audeering/data/audbunittests/audbunittests/2.0.0-SNAPSHOT/'
             'audbunittests-2.0.0-20200131.102728-2.pom'),
        ),
    ],
)
def test_server_pom_url(group_id, name, version, expected_url):
    expected_url = artifactory(expected_url)
    url = audfactory.server_pom_url(group_id, name, version)
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
    'group_id,name,version,expected_url',
    [
        (
            '',
            None,
            None,
            '',
        ),
        (
            'com.audeering.data',
            None,
            None,
            'com/audeering/data',
        ),
        (
            'com.audeering.data',
            'database',
            None,
            'com/audeering/data/database',
        ),
        (
            'com.audeering.data',
            'database',
            '1.1.0',
            'com/audeering/data/database/1.1.0',
        ),
    ],
)
def test_server_url(group_id, name, version, expected_url):
    url = audfactory.server_url(
        group_id,
        name=name,
        version=version,
    )
    expected_url = artifactory(expected_url)
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
        pytest.param(
            'com.audeering.data.audbunittests',
            'audbunittests',
            '1.0.0',
            None,
            marks=pytest.mark.xfail(raises=ValueError),
        ),
        (
            'com.audeering.data.audbunittests',
            'audbunittests',
            '2.*',
            ['2.0.0-20200131.102442-1', '2.0.0-20200131.102728-2'],
        ),
    ]
)
def test_versions(group_id, name, pattern, expected_versions):
    versions = audfactory.versions(group_id, name, pattern=pattern)
    assert versions == expected_versions
