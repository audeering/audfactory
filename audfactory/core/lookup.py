import csv
import io
import typing

import audeer

import audfactory.core.api as audfactory


# Skip doctests until we have public lookup tables
__doctest_skip__ = ['*']


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
    :class:`str`.
    You cannot use strings
    that would be converted to any of the other types like
    ``'None'``,
    ``'True'``,
    ``'False'``,
    ``'4.0'``,
    and ``'4'``.

    The following code converts an :class:`audfactory.Lookup` object
    into a :class:`pandas.DataFrame`:

    .. code-block:: python

        index, data = [], []
        if len(lookup.table) > 1:
            index = [entry[0] for entry in lookup.table[1:]]
            data = [entry[1:] for entry in lookup.table[1:]]
        df = pd.DataFrame(data=data, index=index, columns=lookup.columns)

    Args:
        server: URL of Artifactory server,
            e.g. https://audeering.jfrog.io/artifactory
        repository: repository of lookup table
        group_id: group ID of lookup table
        name: name of lookup table
        version: version of lookup table

    Raises:
        RuntimeError: if no lookup tables or no lookup
            table with the specified version can be found

    Examples:
        >>> lookup = Lookup(
        ...     'https://artifactory.audeering.com/artifactory',
        ...     'models-public-local',
        ...     'com.audeering.models.gender.voxcnn',
        ...     version='0.2.0',
        ... )
        >>> lookup
        id                                    purpose  sampling_rate  train-db
        3bb24968-759a-11ea-ab25-309c2364e602  prod     16000          voxceleb1
        >>> lookup.table
        [['id', 'purpose', 'sampling_rate', 'train-db'],
         ['3bb24968-759a-11ea-ab25-309c2364e602', 'prod', 16000, 'voxceleb1']]
        >>> lookup['3bb24968-759a-11ea-ab25-309c2364e602']
        {'purpose': 'prod', 'sampling_rate': 16000, 'train-db': 'voxceleb1'}

    """

    def __init__(
            self,
            server,
            repository: str,
            group_id: str,
            *,
            name: str = 'lookup',
            version: str = None,
    ):
        self.server = server
        """server URL"""
        self.group_id = group_id
        """group ID of lookup table"""
        self.name = name
        """name of lookup table"""
        self.repository = repository
        """repository of lookup table"""

        if version is None:
            version = Lookup.latest_version(
                server,
                repository,
                group_id,
                name=name,
            )

        if version is None:
            url = audfactory.url(
                server,
                repository=repository,
                group_id=group_id,
                name=name,
            )
            raise RuntimeError(
                f"No lookup tables available under '{url}'"
            )
        elif not Lookup.exists(
                server, repository, group_id, version, name=name
        ):
            url = audfactory.url(
                server,
                repository=repository,
                group_id=group_id,
                name=name,
                version=version,
            )
            raise RuntimeError(
                f"Lookup table '{url}/"
                f"{name}-{version}.{LOOKUP_EXT}' does not exist yet."
            )

        self.version = version
        """version of lookup table"""
        self.url = _url_table(server, repository, group_id, name, version)
        """Artifactory URL of lookup table"""

    def __getitem__(self, uid: str) -> typing.Dict:
        r"""Get lookup table entry by ID.

        Args:
            uid: ID of lookup table entry

        Returns:
            lookup table entry

        """
        table = self.table
        columns = _columns(table)
        item = {}
        for row in table[1:]:
            if row[0] == uid:
                item = {c: p for c, p in zip(columns, row[1:])}
                break
        return item

    def __repr__(self):
        r"""String representation of lokkup table."""
        table = self.table
        padding = 2
        # Longest string in each column
        transposed_table = [list(x) for x in zip(*table)]
        col_width = [
            len(max([str(word) for word in row], key=len)) + padding
            for row in transposed_table
        ]
        # Don't pad the last column
        col_width[-1] -= padding
        row = [
            ''.join(
                str(word).ljust(width) for word, width in zip(row, col_width)
            )
            for row in table
        ]
        return '\n'.join(row)

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

        The lookup table entry gets a unique ID
        from ``params``,
        :attr:`self.name`,
        :attr:`self.group_id`,
        :attr:`self.version`,
        and :attr:`self.repository`.

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
        uid = self.generate_uid(
            params=str(params),
            group_id=self.group_id,
            name=self.name,
            version=self.version,
            repository=self.repository,
        )
        new_row = [uid] + list(params.values())
        table.append(new_row)
        _upload(table, self.url)

        return uid

    def clear(self) -> None:
        r"""Clear lookup table."""
        table = self.table

        table = [table[0]]  # empty table with header
        _upload(table, self.url)

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
                    _upload(table, self.url)
                    original_params = {p: None for p in columns}
                    self.append({**original_params, **{param: value}})
                    table = self.table
                else:
                    for n in range(len(table[1:])):
                        # Append param value to every row
                        table[n + 1] += [value]

        table = _sort(table)
        _upload(table, self.url)

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
        _upload(table, self.url)

        return uid

    @staticmethod
    def create(
            server: str,
            repository: str,
            group_id: str,
            version: str,
            params: typing.Sequence[str] = (),
            *,
            name: str = 'lookup',
            force: bool = False
    ) -> str:
        r"""Create lookup table on server.

        Args:
            server: URL of Artifactory server,
                e.g. https://audeering.jfrog.io/artifactory
            repository: repository of lookup table
            group_id: group ID of lookup table
            version: version of lookup table
            params: lookup table column names
            name: name of lookup table
            force: if ``True`` an existing lookup table is overwritten

        Returns:
            URL of lookup table

        Raises:
            RuntimeError: if lookup table exists already
                and ``force=False``

        """
        ex = Lookup.exists(server, repository, group_id, version, name=name)
        url = _url_table(server, repository, group_id, name, version)
        if force or not ex:
            table = [['id'] + sorted(params)]
            _upload(table, url)
        else:
            raise RuntimeError(
                f"Lookup table '{name}-{version}' exists already."
            )
        return url

    @staticmethod
    def delete(
            server: str,
            repository: str,
            group_id: str,
            version: str,
            *,
            name: str = 'lookup',
            force: bool = True,
    ) -> None:
        r"""Delete lookup table on server.

        Args:
            server: URL of Artifactory server,
                e.g. https://audeering.jfrog.io/artifactory
            repository: repository of lookup table
            group_id: group ID of lookup table
            version: version of lookup table
            name: name of lookup table
            force: if ``True`` removes lookup table even if not empty

        Raises:
            RuntimeError: if lookup table is not empty
                and ``force=False``

        """
        lookup = Lookup(
            server,
            repository,
            group_id,
            name=name,
            version=version,
        )
        if len(lookup.table) > 1:
            if not force:
                raise RuntimeError(
                    f"Cannot remove lookup table '{name}-{version}' "
                    f"if it is not empty.")
            lookup.clear()
        audfactory.path(lookup.url).parent.rmdir()

    @staticmethod
    def exists(
            server: str,
            repository: str,
            group_id: str,
            version: str,
            *,
            name: str = 'lookup',
    ) -> bool:
        r"""Check if lookup table exists on server.

        Args:
            server: URL of Artifactory server,
                e.g. https://audeering.jfrog.io/artifactory
            repository: repository of lookup table
            group_id: group ID of lookup table
            version: version of lookup table
            name: name of lookup table

        Returns:
            ``True`` if lookup table exists

        Examples:
            >>> Lookup.exists(
            ...     'https://artifactory.audeering.com/artifactory',
            ...     'models-public-local',
            ...     'com.audeering.models.gender.voxcnn',
            ...     '0.1.0',
            ... )
            True

        """
        versions = audfactory.versions(server, repository, group_id, name)
        return version in versions

    @staticmethod
    def latest_version(
            server: str,
            repository: str,
            group_id: str,
            *,
            params: typing.Dict[str, typing.Any] = None,
            name: str = 'lookup',
    ) -> typing.Optional[str]:
        r"""Latest version of lookup table on server.

        Args:
            server: URL of Artifactory server,
                e.g. https://audeering.jfrog.io/artifactory
            repository: repository of lookup table
            group_id: group ID of lookup table
            params: lookup table entry in the form of ``{column: parameter}``
            name: name of lookup table

        Returns:
            latest version of lookup table

        Examples:
            >>> Lookup.latest_version(
            ...     'https://artifactory.audeering.com/artifactory',
            ...     'models-public-local',
            ...     'com.audeering.models.gender.voxcnn',
            ... )
            '0.2.0'

        """
        v = Lookup.versions(server, repository, group_id, params, name=name)
        if len(v) > 0:
            return v[-1]
        else:
            return None

    @staticmethod
    def generate_uid(
            *,
            params: typing.Dict[str, typing.Any],
            name: str,
            group_id: str,
            version: str,
            repository: str,
    ) -> str:
        r"""Generate unique ID.

        It converts ``params`` to a string,
        and concatenates it with ``name``, ``group_id``, ``version``,
        and ``repository``.
        From that concatenated string a unique ID is derived.

        Args:
            params: params in the form of ``{column: parameter}``
            group_id: group ID of lookup table
            name: name of lookup table
            version: version of lookup table
            repository: repository of lookup table

        Returns:
            unique identifier of length 36

        Examples:
            >>> Lookup.generate_uid(
            ...     params={0: None},
            ...     name='name',
            ...     group_id='group.id',
            ...     version='1.0.0',
            ...     repository='models-public-local',
            ... )
            'afe694a5-8bad-4dbc-73ba-636f18340615'

        """
        unique_string = (
            str(params)
            + group_id
            + name
            + version
            + repository
        )
        uid = audeer.uid(from_string=unique_string)
        return uid

    @staticmethod
    def versions(
            server: str,
            repository: str,
            group_id: str,
            params: typing.Dict[str, typing.Any] = None,
            *,
            name: str = 'lookup',
    ) -> list:
        r"""Available versions of lookup table on server.

        Args:
            server: URL of Artifactory server,
                e.g. https://audeering.jfrog.io/artifactory
            repository: repository of lookup table
            group_id: group ID of lookup table
            params: lookup table entry in the form of ``{column: parameter}``
            name: name of lookup table

        Returns:
            available versions of lookup table

        Examples:
            >>> Lookup.versions(
            ...     'https://artifactory.audeering.com/artifactory',
            ...     'models-public-local',
            ...     'com.audeering.models.gender.voxcnn',
            ... )
            ['0.1.0', '0.2.0']

        """
        versions = audfactory.versions(server, repository, group_id, name)
        if params is not None:
            filtered_versions = []
            for version in versions:
                lookup = Lookup(
                    server,
                    repository,
                    group_id,
                    name=name,
                    version=version,
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
        url: str,
) -> None:
    r"""Upload table to a CSV file on Artifactory without using a tmp file."""
    fobj = io.StringIO()
    writer = csv.writer(fobj, delimiter=',')
    writer.writerows(table)
    # Seek to beginning of file, otherwise an empty CSV file wil be written
    fobj.seek(0)
    artifactory_path = audfactory.path(url)
    if not artifactory_path.parent.exists():
        artifactory_path.parent.mkdir()
    artifactory_path.deploy(fobj)

    return url


def _url_table(
        server: str,
        repository: str,
        group_id: str,
        name: str,
        version: str,
) -> str:
    url = audfactory.url(
        server,
        repository=repository,
        group_id=group_id,
        name=name,
        version=version,
    )
    return f'{url}/{name}-{version}.{LOOKUP_EXT}'
