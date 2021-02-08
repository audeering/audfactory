from distutils.version import LooseVersion
import json
import os
import re
import errno
from typing import Dict, List, Union, Tuple
import xml

from artifactory import (
    ArtifactoryPath,
    get_global_config_entry,
    md5sum,
    sha1sum,
    sha256sum,
)
import audeer
import requests
import tqdm
import xmltodict

from audfactory.core import pom as _pom
from audfactory.core.config import config


REPORT_ISSUE = (
    'Please report the issue by clicking on the following link\n'
    'https://gitlab.audeering.com/tools/audfactory/-/issues/'
    'new?issue%5Bassignee_id%5D=&issue%5Bmilestone_id%5D='
)


def artifactory_path(
        url: str,
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
    username, apikey = authentification()
    return ArtifactoryPath(url, auth=(username, apikey))


def authentification() -> Tuple[str, str]:
    """Look for username and API key.

    It first looks for the two environment variables
    ``ARTIFACTORY_USERNAME`` and
    ``ARTIFACTORY_API_KEY``.
    If some of them or both are missing,
    it tries to extract them from the
    :file:`~/.artifactory_python.cfg` config file.

    Returns:
        username and API key

    Raises:
        RuntimeError: if no authentification credentials can be find

    """
    username = os.getenv('ARTIFACTORY_USERNAME', None)
    apikey = os.getenv('ARTIFACTORY_API_KEY', None)
    if apikey is None or username is None:  # pragma: no cover
        config_entry = get_global_config_entry(config.ARTIFACTORY_ROOT)
        if config_entry is None:
            raise RuntimeError(
                'No Artifactory credentials found.\n'
                'Please check you have a ~/.artifactory_python.cfg '
                'file containing:\n'
                '[artifactory.audeering.com/artifactory]\n'
                'username = MY_USERNAME\n'
                'password = MY_API_KEY'
            )
        username = config_entry['username']
        apikey = config_entry['password']
    return username, apikey


def checksum(path, type='md5') -> str:
    r"""Calculate checksum for local or remote file.

    Args:
        path: local file path,
            or URL to file path on Artifactory
        type: checksum type to calculate,
            one of ``'md5'``, ``'sha1'``, ``'sha256'``

    Returns:
        checksum

    Example:
        >>> checksum(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'edu/upenn/ldc/timit/1.0.1/timit-1.0.1.pom'
        ... )
        '9f0c246e1b3ab736c28bbe0f00caf277'

    """
    if path.startswith('http'):
        path = artifactory_path(path)
        if not path.exists():
            raise RuntimeError(f'File not found: {path}')
        if type == 'md5':
            return ArtifactoryPath.stat(path).md5
        elif type == 'sha1':
            return ArtifactoryPath.stat(path).sha1
        elif type == 'sha256':
            return ArtifactoryPath.stat(path).sha256
    else:
        path = audeer.safe_path(path)
        if not os.path.exists(path):
            raise RuntimeError(f'File not found: {path}')
        if type == 'md5':
            return md5sum(path)
        elif type == 'sha1':
            return sha1sum(path)
        elif type == 'sha256':
            return sha256sum(path)


@audeer.deprecated(removal_version='1.0.0')
def dependencies(
        pom: Dict,
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
        return f'{_pom.group_id(d)}:{_pom.name(d)}:{_pom.version(d)}'

    return sorted([dict_to_string(d) for d in deps])


def deploy_artifact(
        path: str,
        url: str,
        *,
        md5: str = None,
        sha1: str = None,
        sha256: str = None,
        parameters: Dict = {},
        verbose: bool = False,
) -> str:
    r"""Deploy local file as an artifact.

    This works similar to :func:`audfactory.upload_artifact`,
    but allows for providing an URL
    and using a filename that differs from
    {name}-{version}.{extension}.

    If your URL ends different from {name}-{version}.{extension},
    :func:`audfactory.versions` will not list the file
    as it does not follow the Maven repository conventions.

    Args:
        path: local file path (must exist)
        url: path on Artifactory
        md5: MD5 sum, will be calculated if not provided
        sha1: SHA1 hash, will be calculated if not provided
        sha256: SHA256 hash, will be calculated if not provided
        parameters: attach any additional metadata
        verbose: show information on the upload process

    Returns:
        URL of the artifact

    Raises:
        FileNotFoundError: if local file does not exist

    """
    src_path = audeer.safe_path(path)
    if not os.path.exists(src_path):
        raise FileNotFoundError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            src_path,
        )

    if verbose:  # pragma: no cover
        desc = audeer.format_display_message(
            f'Deploy {src_path}',
            pbar=False,
        )
        print(desc, end='\r')

    if md5 is None:
        md5 = md5sum(src_path)
    if sha1 is None:
        sha1 = sha1sum(src_path)
    if sha256 is None:
        sha256 = sha256sum(src_path)

    dst_path = artifactory_path(url)
    if not dst_path.parent.exists():
        dst_path.parent.mkdir()
    with open(src_path, "rb") as fobj:
        dst_path.deploy(
            fobj,
            md5=md5,
            sha1=sha1,
            sha256=sha256,
            parameters=parameters,
        )

    if verbose:  # pragma: no cover
        # Final clearing of progress line
        print(audeer.format_display_message(' ', pbar=False), end='\r')

    return url


def download_artifact(
        url: str,
        destination: str = '.',
        *,
        chunk: int = 4 * 1024,
        force_download: bool = True,
        verbose=False,
) -> str:
    r"""Download an artifact.

    Args:
        url: artifact URL
        destination: path to store the artifact,
            can be a folder or a file name
        chunk: amount of data read at once during the download
        force_download: forces the artifact to be downloaded
            even if it exists locally already
        verbose: show information on the download process

    Returns:
        path to local artifact

    Raises:
        RuntimeError: if artifact cannot be found,
            or you don't have access rights to the artifact

    Example:
        >>> file = download_artifact(
        ...     ('https://artifactory.audeering.com/artifactory/maven/'
        ...      'com/audeering/data/audbunittests/audbunittests-data/'
        ...      '4.0.0/audbunittests-data-4.0.0.flac'),
        ...     '.',
        ... )
        >>> os.path.basename(file)
        'audbunittests-data-4.0.0.flac'

    """
    destination = audeer.safe_path(destination)
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(url))
    if os.path.exists(destination) and not force_download:
        return destination

    src_path = artifactory_path(url)
    src_size = ArtifactoryPath.stat(src_path).size

    with audeer.progress_bar(total=src_size, disable=not verbose) as pbar:
        desc = audeer.format_display_message(
            'Download {}'.format(os.path.basename(str(src_path))),
            pbar=True,
        )
        pbar.set_description_str(desc)
        pbar.refresh()

        try:
            dst_size = 0
            with src_path.open() as src_fp:
                with open(destination, 'wb') as dst_fp:
                    while src_size > dst_size:
                        data = src_fp.read(chunk)
                        n_data = len(data)
                        if n_data > 0:
                            dst_fp.write(data)
                            dst_size += n_data
                            pbar.update(n_data)
        except (KeyboardInterrupt, Exception):
            # Clean up broken artifact files
            if os.path.exists(destination):
                os.remove(destination)  # pragma: no cover
            raise

    return destination


@audeer.deprecated(removal_version='1.0.0')
def download_pom(
        pom_url: str,
) -> Dict:
    r"""Retrieves a POM from Artifactory.

    Args:
        pom_url: URL of POM file to download

    Returns:
        parsed POM

    Raises:
        RuntimeError: if POM is not valid,
            URL is not available,
            or user has no access rights

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'edu/upenn/ldc/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> pom['project']['url']
        'https://catalog.ldc.upenn.edu/LDC93S1'

    """
    pom_path = artifactory_path(pom_url)
    try:
        with pom_path.open() as fp:
            pom = xmltodict.parse(fp.read())
    except xml.parsers.expat.ExpatError:
        raise RuntimeError(f"No valid POM. Maybe '{pom_url}' is not a POM?")
    except RuntimeError as e:
        code = str(e)
        if code == '404':  # pragma: no cover as only admins see this
            raise RuntimeError(f"{code}, cannot find '{pom_url}'")
        elif code == '403':
            raise RuntimeError(f"{code}, no access rights for '{pom_url}'")
        else:
            raise RuntimeError(
                f"{code}, problem downloading '{pom_url}'.\n{REPORT_ISSUE}"
            )  # pragma: no cover
    return pom


@audeer.deprecated(removal_version='1.0.0')
def exclude_dependencies(
        deps: Dict,
        pattern: str,
) -> Dict:
    r"""Exclude nodes of a transitive dependency tree.

    Args:
        deps: transitive dependencies
        pattern: regexp filter pattern specifying dependencies to exclude

    Returns:
        filtered transitive dependency tree

    Example:
        >>> deps = {'a': {'b': {'c': {'c1': [], 'c2': []}, 'd': []}}}
        >>> exclude_dependencies(deps, pattern='c')
        {'a': {'b': {'d': []}}}

    """
    filtered_deps = {}
    for key, value in deps.items():
        if re.search(pattern, key):
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
        group_id: str,
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


@audeer.deprecated(removal_version='1.0.0')
def include_dependencies(
        deps: Dict,
        pattern: str,
) -> Dict:
    r"""Include nodes of a transitive dependency tree.

    Args:
        deps: transitive dependencies
        pattern: regexp filter pattern specifying dependencies to include

    Returns:
        filtered transitive dependency tree

    Example:
        >>> deps = {'a': {'b': {'c': {'c1': [], 'c2': []}, 'd': []}}}
        >>> include_dependencies(deps, pattern='d')
        {'a': {'b': {'d': []}}}

    """
    filtered_deps = {}
    for key, value in deps.items():
        if re.search(pattern, key):
            filtered_deps[key] = value
        elif isinstance(value, dict):
            # Recursively traverse the sub-tree
            sub_tree = include_dependencies(value, pattern)
            # Only include sub-tree if not empty
            if sub_tree:
                filtered_deps[key] = sub_tree
        else:
            continue  # pragma: no cover
    return filtered_deps


def list_artifacts(
        deps: Dict,
        *,
        repository: str = 'maven',
) -> List:
    r"""Extract all artifacts from a nested dependency tree.

    Such a dictionary can be created by :func:`transitive_dependencies`.
    It returns a list with the URL of all artifacts.

    Args:
        deps: dependency tree
        repository: repository of dependencies

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
                artifact_urls += list_artifacts(value, repository=repository)
            else:
                group_id, name, version = key.split(':')
                pom_url = server_pom_url(
                    group_id,
                    name,
                    version,
                    repository=repository,
                )
                artifact_urls += [pom_url.replace('.pom', '.' + value)]
    # Ensure unique entries as some packages might have duplicted ones
    return sorted(list(set(artifact_urls)))


def path_to_group_id(
        path: str,
) -> str:
    r"""Replaces ``/`` by ``.`` in group ID.

    Args:
        path: group ID path

    Returns:
        group ID

    Example:
        >>> path_to_group_id('com/audeering/data/emodb')
        'com.audeering.data.emodb'

    """
    return '.'.join(path.split('/'))


def rest_api_get(
        url: str,
) -> requests.models.Response:
    """Execute a GET REST API request.

    For details on the REST API, see
    https://www.jfrog.com/confluence/display/JFROG/Artifactory+REST+API

    Args:
        url: URl to send the request without Artifactory base URL
            as specified in ``config.ARTIFACTORY_ROOT``

    Returns:
        server response

    Example:
        >>> r = rest_api_get('maven/com/audeering/data/emodb/emodb-metadata/'
        ...                  '0.2.2/emodb-metadata-0.2.2.zip!/db.yaml')
        >>> print(r.text[:60])
        name: emodb
        description: Berlin Database of Emotional Speech

    """
    url = f'{config.ARTIFACTORY_ROOT}/{url}'
    username, apikey = authentification()
    return requests.get(url, auth=(username, apikey))


def rest_api_search(
        pattern: str,
        *,
        repository: str = 'maven',
) -> requests.models.Response:
    """Execute a GET REST API query.

    For details on the REST API, see
    https://www.jfrog.com/confluence/display/JFROG/Artifactory+REST+API

    Args:
        pattern: search pattern
        repository: repository to be used for the request

    Returns:
        server response

    Example:
        >>> r = rest_api_search('latestVersion?g=edu.upenn.ldc&a=timit')
        >>> r.text
        '1.0.1'

    """
    url = f'api/search/{pattern}&repos={repository}'
    return rest_api_get(url)


def server_url(
        group_id: str,
        *,
        name: str = None,
        repository: str = 'maven',
        version: str = None,
) -> str:
    r"""Creates Artifactory URL from group_id, name, and version.

    Args:
        group_id: group ID of artifact
        name: name of artifact
        repository: repository of artifact
        version: version of artifact

    Returns:
        URL to artifact location on server

    Example:
        >>> server_url('edu.upenn.ldc')
        'https://artifactory.audeering.com/artifactory/maven/edu/upenn/ldc'

    """
    group_id = group_id_to_path(group_id)
    if name is not None and version is not None:
        url = f'{group_id}/{name}/{version}'
    elif name is not None:
        url = f'{group_id}/{name}'
    else:
        url = group_id
    return f'{config.ARTIFACTORY_ROOT}/{repository}/{url}'


def server_pom_url(
        group_id: str,
        name: str,
        version: str,
        *,
        repository: str = 'maven',
) -> str:
    r"""URL of POM generated from name, group_id, version.

    For snapshot versions you have to provide the exact version,
    e.g. ``'2.0.0-20200131.102728-2'``

    Args:
        group_id: group ID of artifact
        name: name of artifact
        version: version of artifact
        repository: repository of artifact

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
    url = server_url(
        group_id,
        name=name,
        repository=repository,
        version=version_folder,
    )
    return f'{url}/{name}-{version}.pom'


@audeer.deprecated(removal_version='1.0.0', alternative='audeer.sort_versions')
def sort_versions(
        versions: List[str],
) -> List:
    """Sort version and snapshot versions.

    As no Python package provides the desired results,
    we implement the sorting ourselves.

    Args:
        versions: list with versions

    Returns:
        sorted list of version with highest as last entry

    Example:
        >>> vers = [
        ...     '1.0.0',
        ...     '2.0.0',
        ...     '2.0.0-SNAPSHOT',
        ... ]
        >>> sort_versions(vers)
        ['1.0.0', '2.0.0-SNAPSHOT', '2.0.0']

    """
    versions = sorted(versions, key=LooseVersion)
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


def transitive_dependencies(
        pom: Dict,
        *,
        repository: str = 'maven',
        verbose: bool = False,
) -> Dict:
    r"""Extract all transitive dependencies of a POM.

    Each dependency is used as a key of the dictionary
    with further dependencies as values.
    If there are no more transitive dependencies
    the package type of the artifact (e.g. ``'zip'``)
    is stored as the dictionary value.

    Args:
        pom: POM of artifact
        repository: repository of artifact.
            If a dependency is not available in the specified repository,
            :func:`transitive_dependencies` will fail
        verbose: show progress messages

    Returns:
        transitive dependency tree

    Example:
        >>> url = server_pom_url('com.audeering.data.timit', 'timit', '1.0.0')
        >>> pom = download_pom(url)
        >>> transitive_dependencies(pom)
        {'com.audeering.data.timit:timit-data:1.0.0': {'edu.upenn.ldc:timit:1.0.0': 'zip'}, 'com.audeering.data.timit:timit-metadata:1.0.0': 'zip'}

    """  # noqa: E501
    package_type = _pom.type(pom)
    if package_type == 'pom':
        transitive_deps = {}
        deps = dependencies(pom)

        for dep in deps:
            group_id, name, version = dep.split(':')
            pom_url = server_pom_url(
                group_id,
                name,
                version,
                repository=repository,
            )
            if verbose:  # pragma: no cover
                desc = audeer.format_display_message(
                    f'Dependencies: {dep}',
                    pbar=False,
                )
                print(desc, end='\r')
            pom = download_pom(pom_url)
            transitive_deps[dep] = transitive_dependencies(
                pom,
                repository=repository,
                verbose=verbose,
            )

    else:
        transitive_deps = package_type

    if verbose:  # pragma: no cover
        # Final clearing of progress line
        print(audeer.format_display_message(' ', pbar=False), end='\r')

    return transitive_deps


def transitive_dependencies_as_string(
        d: Dict,
        *,
        prefix: str = '',
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
        output += f'{prefix}+-{key}\n'
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
            output = f'{output.rstrip()} ({str(value)})\n'
    return output


def upload_artifact(
        path: str,
        repository: str,
        group_id: str,
        name: str,
        version: str,
        *,
        md5: str = None,
        sha1: str = None,
        sha256: str = None,
        parameters: Dict = {},
        verbose: bool = False,
) -> str:
    r"""Upload local file as an artifact.

    The URL will be composed as follows:

        {repository}/{group_id}/{name}/{version}/{name}-{version}.{extension}

    It will raise an error if filename does not match
    {name}-{version}.{extension}.
    If you need to publish files with a different name,
    use :func:`deploy_artifact` instead.

    Args:
        path: local file path (must exist)
        repository: name of the repository
        group_id: group ID of the artifact
        name: name of the artifact
        version: version string
        md5: MD5 sum, will be calculated if not provided
        sha1: SHA1 hash, will be calculated if not provided
        sha256: SHA256 hash, will be calculated if not provided
        parameters: attach any additional metadata
        verbose: show information on the upload process

    Returns:
        URL of the artifact

    Raises:
        FileNotFoundError: if local file does not exist
        ValueError: if filename does not match {name}-{version}.{extension}

    """
    src_filename = os.path.basename(path)
    if not src_filename.startswith(f'{name}-{version}.'):
        raise ValueError(
            f"Invalid filename '{src_filename}', expected "
            f"'{name}-{version}.<extension>'"
        )
    url = server_url(
        group_id,
        repository=repository,
        name=name,
        version=version,
    )
    url = f'{url}/{src_filename}'
    return deploy_artifact(
        path,
        url,
        md5=md5,
        sha1=sha1,
        sha256=sha256,
        parameters=parameters,
        verbose=verbose,
    )


def versions(
        group_id: str,
        name: str,
        *,
        pattern: str = None,
        repository: str = 'maven',
) -> List:
    r"""Versions of an artifact on Artifactory.

    It considers stable and snapshot releases.

    Args:
        name: name of artifact
        group_id: group ID of artifact
        pattern: limit versions to specified pattern.
            Could be ``'1.*'``
            or a snapshot like ``'1.1.1-SNAPSHOT'``
        repository: repository of artifact

    Returns:
        versions of artifact on Artifactory

    Raises:
        RuntimeError: if versions cannot be determined
        ValueError: if wrong version pattern is provided

    Example:
        >>> versions('edu.upenn.ldc', 'timit')
        ['1.0.0', '1.0.1']

    """

    if pattern is None:
        pattern = '*'
    if not pattern.endswith('-SNAPSHOT') and '*' not in pattern:
        raise ValueError(
            f'version pattern {pattern} not valid. '
            f'It has to end with \'-SNAPSHOT\' or inlcude \'*\'.'
        )
    query_pattern = f'versions?g={group_id}&a={name}&v={pattern}'
    r = rest_api_search(query_pattern, repository=repository)
    if r.status_code == 404:
        return []
    elif r.status_code != 200:  # pragma: no cover (should never happen)
        raise RuntimeError(
            f'Error trying to get versions for:\n'
            f'\n'
            f'repository: {repository}\n'
            f'  group_id: {group_id}\n'
            f'      name: {name}\n'
            f'\n'
            f'{REPORT_ISSUE}'
        )
    versions = [v['version'] for v in r.json()['results']]
    return sort_versions(versions)
