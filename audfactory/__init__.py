from audfactory import pom
from audfactory.core.api import (
    artifactory_path,
    authentification,
    checksum,
    dependencies,
    deploy_artifact,
    download_artifact,
    download_pom,
    exclude_dependencies,
    group_id_to_path,
    include_dependencies,
    list_artifacts,
    path_to_group_id,
    rest_api_get,
    rest_api_search,
    server_pom_url,
    server_url,
    sort_versions,
    transitive_dependencies,
    transitive_dependencies_as_string,
    upload_artifact,
    versions,
)
from audfactory.core.config import config
from audfactory.core.lookup import Lookup


# Disencourage from audfactory import *
__all__ = []


# Dynamically get the version of the installed module
try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception:  # pragma: no cover
    pkg_resources = None  # pragma: no cover
finally:
    del pkg_resources
