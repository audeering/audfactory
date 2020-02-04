class config:
    """Get/set defaults for the :mod:`audfactory` module.

    For example, when you want to limit the repository
    to public database releases::

        import audfactory
        audfactory.config.ARTIFACTORY_REPO = 'data-public-release-local'

    """

    ARTIFACTORY_ROOT = (
        'https://artifactory.audeering.com/artifactory'
    )
    """Artifactory URL"""

    ARTIFACTORY_REPO = (
        'maven'
    )
    """Artifactory repository"""
