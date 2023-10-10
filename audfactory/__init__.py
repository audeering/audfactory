from audfactory.core.api import authentification
from audfactory.core.api import checksum
from audfactory.core.api import deploy
from audfactory.core.api import download
from audfactory.core.api import group_id_to_path
from audfactory.core.api import path
from audfactory.core.api import path_to_group_id
from audfactory.core.api import rest_api_get
from audfactory.core.api import url
from audfactory.core.api import versions
from audfactory.core.lookup import Lookup


# Disencourage from audfactory import *
__all__ = []


# Dynamically get the version of the installed module
try:
    import importlib.metadata
    __version__ = importlib.metadata.version(__name__)
except Exception:  # pragma: no cover
    importlib = None  # pragma: no cover
finally:
    del importlib
