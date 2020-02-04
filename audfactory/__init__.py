from audfactory import pom
from audfactory.core.config import config
from audfactory.core.api import (
    artifactory_path,
    dependencies,
    download_artifacts,
    download_pom,
    exclude_dependencies,
    group_id_to_path,
    include_dependencies,
    list_artifacts,
    rest_api_request,
    server_pom_url,
    server_url,
    transitive_dependencies,
    transitive_dependencies_as_string,
    versions,
)


# Disencourage from audb import *
__all__ = []


# Dynamically get the version of the installed module
try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception:
    pkg_resources = None
finally:
    del pkg_resources
