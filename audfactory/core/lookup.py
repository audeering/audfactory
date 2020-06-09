import csv
import io
import os
import typing
import uuid

import audeer

from audfactory.core.config import config
import audfactory.core.api as audfactory


LOOKUP_EXT = 'csv'


class Lookup:
    r"""Lookup table for managing artifact flavors on Artifactory.

    It creates one row for every flavor,
    and assigns a unique ID to it.
    The columns are parameters associated with the flavor.
    The parameter names are stored as column headers.
    The column values can be of type
    :class:`bool`,
    :class:`float`,
    :class:`int`,
    :class:`NoneType`,
    :class:`str`,
    where ``''`` will be automatically converted to ``None``,
    ``'True'`` to ``True``,
    ``'False'`` to ``False``,
    ``'4.0'`` to ``4.0``,
    and ``'4'`` to ``4``.

    Args:
        group_id: group ID of lookup table
        name: name of lookup table
        version: version of lookup table
        repository: repository of lookup table

    Raises:
        RuntimeError: if no lookup tables or no lookup
            table with the specified version can be found

    """

    def __init__(
            self,
            group_id: str,
            *,
            name: str = 'lookup',
            version: str = None,
            repository: str = 'models-public-local',
    ):
        self.group_id = group_id
        self.name = name
        self.repository = repository

        if version is None:
            version = Lookup.latest_version(
                group_id,
                name=name,
                repository=repository,
            )

        if version is None:
            raise RuntimeError(
                f"No lookup tables available under group ID '{group_id}'"
            )
        elif not Lookup.exists(
                group_id, version, name=name, repository=repository):
            raise RuntimeError(
                f"Lookup table '{audfactory.group_id_to_path(group_id)}/"
                f"{name}-{version}.{LOOKUP_EXT}' does not exist yet."
            )

        self.version = version
        self.url = _url_table(group_id, name, version, repository)

    def __getitem__(self, uid: str):
        r"""Get lookup table entry by ID.

        Args:
            uid: ID of lookup table entry

        """
        table = self.table
        columns = _columns(table)
        item = {}
        for row in table[1:]:
            if row[0] == uid:
                item = {c: p for c, p in zip(columns, row[1:])}
                break
        return item

    @property
    def columns(self) -> typing.List:
        r"""Lookup table column names."""
        table = _download(self.url)
        return _columns(table)

    @property
    def ids(self) -> typing.List:
        r"""Lookup table ids."""
        table = _download(self.url)
        return _ids(table)

    @property
    def table(self) -> typing.List[typing.List]:
        r"""Lookup table."""
        return _download(self.url)

    def append(self, params: typing.Dict[str, typing.Any]) -> str:
        r"""Append entry to lookup table.

        Args:
            params: lookup table entry in the form of ``{column: parameter}``

        Returns:
            ID of added lookup table entry

        Raises:
            RuntimeError: if entry for given ``params`` exists already,
                or the columns ``params`` do not match the columns
                of the lookup
            ValueError: if ``params`` contain unsupported data types

        """
        table = self.table
        columns = _columns(table)
        _check_params_type(params)
        params = dict(sorted(params.items()))

        if self.contains(params):
            raise RuntimeError(f"Entry for '{params}' already exists.")
        if list(params.keys()) != columns:
            raise RuntimeError(
                f"Table columns '{columns}' do not match parameters '{params}'"
            )

        # Add an UID to the new row and append it to the table
        uid = str(uuid.uuid1())
        new_row = [uid] + list(params.values())
        table.append(new_row)
        _upload(table, self.group_id, self.name, self.version, self.repository)

        return uid

    def clear(self) -> None:
        r"""Clear lookup table."""
        table = self.table

        table = [table[0]]  # empty table with header
        _upload(table, self.group_id, self.name, self.version, self.repository)

    def contains(self, params: typing.Dict[str, typing.Any]) -> bool:
        r"""Check if lookup table contains entry.

        Args:
            params: lookup table entry in the form of ``{column: parameter}``

        Returns:
            ``True`` if lookup table contains entry

        """
        try:
            self.find(params)
        except RuntimeError:
            return False
        return True

    def extend(
            self,
            params: typing.Union[
                str,
                typing.Sequence[str],
                typing.Dict[str, typing.Any],
            ],
    ) -> typing.List[typing.List]:
        r"""Extend columns of lookup table.

        If no parameter values are given for the new columns,
        they are set to ``None``.

        Args:
            params: lookup table entry in the form of ``{column: parameter}``
                or ``[column]`` or ``column``

        Returns:
            lookup table

        Raises:
            ValueError: if ``params`` contain unsupported data types

        """
        if isinstance(params, str):
            params = [params]
        if isinstance(params, (tuple, list)):
            params = {param: None for param in params}
        _check_params_type(params)

        table = self.table
        columns = _columns(table)

        for param, value in params.items():
            if param not in columns:
                # Append param key to columns
                table[0] += [param]
                # FIXME: the following code seems ugly to me
                if len(table) == 1 and value is not None:
                    # Start from empty table, by first updating the columns
                    _upload(
                        table,
                        self.group_id,
                        self.name,
                        self.version,
                        self.repository,
                    )
                    original_params = {p: None for p in columns}
                    self.append({**original_params, **{param: value}})
                    table = self.table
                else:
                    for n in range(len(table[1:])):
                        # Append param value to every row
                        table[n + 1] += [value]

        table = _sort(table)
        _upload(table, self.group_id, self.name, self.version, self.repository)

        return table

    def find(self, params: typing.Dict[str, typing.Any]) -> str:
        r"""Find entry in lookup table.

        Args:
            params: lookup table entry in the form of ``{column: parameter}``

        Returns:
            ID of lookup table entry

        Raises:
            RuntimeError: if lookup table entry cannot be found

        """
        table = self.table
        params = dict(sorted(params.items()))

        for row in table[1:]:
            uid = row[0]
            entries = row[1:]
            if entries == list(params.values()):
                return uid

        raise RuntimeError(
            f"Could not find requested entry '{params}' "
            f"in version {self.version}:\n\n{table}"
        )

    def remove(self, params: typing.Dict[str, typing.Any]) -> str:
        r"""Remove entry from lookup table.

        Args:
            params: lookup table entry in the form of ``{column: parameter}``

        Returns:
            ID of removed entry

        """
        table = self.table
        uid = self.find(params)
        for n in range(len(table)):
            if table[n][0] == uid:
                table.pop(n)
                break
        _upload(table, self.group_id, self.name, self.version, self.repository)

        return uid

    @staticmethod
    def create(
            group_id: str,
            version: str,
            params: typing.Sequence[str] = (),
            *,
            name: str = 'lookup',
            repository: str = 'models-public-local',
            force: bool = False
    ) -> str:
        r"""Create lookup table on server.

        Args:
            group_id: group ID of lookup table
            version: version of lookup table
            params: lookup table column names
            name: name of lookup table
            repository: repository of lookup table
            force: if ``True`` an existing lookup table is overwritten

        Returns:
            URL of lookup table

        Raises:
            RuntimeError: if lookup table exists already
                and ``force=False``

        """
        ex = Lookup.exists(group_id, version, name=name, repository=repository)
        if force or not ex:
            table = [['id'] + sorted(params)]
            _upload(table, group_id, name, version, repository)
        else:
            raise RuntimeError(
                f"Lookup table '{name}-{version}' exists already."
            )
        return _url_table(group_id, name, version, repository)

    @staticmethod
    def delete(
            group_id: str,
            version: str,
            *,
            name: str = 'lookup',
            repository: str = 'models-public-local',
            force: bool = True,
    ) -> None:
        r"""Delete lookup table on server.

        Args:
            group_id: group ID of lookup table
            version: version of lookup table
            name: name of lookup table
            repository: repository of lookup table
            force: if ``True`` removes lookup table even if not empty

        Raises:
            RuntimeError: if lookup table is not empty
                and ``force=False``

        """
        lookup = Lookup(
            group_id,
            name=name,
            version=version,
            repository=repository,
        )
        if len(lookup.table) > 1:
            if not force:
                raise RuntimeError(
                    f"Cannot remove lookup table '{name}-{version}' "
                    f"if it is not empty.")
            lookup.clear()
        audfactory.artifactory_path(lookup.url).parent.rmdir()

    @staticmethod
    def exists(
            group_id: str,
            version: str,
            *,
            name: str = 'lookup',
            repository: str = 'models-public-local',
    ) -> bool:
        r"""Check if lookup table exists on server.

        Args:
            group_id: group ID of lookup table
            version: version of lookup table
            name: name of lookup table
            repository: repository of lookup table

        Returns:
            ``True`` if lookup table exists

        """
        versions = audfactory.versions(group_id, name, repository=repository)
        return version in versions

    @staticmethod
    def latest_version(
            group_id: str,
            *,
            params: typing.Dict[str, typing.Any] = None,
            name: str = 'lookup',
            repository: str = 'models-public-local',
    ) -> typing.Optional[str]:
        r"""Latest version of lookup table on server.

        Args:
            group_id: group ID of lookup table
            params: lookup table entry in the form of ``{column: parameter}``
            name: name of lookup table
            repository: repository of lookup table

        Returns:
            latest version of lookup table

        """
        v = Lookup.versions(group_id, params, name=name, repository=repository)
        if len(v) > 0:
            return v[-1]
        else:
            return None

    @staticmethod
    def versions(
            group_id: str,
            params: typing.Dict[str, typing.Any] = None,
            *,
            name: str = 'lookup',
            repository: str = 'models-public-local',
    ) -> list:
        r"""Available versions of lookup table on server.

        Args:
            group_id: group ID of lookup table
            params: lookup table entry in the form of ``{column: parameter}``
            name: name of lookup table
            repository: repository of lookup table

        Returns:
            available versions of lookup table

        """
        versions = audfactory.versions(group_id, name, repository=repository)
        if params is not None:
            filtered_versions = []
            for version in versions:
                lookup = Lookup(
                    group_id,
                    name=name,
                    version=version,
                    repository=repository,
                )
                if lookup.contains(params):
                    filtered_versions.append(version)
            versions = filtered_versions
        return versions


def _check_params_type(params):
    r"""Raise error if params includes wrong data types."""
    for value in params.values():
        if not isinstance(value, (bool, float, int, type(None), str)):
            raise ValueError(
                "'params' can only contain values of type: "
                "bool, float, int, NoneType, str. "
                f"Yours includes {type(value)}"
            )
        if isinstance(value, str):
            # Forbid strings that are converted to other types
            try:
                int(value)
            except ValueError:
                pass
            else:
                raise ValueError(
                    f"'{value}' is forbidden, use the int {value} instead"
                )
            try:
                float(value)
            except ValueError:
                pass
            else:
                raise ValueError(
                    f"'{value}' is forbidden, use the float {value} instead"
                )
            if value in ['True', 'False']:
                raise ValueError(
                    f"'{value}' is forbidden, use the bool {value} instead"
                )
            if value == 'None':
                raise ValueError(
                    f"'{value}' is forbidden, use the NoneType {value} instead"
                )


def _columns(table: typing.List[typing.List]) -> typing.List:
    return table[0][1:]


def _ids(table: typing.List[typing.List]) -> typing.List:
    return [row[0] for row in table[1:]]


def _import_csv(s):
    r"""Convert strings to int, float, and None.

    The build in CSV reader returns only strings.
    """
    if s == '':
        return None
    if s == 'True':
        return True
    if s == 'False':
        return False
    try:
        s = int(s)
    except ValueError:
        try:
            s = float(s)
        except ValueError:
            pass
    return s


def _download(url: str) -> typing.List[typing.List]:
    # Remove https://... at the beginning as not needed for rest API
    url = url[len(f'{config.ARTIFACTORY_ROOT}/'):]
    r = audfactory.rest_api_get(url)
    code = r.status_code
    if code in [403, 404]:  # pragma: no cover
        raise RuntimeError(
            f"{code}, URL not found or no access rights: '{url}'"
        )
    elif code != 200:  # pragma: no cover
        raise RuntimeError(
            f"{code}, problem downloading '{url}'.\n{audfactory.REPORT_ISSUE}"
        )
    r.encoding = 'utf-8'
    table = []
    csvreader = csv.reader(r.text.splitlines(), delimiter=',')
    for row in csvreader:
        # Convert '' to None
        row = [_import_csv(r) for r in row]
        table.append(row)
    return table


def _sort(table: typing.List[typing.List]) -> typing.List[typing.List]:
    # Get index to sort each row, excluding 'id'
    idx = sorted(range(len(table[0][1:])), key=lambda k: table[0][k + 1])
    idx = [0] + [i + 1 for i in idx]
    for n in range(len(table)):
        table[n] = [table[n][i] for i in idx]
    return table


def _upload(
        table: typing.List[typing.List],
        group_id: str,
        name: str,
        version: str,
        repository: str,
) -> None:
    r"""Upload table to a CSV file on Artifactory without using a tmp file."""
    fobj = io.StringIO()
    writer = csv.writer(fobj, delimiter=',')
    writer.writerows(table)
    # Seek to beginning of file, otherwise an empty CSV file wil be written
    fobj.seek(0)
    url = _url_table(group_id, name, version, repository)
    artifactory_path = audfactory.artifactory_path(url)
    if not artifactory_path.parent.exists():
        artifactory_path.parent.mkdir()
    artifactory_path.deploy(fobj)

    return url


def _url_table(
        group_id: str,
        name: str,
        version: str,
        repository: str,
) -> str:
    url = audfactory.server_url(
        group_id,
        name=name,
        repository=repository,
        version=version,
    )
    return f'{url}/{name}-{version}.{LOOKUP_EXT}'
