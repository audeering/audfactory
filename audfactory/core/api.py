from collections import OrderedDict
import os
import re
from typing import Dict, List, Tuple

from artifactory import ArtifactoryPath, get_global_config_entry
import audeer
import requests
import xmltodict

from audfactory.core import pom as _pom
from audfactory.core.config import config


def artifactory_path(
        url: str
) -> ArtifactoryPath:
    r"""Authenticate at Artifactory and get path object.

    You can set your username and API key in the console:

    .. code-block:: bash

        $ export ARTIFACTORY_USERNAME=...
        $ export ARTIFACTORY_API_KEY=...

    If they are not specified,
    they are read from :file:`~/.artifactory_python.cfg`.

    Args:
        url: URL to path on Artifactory

    Returns:
        Artifactory path object similar to pathlib.Path

    Example:
        >>> path = artifactory_path(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/'
        ... )
        >>> for p in path:
        ...     print(os.path.basename(str(p)))
        ...
        timit-metadata
        timit-data
        timit

    """
    apikey = os.getenv('ARTIFACTORY_API_KEY', None)
    username = os.getenv('ARTIFACTORY_USERNAME', None)
    if apikey is None or username is None:
        return ArtifactoryPath(url)
    else:
        return ArtifactoryPath(url, auth=(username, apikey))


def dependencies(
        pom: Dict
) -> List:
    r"""Extract all direct dependencies from a POM.

    The dependencies are returned in a list,
    and each entry has the form: ``'{group_id}:{name}:{version}'``

    Args:
        pom: POM of artifact the dependencies are extracted from

    Returns:
        sorted list of dependencies

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> dependencies(pom)
        ['com.audeering.data.timit:timit-data:1.0.1',
         'com.audeering.data.timit:timit-metadata:1.0.1']

    """
    try:
        deps = pom['project']['dependencies']['dependency']
        if not isinstance(deps, list):
            deps = [deps]
    except (KeyError, TypeError):
        deps = []

    def dict_to_string(d: Dict) -> str:
        """Dependency as 'group_id:name:version'."""
        return (
            '{}:{}:{}'
            .format(_pom.group_id(d), _pom.name(d), _pom.version(d))
        )

    return sorted([dict_to_string(d) for d in deps])


def download_artifacts(
        artifact_urls: List,
        destination: str,
        *,
        chunk: int = 4 * 1024,
        force_download: bool = False,
        verbose: bool = True
) -> List:
    r"""Download listed artifacts.

    The artifacts will be stored inside the :file:`destination` folder,
    in sub-folders named after::

        {group_id_as_path}/{name}/{version}/{name}-{version}.{extension}

    Args:
        artifact_urls: list of URLs of the artifact files to download
        destination: folder under which the artifacts should be stored
        chunk: amount of data read at once during the download
        force_download: forces the artifact to be downloaded
            even if it exists locally already
        verbose: show information on the download process

    Returns:
        list of local artifact paths

    Raises:
        RuntimeError: if the provided artifact URLs are not valid

    Example:
        >>> files = download_artifacts(
        ...     [('https://artifactory.audeering.com/artifactory/maven/'
        ...       'com/audeering/data/audbunittests/audbunittests-data/'
        ...       '4.0.0/audbunittests-data-4.0.0.flac')],
        ...     '.',
        ... )
        >>> os.path.basename(files[0])
        'audbunittests-data-4.0.0.flac'

    """
    destination = audeer.safe_path(destination)
    audeer.mkdir(destination)
    dst_paths = []
    download_items = []

    # Get artifact paths, sizes, and destination paths
    with audeer.progress_bar(
            total=len(artifact_urls),
            disable=not verbose,
    ) as pbar:
        for artifact_url in artifact_urls:

            desc = audeer.format_display_message(
                'Scan {}'.format(os.path.basename(artifact_url)),
                pbar=True,
            )
            pbar.set_description_str(desc)
            pbar.refresh()

            repo_url = '{}/{}'.format(
                config.ARTIFACTORY_ROOT,
                config.ARTIFACTORY_REPO,
            )
            if artifact_url.startswith(repo_url):
                # Extract destination path from source URL
                relative_url = artifact_url[len(repo_url):]
                if relative_url.startswith('/'):
                    relative_url = relative_url[1:]
                dst_path = os.path.join(
                    destination,
                    relative_url,
                )
            else:
                raise RuntimeError(
                    '{} has to start with {}'
                    .format(artifact_url, repo_url)
                )

            # Append all destination paths,
            # including the ones data is already downloaded
            dst_paths.append(dst_path)

            if not os.path.exists(dst_path) or force_download:
                src_path = artifactory_path(artifact_url)
                src_size = ArtifactoryPath.stat(src_path).size
                download_items.append((dst_path, src_path, src_size))

            pbar.update()

    # Download artifacts
    _download_artifacts(download_items, chunk, verbose)

    return dst_paths


def download_pom(
        pom_url: str
) -> OrderedDict:
    r"""Retrieves a POM from Artifactory.

    Args:
        pom_url: URL of POM file to download

    Returns:
        parsed POM

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'edu/upenn/ldc/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> pom['project']['url']
        'https://catalog.ldc.upenn.edu/LDC93S1'

    """
    pom_path = artifactory_path(pom_url)
    with pom_path.open() as fp:
        pom = xmltodict.parse(fp.read())
    return pom


def exclude_dependencies(
        deps: Dict,
        pattern: str
) -> OrderedDict:
    r"""Exclude nodes of a transitive dependency tree.

    Args:
        deps: transitive dependencies
        pattern: regexp filter pattern specifying dependencies to exclude

    Returns:
        filtered transitive dependency tree

    Example:
        >>> deps = {'a': {'b': {'c': {'c1': [], 'c2': []}, 'd': []}}}
        >>> exclude_dependencies(deps, pattern='c')
        OrderedDict([('a', OrderedDict([('b', OrderedDict([('d', [])]))]))])

    """
    filtered_deps = OrderedDict()
    for key, value in deps.items():
        if re.match(pattern, key):
            continue
        elif isinstance(value, dict):
            # Recursively traverse the sub-tree
            sub_tree = exclude_dependencies(value, pattern)
            # Only include sub-tree if not empty
            if sub_tree:
                filtered_deps[key] = sub_tree
        else:
            filtered_deps[key] = value
    return filtered_deps


def group_id_to_path(
        group_id: str
) -> str:
    r"""Replaces ``.`` by ``/`` in group ID.

    Args:
        group_id: group ID

    Returns:
        group ID path

    Example:
        >>> group_id_to_path('com.audeering.data.emodb')
        'com/audeering/data/emodb'

    """
    return '/'.join(group_id.split('.'))


def include_dependencies(
        deps: Dict,
        pattern: str
) -> OrderedDict:
    r"""Include nodes of a transitive dependency tree.

    Args:
        deps: transitive dependencies
        pattern: regexp filter pattern specifying dependencies to include

    Returns:
        filtered transitive dependency tree

    Example:
        >>> deps = {'a': {'b': {'c': {'c1': [], 'c2': []}, 'd': []}}}
        >>> include_dependencies(deps, pattern='d')
        OrderedDict([('a', OrderedDict([('b', OrderedDict([('d', [])]))]))])

    """
    filtered_deps = OrderedDict()
    for key, value in deps.items():
        if re.match(pattern, key):
            filtered_deps[key] = value
        elif isinstance(value, dict):
            # Recursively traverse the sub-tree
            sub_tree = include_dependencies(value, pattern)
            # Only include sub-tree if not empty
            if sub_tree:
                filtered_deps[key] = sub_tree
        else:
            continue
    return filtered_deps


def list_artifacts(
        deps: Dict
) -> List:
    r"""Extract all artifacts from a nested dependency tree.

    Such a dictionary can be created by :func:`transitive_dependencies`.
    It returns a list with the URL of all artifacts.

    Args:
        deps: dependency tree

    Returns:
        list of all included artifact URLs

    Example:
        >>> deps = {'a:a:1.0.0': {'b:b:1.0.0': 'zip', 'c:c:1.2.0': 'zip'}}
        >>> artifacts = list_artifacts(deps)
        >>> [os.path.basename(a) for a in artifacts]
        ['b-1.0.0.zip', 'c-1.2.0.zip']

    """
    artifact_urls = []

    if isinstance(deps, dict):
        for key, value in deps.items():
            if isinstance(value, dict):
                artifact_urls += list_artifacts(value)
            else:
                group_id, name, version = key.split(':')
                pom_url = server_pom_url(group_id, name, version)
                artifact_urls += [pom_url.replace('.pom', '.' + value)]
    # Ensure unique entries as some packages might have duplicted ones
    return sorted(list(set(artifact_urls)))


def rest_api_request(
        pattern: str
) -> requests.models.Response:
    """Execute a GET REST API query.

    For details on the REST API, see
    https://www.jfrog.com/confluence/display/JFROG/Artifactory+REST+API

    Args:
        pattern: search pattern

    Returns:
        server response

    Example:
        >>> r = rest_api_request('latestVersion?g=edu.upenn.ldc&a=timit')
        >>> r.text
        '1.0.1'

    """
    search_url = (
        '{}/api/search/{}&repos={}'
        .format(config.ARTIFACTORY_ROOT, pattern, config.ARTIFACTORY_REPO)
    )
    # Authentification
    apikey = os.getenv('ARTIFACTORY_API_KEY', None)
    username = os.getenv('ARTIFACTORY_USERNAME', None)
    if apikey is None or username is None:
        config_entry = get_global_config_entry(config.ARTIFACTORY_ROOT)
        username = config_entry['username']
        apikey = config_entry['password']
    return requests.get(search_url, auth=(username, apikey))


def server_url(
        group_id: str,
        *,
        name: str = None,
        version: str = None
) -> str:
    r"""Creates Artifactory URL from group_id, name, and version.

    Args:
        group_id: group ID of artifact
        name: name of artifact
        version: version of artifact

    Returns:
        URL to artifact location on server

    Example:
        >>> server_url('edu.upenn.ldc')
        'https://artifactory.audeering.com/artifactory/maven/edu/upenn/ldc'

    """
    group_id = group_id_to_path(group_id)
    if name is not None and version is not None:
        url = '{}/{}/{}'.format(group_id, name, version)
    elif name is not None:
        url = '{}/{}'.format(group_id, name)
    else:
        url = group_id
    return '{}/{}/{}'.format(
        config.ARTIFACTORY_ROOT,
        config.ARTIFACTORY_REPO,
        url,
    )


def server_pom_url(
        group_id: str,
        name: str,
        version: str
) -> str:
    r"""URL of POM generated from name, group_id, version.

    For snapshot versions you have to provide the exact version,
    e.g. ``'2.0.0-20200131.102728-2'``

    Args:
        group_id: group ID of artifact
        name: name of artifact
        version: version of artifact

    Returns:
        URL to POM

    Example:
        >>> server_pom_url('edu.upenn.ldc', 'timit', '1.0.1')
        'https://artifactory.audeering.com/artifactory/maven/edu/upenn/ldc/timit/1.0.1/timit-1.0.1.pom'

    """
    # Snapshot version folders on Artifactory have the form X.Y.Z-SNAPSHOT
    if len(version.split('-')) > 1:
        version_folder = version.split('-')[0] + '-SNAPSHOT'
    else:
        version_folder = version
    return '{}/{}-{}.pom'.format(
        server_url(group_id, name=name, version=version_folder),
        name,
        version,
    )


def transitive_dependencies(
        pom: Dict,
        *,
        verbose: bool = False
) -> OrderedDict:
    r"""Extract all transitive dependencies of a POM.

    Each dependency is used as a key of the dictionary
    with further dependencies as values.
    If there are no more transitive dependencies
    the package type of the artifact (e.g. ``'zip'``)
    is stored as the dictionary value.

    Args:
        pom: POM of artifact
        verbose: show progress messages

    Returns:
        transitive dependency tree

    Example:
        >>> url = server_pom_url('com.audeering.data.timit', 'timit', '1.0.0')
        >>> pom = download_pom(url)
        >>> transitive_dependencies(pom)
        OrderedDict([('com.audeering.data.timit:timit-data:1.0.0',
                      OrderedDict([('edu.upenn.ldc:timit:1.0.0', 'zip')])),
                     ('com.audeering.data.timit:timit-metadata:1.0.0', 'zip')])

    """
    package_type = _pom.type(pom)
    if package_type == 'pom':
        transitive_deps = OrderedDict()
        deps = dependencies(pom)

        for dep in deps:
            group_id, name, version = dep.split(':')
            pom_url = server_pom_url(group_id, name, version)
            if verbose:
                desc = audeer.format_display_message(
                    'Dependencies: {}'.format(dep),
                    pbar=False,
                )
                print(desc, end='\r')
            pom = download_pom(pom_url)
            transitive_deps[dep] = transitive_dependencies(
                pom,
                verbose=verbose,
            )

    else:
        transitive_deps = package_type

    return transitive_deps


def transitive_dependencies_as_string(
        d: Dict,
        *,
        prefix: str = ''
) -> str:
    r"""Transitive dependency graph as string output.

    This function is designed to be recursively called.

    Args:
        d: dependency tree
        prefix: string printed in front of ``+-``.
            This can be used in recursive calls to add ``|``

    Returns:
        dependency tree to use with :func:`print`

    Example:
        >>> url = server_pom_url('com.audeering.data.timit', 'timit', '1.0.0')
        >>> pom = download_pom(url)
        >>> d = transitive_dependencies(pom)
        >>> print(transitive_dependencies_as_string(d))
        +-com.audeering.data.timit:timit-data:1.0.0
        | +-edu.upenn.ldc:timit:1.0.0 (zip)
        +-com.audeering.data.timit:timit-metadata:1.0.0 (zip)

    """
    output = ''
    for n, (key, value) in enumerate(d.items()):
        output += '{}+-{}\n'.format(prefix, key)
        if n < len(d) - 1:
            # Add | connection line to next dep on same level
            new_prefix = prefix + '| '
        else:
            # Last entry in dict, no more deps on same level
            new_prefix = prefix + '  '
        if isinstance(value, dict):
            # Rerun until we reach a leaf of the dependency graph
            output += transitive_dependencies_as_string(
                value,
                prefix=new_prefix,
            )
        else:
            # Leaf entry adds "(value)" to same line as corresponding key
            output = '{} ({})\n'.format(output.rstrip(), str(value))
    return output


def versions(
        group_id: str,
        name: str,
        *,
        pattern: str = None
) -> str:
    r"""Versions of an artifact on Artifactory.

    It considers stable and snapshot releases.

    Args:
        name: name of artifact
        group_id: group ID of artifact
        pattern: limit versions to specified pattern.
            Could be ``'1.*'``
            or a snapshot like ``'1.1.1-SNAPSHOT'``

    Returns:
        versions of artifact on Artifactory

    Raises:
        RuntimeError: if versions cannot be determined
        ValueError: if wrong version pattern is provided

    Example:
        >>> versions('edu.upenn.ldc', 'timit')
        ['1.0.0', '1.0.1']

    """
    def sort_versions(versions):
        """Sort version and snapshot versions.

        As no Python package provides the desired results,
        we implement the sorting ourselves.

        Desired order is::

            [
                '0.0.1',
                '1.0.0-SNAPSHOT',
                '1.0.0-20200131.093409-1',
                '1.0.0',
                '2.0.0-20200131.093409-1',
                '2.0.0-20200131.102728-2',
                '2.0.0',
                '3.0.0',
                '3.1.0',
            ]

        """
        versions = sorted(versions)
        # Now we have to move SNAPSHOT before the stable releases
        sorted_versions = []
        n = 0
        while n < len(versions):
            v = versions[n].split('-')
            # Non snapshot version
            if len(v) == 1:
                # Make sure we include the last entry of the list
                if n + 1 == len(versions):
                    sorted_versions.append('-'.join(v))
                # Check if the following up entries are SNAPSHOTs
                # that needs to be shifted to the front
                while n + 1 < len(versions):
                    v_next = versions[n + 1].split('-')
                    if len(v_next) == 1 or v_next[0] != v[0]:
                        sorted_versions.append('-'.join(v))
                        break
                    else:
                        sorted_versions.append('-'.join(v_next))
                        n = n + 1
                        # Again make sure we handle the end of the list
                        if n + 1 == len(versions):
                            sorted_versions.append('-'.join(v))
            # Snapshot version
            else:
                sorted_versions.append(versions[n])
            n = n + 1
        return sorted_versions

    if pattern is None:
        pattern = '*'
    if not pattern.endswith('-SNAPSHOT') and '*' not in pattern:
        raise ValueError(
            'version pattern {} not valid. '
            'It has to end with \'-SNAPSHOT\' or inlcude \'*\'.'
            .format(pattern)
        )
    query_pattern = 'versions?g={}&a={}&v={}'.format(group_id, name, pattern)
    r = rest_api_request(query_pattern)
    if r.status_code != 200:
        raise RuntimeError(
            'Error trying to get versions for:\n'
            '\n'
            '  group_id: {}\n'
            '      name: {}\n'
            '\n'
            'The reason could be that you '
            'don\'t have access rights for the specified '
            'artifact, used the wrong group_id, '
            'or misspelled the artifact.'
            .format(group_id, name)
        )
    versions = [v['version'] for v in r.json()['results']]
    if not versions:
        raise RuntimeError(
            'No version found for:\n'
            '\n'
            '  group_id: {}\n'
            '      name: {}\n'
            '   pattern: {}\n'
            .format(group_id, name, pattern)
        )
    return sort_versions(versions)


def _download_artifacts(
        download_items: List,
        chunk: int,
        verbose: bool
):
    r"""Helper function called by download_artifacts"""

    if not download_items:
        return

    total_download_size = sum([src_size for _, _, src_size in download_items])
    with audeer.progress_bar(
            total=total_download_size,
            disable=not verbose,
    ) as pbar:
        for dst_path, src_path, src_size in download_items:
            audeer.mkdir(os.path.dirname(dst_path))
            dst_size = 0

            desc = audeer.format_display_message(
                'Download {}'.format(os.path.basename(str(src_path))),
                pbar=True,
            )
            pbar.set_description_str(desc)
            pbar.refresh()

            try:
                with src_path.open() as src_fp:
                    with open(dst_path, 'wb') as dst_fp:
                        while src_size > dst_size:
                            data = src_fp.read(chunk)
                            n_data = len(data)
                            if n_data > 0:
                                dst_fp.write(data)
                                dst_size += n_data
                                pbar.update(n_data)
            except (KeyboardInterrupt, Exception):
                # Clean up broken artifact files
                if os.path.exists(dst_path):
                    os.remove(dst_path)
                raise
