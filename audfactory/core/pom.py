from typing import Dict

from audfactory.core.api import download_pom


def description(pom: Dict) -> str:
    """Description of artifact.

    Args:
        pom: POM of artifact

    Returns:
        description of artifact

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> description(pom)[:56]
        'TIMIT contains read speech for acoustic-phonetic studies'

    """
    return get_attr(pom, 'description')


def get_attr(pom: Dict, attribute: str) -> str:
    """Return POM attribute or empty string.

    Args:
        pom: POM of artifact
        attribute: dictionary key under ``pom['project']``

    Returns:
        requested attribute of artifact

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> get_attr(pom, '@xmlns')
        'http://maven.apache.org/POM/4.0.0'

    """
    try:
        attr = pom['project'][attribute]
    except (KeyError, TypeError):
        try:
            attr = pom[attribute]
        except (KeyError, TypeError):
            attr = ''
    return attr


def group_id(pom: Dict) -> str:
    """Group ID of artifact.

    Args:
        pom: POM of artifact

    Returns:
        group ID of artifact

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> group_id(pom)
        'com.audeering.data.timit'

    """
    return get_attr(pom, 'groupId')


def license(pom: Dict) -> str:
    """License name and if given license URL of artifact.

    Args:
        pom: POM of artifact

    Returns:
        license of artifact

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> name, url = license(pom)[:-1].split(' <')
        >>> name
        'LDC User Agreement for Non-Members'
        >>> url
        'https://catalog.ldc.upenn.edu/license/ldc-non-members-agreement.pdf'

    """
    license = ''
    licenses = get_attr(pom, 'licenses')
    if licenses:
        if 'name' in licenses['license']:
            license += licenses['license']['name']
        if 'url' in licenses['license']:
            if licenses['license']['url']:
                license += f" <{licenses['license']['url']}>"
    return license


def maintainer(pom: Dict) -> str:
    """Maintainer of artifact.

    Args:
        pom: POM of artifact

    Returns:
        maintainer of artifact

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> maintainer(pom)
        ''

    """
    return get_attr(pom, 'maintainer')


def name(pom: Dict) -> str:
    """Name of artifact.

    Args:
        pom: POM of artifact

    Returns:
        name of artifact

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> name(pom)
        'timit'

    """
    return get_attr(pom, 'artifactId')


def type(pom: Dict) -> str:
    """File type of artifact.

    Args:
        pom: POM of artifact

    Returns:
        file type of artifact

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> type(pom)
        'pom'

    """
    return get_attr(pom, 'packaging')


def url(pom: Dict) -> str:
    """URL of artifact.

    Args:
        pom: POM of artifact

    Returns:
        URL entry of artifact

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> url(pom)
        'http://gitlab2.audeering.local/data/timit'

    """
    return get_attr(pom, 'url')


def version(pom: Dict) -> str:
    """Version of artifact.

    Args:
        pom: POM of artifact

    Returns:
        version of artifact

    Example:
        >>> pom = download_pom(
        ...     'https://artifactory.audeering.com/artifactory/maven/'
        ...     'com/audeering/data/timit/timit/1.0.1/timit-1.0.1.pom'
        ... )
        >>> version(pom)
        '1.0.1'

    """
    return get_attr(pom, 'version')
