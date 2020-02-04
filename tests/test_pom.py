import pytest

import audfactory as audf

from example_poms import example_pom, empty_pom


@pytest.mark.parametrize(
    'pom,expected_description',
    [
        (example_pom, 'Test database'),
        (empty_pom, ''),
    ],
)
def test_description(pom, expected_description):
    assert audf.pom.description(pom) == expected_description


@pytest.mark.parametrize(
    'pom,expected_group_id',
    [
        (example_pom, 'com.audeering.data.database'),
        (empty_pom, ''),
    ],
)
def test_group_id(pom, expected_group_id):
    assert audf.pom.group_id(pom) == expected_group_id


@pytest.mark.parametrize(
    'pom,expected_license',
    [
        (example_pom, ('CC0 1.0 <https://creativecommons.org/'
                       'publicdomain/zero/1.0/>')),
        (empty_pom, ''),
    ],
)
def test_license(pom, expected_license):
    assert audf.pom.license(pom) == expected_license


@pytest.mark.parametrize(
    'pom,expected_maintainer',
    [
        (example_pom, 'Firstname Lastname'),
        (empty_pom, ''),
    ],
)
def test_maintainer(pom, expected_maintainer):
    assert audf.pom.maintainer(pom) == expected_maintainer


@pytest.mark.parametrize(
    'pom,expected_name',
    [
        (example_pom, 'database'),
        (empty_pom, ''),
    ],
)
def test_name(pom, expected_name):
    assert audf.pom.name(pom) == expected_name


@pytest.mark.parametrize(
    'pom,expected_type',
    [
        (example_pom, 'pom'),
        (empty_pom, ''),
    ],
)
def test_type(pom, expected_type):
    assert audf.pom.type(pom) == expected_type


@pytest.mark.parametrize(
    'pom,expected_url',
    [
        (example_pom, 'https://gitlab.audeering.com/data/database'),
        (empty_pom, ''),
    ],
)
def test_url(pom, expected_url):
    assert audf.pom.url(pom) == expected_url


@pytest.mark.parametrize(
    'pom,expected_version',
    [
        (example_pom, '1.1.3'),
        (empty_pom, ''),
    ],
)
def test_version(pom, expected_version):
    assert audf.pom.version(pom) == expected_version
