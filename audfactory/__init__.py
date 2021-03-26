from audfactory.core.api import (
    authentification,
    checksum,
    deploy,
    download,
    group_id_to_path,
    path,
    path_to_group_id,
    rest_api_get,
    url,
    versions,
)
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
