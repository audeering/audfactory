from typing import Dict


def description(pom: Dict) -> str:
    """Description of database."""
    return get_attr(pom, 'description')


def get_attr(pom: Dict, attribute: str) -> str:
    """Return POM attribute or empty string."""
    try:
        attr = pom['project'][attribute]
    except (KeyError, TypeError):
        try:
            attr = pom[attribute]
        except (KeyError, TypeError):
            attr = ''
    return attr


def group_id(pom: Dict) -> str:
    """Group ID of database."""
    return get_attr(pom, 'groupId')


def license(pom: Dict) -> str:
    """License name and if given license URL of database."""
    license = ''
    licenses = get_attr(pom, 'licenses')
    if licenses:
        if 'name' in licenses['license']:
            license += licenses['license']['name']
        if 'url' in licenses['license']:
            if licenses['license']['url']:
                license += ' <{}>'.format(licenses['license']['url'])
    return license


def maintainer(pom: Dict) -> str:
    """Maintainer of database."""
    return get_attr(pom, 'maintainer')


def name(pom: Dict) -> str:
    """Name of database."""
    return get_attr(pom, 'artifactId')


def type(pom: Dict) -> str:
    """File type of database."""
    return get_attr(pom, 'packaging')


def url(pom: Dict) -> str:
    """URL of database."""
    return get_attr(pom, 'url')


def version(pom: Dict) -> str:
    """Version of database."""
    return get_attr(pom, 'version')
