class config:
    """Get/set defaults for the :mod:`audfactory` module.

    For example, when you want to limit the repository
    to public database releases::

        import audfactory
        audfactory.config.ARTIFACTORY_URL = 'https://artf.audeering.com/artf'

    """

    ARTIFACTORY_ROOT = (
        'https://artifactory.audeering.com/artifactory'
    )
    """Artifactory URL"""
