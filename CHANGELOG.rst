Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_,
and this project adheres to `Semantic Versioning`_.


Version 0.4.0 (2020-04-01)
--------------------------

* Added: test coverage
* Added: :func:`audfactory.rest_api_get`
* Added: :func:`rest_api_search`
* Added: :func:`audfactory.authentification`
* Deprecated: :func:`rest_api_request`
* Removed: :func:`audfactory.download_artifacts`


Version 0.3.2 (2020-03-06)
--------------------------

* Fixed: :func:`audfactory.pom.license` now doesn't fail for empty license
  entries


Version 0.3.1 (2020-02-14)
--------------------------

* Changed: improve progress bars for downloads


Version 0.3.0 (2020-02-14)
--------------------------

* Added: Python 3.8 support
* Added: :func:`audfactory.upload_artifact`
* Added: :func:`audfactory.download_artifact`
* Changed: add ``repository`` as optional argument instead config value
* Deprecated: :func:`audfactory.download_artifacts`
* Removed: Python 3.5 support


Version 0.2.0 (2020-02-07)
--------------------------

* Added: :func:`audfactory.sort_versions`


Version 0.1.2 (2020-02-07)
--------------------------

* Changed: add more examples to documentation
* Fixed: typos in documentation


Version 0.1.1 (2020-02-07)
--------------------------

* Changed: improve documentation


Version 0.1.0 (2020-02-06)
--------------------------

* Added: initial release


.. _Keep a Changelog:
    https://keepachangelog.com/en/1.0.0/
.. _Semantic Versioning:
    https://semver.org/spec/v2.0.0.html
