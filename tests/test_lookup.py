import csv
import os
import uuid

import pandas as pd
import pytest

import audfactory


RANDOM_NAME = uuid.uuid1()
GROUP_ID = f'com.audeering.audfactory.unittest.{RANDOM_NAME}'
VERSION = '1.0.0'


@pytest.fixture()
def lookup_table():
    audfactory.Lookup.create(GROUP_ID, VERSION)
    lookup_table = audfactory.Lookup(GROUP_ID, version=VERSION)
    yield lookup_table
    # Clean up
    if audfactory.Lookup.exists(GROUP_ID, VERSION):
        lookup_table.clear()
        audfactory.Lookup.delete(GROUP_ID, VERSION)


@pytest.mark.parametrize(
    'group_id,version',
    [
        # Non existing version of lookup table
        pytest.param(
            'com.audeering.audfactory.non-existent',
            '1.0.0',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        # Non existing lookup tables
        pytest.param(
            'com.audeering.audfactory.non-existent',
            None,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ],
)
def test_init(group_id, version):
    audfactory.Lookup(group_id, version=version)


def test_getitem(lookup_table):
    params = {'a': 1, 'b': 2, 'c': 3}
    lookup_table.extend(list(params.keys()))
    lookup_table.append(params)
    table = lookup_table.table
    uid = table[1][0]
    assert params == lookup_table[uid]


def test_table(lookup_table):
    params = {'a': 1, 'b': 2.0, 'c': '3.0.0', 'd': True, 'e': '4.0', 'f': None}
    lookup_table.extend(list(params.keys()))
    lookup_table.append(params)
    csvfile = audfactory.download_artifact(lookup_table.url)
    df = pd.read_csv(csvfile)
    # Replace nan by None
    df['f'] = None
    os.remove(csvfile)
    table = lookup_table.table
    assert list(df.columns.values) == table[0]
    assert list(df.iloc[0, :].values) == table[1]
    with pytest.raises(AttributeError):
        lookup_table.table = []


def test_append(lookup_table):
    with pytest.raises(RuntimeError):
        lookup_table.append({'a': 1})
    # Extend lookup to 3 columns and add two new rows
    lookup_table.extend(('a', 'b', 'c'))
    lookup_table.append({'a': 1, 'b': 2, 'c': 3})
    lookup_table.append({'a': 4, 'b': 5, 'c': 6})
    table = lookup_table.table
    assert table[0] == ['id', 'a', 'b', 'c']
    assert table[1][1:] == [1, 2, 3]
    assert table[2][1:] == [4, 5, 6]
    assert table[1][0] != table[2][0]  # Checks for different IDs
    # Fail for trying to add the same row again
    with pytest.raises(RuntimeError):
        lookup_table.append({'a': 1, 'b': 2, 'c': 3})
    # Fail for trying to add a new row with wrong number of columns
    with pytest.raises(RuntimeError):
        lookup_table.append({'a': 1})
    # Fail for non-supported data types
    with pytest.raises(ValueError):
        lookup_table.append({'a': len})


def test_contains(lookup_table):
    p1 = {'a': 1}
    p2 = {'b': 2.0}
    assert not lookup_table.contains(p1)
    lookup_table.extend(p1)
    assert lookup_table.contains(p1)
    lookup_table.extend(p2)
    assert not lookup_table.contains(p1)
    assert not lookup_table.contains(p2)
    assert lookup_table.contains({**p1, **p2})


def test_extend(lookup_table):
    lookup_table.extend('a')
    assert lookup_table.table[0] == ['id', 'a']
    lookup_table.extend(('b', 'c'))
    assert lookup_table.table[0] == ['id', 'a', 'b', 'c']
    lookup_table.extend(['d'])
    assert lookup_table.table[0] == ['id', 'a', 'b', 'c', 'd']
    lookup_table.extend(('a', 'b'))
    assert lookup_table.table[0] == ['id', 'a', 'b', 'c', 'd']
    lookup_table.append({'a': 1.0, 'b': 2, 'c': True, 'd': '4.0.0'})
    lookup_table.extend('e')
    table = lookup_table.table
    assert table[0] == ['id', 'a', 'b', 'c', 'd', 'e']
    assert table[1][1:] == [1.0, 2, True, '4.0.0', None]
    lookup_table.extend({'f': False})
    table = lookup_table.table
    assert table[0] == ['id', 'a', 'b', 'c', 'd', 'e', 'f']
    assert table[1][1:] == [1.0, 2, True, '4.0.0', None, False]
    # Restart from empty one and assign dict
    lookup_table.clear()
    lookup_table.extend({'g': 7})
    table = lookup_table.table
    assert table[0] == ['id', 'a', 'b', 'c', 'd', 'e', 'f', 'g']
    assert table[1][1:] == [None, None, None, None, None, None, 7]
    # Fail for non-supported data types
    with pytest.raises(ValueError):
        lookup_table.append({'a': len})


def test_find(lookup_table):
    p = {'a': 1}
    with pytest.raises(RuntimeError):
        lookup_table.find(p)
    lookup_table.extend(p)
    assert lookup_table.find(p) == lookup_table.table[1][0]


def test_remove(lookup_table):
    p = {'a': 1}
    with pytest.raises(RuntimeError):
        lookup_table.remove(p)
    lookup_table.extend(p)
    lookup_table.remove(p)
    assert lookup_table.table == [['id', 'a']]


@pytest.mark.parametrize(
    'params,expected_columns',
    [
        (
            ('a', 'b', 'c'),
            ['id', 'a', 'b', 'c'],
        ),
        (
            (),
            ['id'],
        ),
    ],
)
def test_create(params, expected_columns):
    # Create a new lookup table
    url = audfactory.Lookup.create(GROUP_ID, VERSION, params)
    # Raise error if lookup table exists already
    with pytest.raises(RuntimeError):
        audfactory.Lookup.create(GROUP_ID, VERSION, params)
    # Check content of CSV file
    lookup_file = audfactory.download_artifact(url)
    with open(lookup_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        assert next(reader) == expected_columns
    # Clean up
    os.remove(lookup_file)
    audfactory.Lookup.delete(GROUP_ID, VERSION)


@pytest.mark.parametrize(
    'empty,force',
    [
        (
            True,
            False,
        ),
        # Fail for deleting non-empty table
        pytest.param(
            False,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        (
            False,
            True,
        ),
    ],
)
def test_delete(lookup_table, empty, force):
    if not empty:
        lookup_table.extend({'a': 1})
    audfactory.Lookup.delete(GROUP_ID, VERSION, force=force)


def test_exists(lookup_table):
    assert audfactory.Lookup.exists(GROUP_ID, VERSION)
    assert not audfactory.Lookup.exists(GROUP_ID, '0.0.0')


def test_latest_version(lookup_table):
    p = {'a': 1}
    assert audfactory.Lookup.latest_version(GROUP_ID) == VERSION
    assert audfactory.Lookup.latest_version(GROUP_ID, params=p) is None
    lookup_table.extend(p)
    assert audfactory.Lookup.latest_version(GROUP_ID, params=p) == VERSION
    assert audfactory.Lookup.latest_version(GROUP_ID, params={'a': 0}) is None


def test_versions(lookup_table):
    p = {'a': 1}
    assert audfactory.Lookup.versions(GROUP_ID) == [VERSION]
    assert audfactory.Lookup.versions(GROUP_ID, params=p) == []
    lookup_table.extend(p)
    assert audfactory.Lookup.versions(GROUP_ID, params=p) == [VERSION]
    assert audfactory.Lookup.versions(GROUP_ID, params={'a': 0}) == []
    # Add another version
    audfactory.Lookup.create(GROUP_ID, '2.0.0')
    assert audfactory.Lookup.versions(GROUP_ID) == [VERSION, '2.0.0']
    assert audfactory.Lookup.versions(GROUP_ID, params=p) == [VERSION]
    audfactory.Lookup.delete(GROUP_ID, '2.0.0')


@pytest.mark.parametrize(
    'table,expected_table',
    [
        (
            [['id']],
            [['id']],
        ),
        (
            [['id', 'a', 'b']],
            [['id', 'a', 'b']],
        ),
        (
            [['id', 'b', 'a']],
            [['id', 'a', 'b']],
        ),
        (
            [['id', 'a', 'b'], ['0', 1, 2]],
            [['id', 'a', 'b'], ['0', 1, 2]],
        ),
        (
            [['id', 'b', 'a'], ['0', 2, 1]],
            [['id', 'a', 'b'], ['0', 1, 2]],
        ),
    ],
)
def test_sort(table, expected_table):
    sorted_table = audfactory.core.lookup._sort(table)
    assert sorted_table == expected_table