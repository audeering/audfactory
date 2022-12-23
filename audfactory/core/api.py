import errno
import json
import os
import typing

from artifactory import (
    ArtifactoryPath,
    get_global_config_entry,
    md5sum,
    sha1sum,
    sha256sum,
)
import requests

import audeer


def authentification(url) -> typing.Tuple[str, str]:
    """Look for username and API key.

    It first looks for the two environment variables
    ``ARTIFACTORY_USERNAME`` and
    ``ARTIFACTORY_API_KEY``.

    If some of them or both are missing,
    it tries to extract them from the
    :file:`~/.artifactory_python.cfg` config file.
    For that it removes ``http://`` or ``https://``
    from the beginning of ``url``
    and everything that comes after ``/artifactory``.
    E.g. for ``https://audeering.jfrog.io/artifactory/data-public/emodb``
    it will look for an entry in the config file under
    ``[audeering.jfrog.io/artifactory]``.

    If it cannot find the config file
    or a matching entry in the config file
    it will set the username to ``anonymous``
    and the API key to an empty string.
    If your Artifactory server is configured
    to allow anonymous users
    you will be able to access the server this way.

    Args:
        url: URL of Artifactory server,
            e.g. https://audeering.jfrog.io/artifactory

    Returns:
        username and API key

    """
    username = os.getenv('ARTIFACTORY_USERNAME', None)
    apikey = os.getenv('ARTIFACTORY_API_KEY', None)
    if apikey is None or username is None:  # pragma: no cover
        url = _strip_url(url)
        config_entry = get_global_config_entry(url)
        if config_entry is None:
            username = 'anonymous'
            apikey = ''
        else:
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

    Examples:
        >>> checksum(
        ...     'https://audeering.jfrog.io/artifactory/'
        ...     'data-public/emodb/db/1.1.0/db-1.1.0.zip'
        ... )
        'f4cfdbc821a070e1163d225b72b241a7'

    """
    if path.startswith('http'):
        path = _path(path)
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


def deploy(
        path: str,
        url: str,
        *,
        md5: str = None,
        sha1: str = None,
        sha256: str = None,
        parameters: typing.Dict = {},
        verbose: bool = False,
) -> str:
    r"""Deploy local file as an artifact.

    Args:
        path: local file path
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

    dst_path = _path(url)
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


def download(
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

    Examples:
        >>> file = download(
        ...     (
        ...         'https://audeering.jfrog.io/artifactory/'
        ...         'data-public/emodb/db/1.1.0/db-1.1.0.yaml'
        ...     ),
        ... )
        >>> os.path.basename(file)
        'db-1.1.0.yaml'

    """
    destination = audeer.safe_path(destination)
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(url))
    if os.path.exists(destination) and not force_download:
        return destination

    src_path = _path(url)
    if not src_path.exists():
        raise RuntimeError(f"Source '{url}' does not exists.")
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


def group_id_to_path(
        group_id: str,
) -> str:
    r"""Replaces ``.`` by ``/`` in group ID.

    Args:
        group_id: group ID

    Returns:
        group ID path

    Examples:
        >>> group_id_to_path('com.audeering.data.emodb')
        'com/audeering/data/emodb'

    """
    return '/'.join(group_id.split('.'))


def path(
        url: str,
) -> ArtifactoryPath:
    r"""Authenticate at Artifactory and get path object.

    You can set your username and API key in the console:

    .. code-block:: bash

        $ export ARTIFACTORY_USERNAME=...
        $ export ARTIFACTORY_API_KEY=...

    If they are not specified,
    they are read from :file:`~/.artifactory_python.cfg`
    by matching ``url`` against the available entries
    to pick the matching Artifactory server.

    Args:
        url: URL to path on Artifactory

    Returns:
        Artifactory path object similar to pathlib.Path

    Examples:
        >>> artifactory_path = path(
        ...     'https://audeering.jfrog.io/artifactory/data-public/emodb/'
        ... )
        >>> for content in artifactory_path:
        ...     print(os.path.basename(str(content)))
        ...
        db
        media
        meta

    """
    username, apikey = authentification(url)
    return ArtifactoryPath(url, auth=(username, apikey))


def path_to_group_id(
        path: str,
) -> str:
    r"""Replaces ``/`` by ``.`` in group ID.

    Args:
        path: group ID path

    Returns:
        group ID

    Examples:
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
        url: REST API request URl

    Returns:
        server response

    Examples:
        >>> r = rest_api_get(
        ...     'https://audeering.jfrog.io/artifactory/'
        ...     'data-public/emodb/meta/files/1.1.0/'
        ...     'files-1.1.0.zip!/db.files.csv'
        ... )
        >>> print(r.text[:35])
        file,duration,speaker,transcription

    """
    username, apikey = authentification(url)
    return requests.get(url, auth=(username, apikey))


def url(
        server: str,
        *,
        repository: str = None,
        group_id: str = None,
        name: str = None,
        version: str = None,
) -> str:
    r"""Creates Artifactory URL from group_id, name, and version.

    Args:
        server: URL of Artifactory server,
            e.g. https://audeering.jfrog.io
        repository: repository
        group_id: group ID
        name: name of artifact
        version: version of artifact

    Returns:
        URL to location on server

    Examples:
        >>> url(
        ...     'https://audeering.jfrog.io/artifactory',
        ...     repository='data-public',
        ...     name='emodb',
        ... )
        'https://audeering.jfrog.io/artifactory/data-public/emodb'

    """
    url = server
    if not repository:
        return url

    url += f'/{repository}'
    if group_id:
        group_id = group_id_to_path(group_id)
        url += f'/{group_id}'
    if name:
        url += f'/{name}'
    if version:
        url += f'/{version}'
    return url


def versions(
        server: str,
        repository: str,
        group_id: str,
        name: str,
) -> typing.List:
    r"""Versions of an artifact on Artifactory.

    It lists all folders under the given path
    and considers all as versions that are conform with
    :func:`audeer.is_semantic_version`.

    Args:
        server: URL of Artifactory server,
            e.g. ``'https://audeering.jfrog.io/artifactory'``
        repository: repository of artifact
        group_id: group ID of artifact
        name: name of artifact

    Returns:
        versions of artifact on Artifactory

    """
    artifact_url = url(
        server,
        repository=repository,
        group_id=group_id,
        name=name,
    )
    path = _path(artifact_url)
    try:
        versions = [os.path.basename(str(p)) for p in path if p.is_dir]
        versions = [v for v in versions if audeer.is_semantic_version(v)]
    except (FileNotFoundError, RuntimeError, requests.exceptions.HTTPError):
        versions = []
    return audeer.sort_versions(versions)


# To use avoid path() be hidden by path arguments
_path = path


def _strip_url(url):  # pragma: nocover
    r"""Returns a URL without http(s):// prefixes and ending /"""
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    # Remove everything after "/artifactory" from the end
    url = f"{url.split('/artifactory')[0]}/artifactory"
    return url
