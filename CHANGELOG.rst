Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_,
and this project adheres to `Semantic Versioning`_.


Version 1.0.3 (2021-03-29)
--------------------------

* Fixed: ``audfactory.versions()`` for missing permissions


Version 1.0.2 (2021-03-26)
--------------------------

* Fixed: link "Edit on Github"


Version 1.0.1 (2021-03-26)
--------------------------

* Fixed: Python package metadata


Version 1.0.0 (2021-03-26)
--------------------------

* Added: support for anonymous Artifactory user access
* Changed: renamed ``audfactory.artifactory_path()`` to ``audfactory.path()``
* Changed: renamed ``audfactory.deploy_artifact()`` to
  ``audfactory.depoy()``
* Changed: renamed ``audfactory.download_artifact()`` to
  ``audfactory.download()``
* Changed: renamed ``audfactory.server_url()`` to ``audfactory.url()``
* Removed: ``audfactory.upload_artifact()``
* Removed: ``audfactory.sort_versions()``
* Removed: ``audfactory.dependencies()``
* Removed: ``audfactory.download_pom()``
* Removed: ``audfactory.exclude_dependencies()``
* Removed: ``audfactory.include_dependencies()``
* Removed: ``audfactory.list_artifacts()``
* Removed: ``audfactory.server_pom_url()``
* Removed: ``audfactory.transitive_dependencies()``
* Removed: ``audfactory.transitive_dependencies_as_string()``
* Removed: ``audfactory.pom``


Version 0.8.1 (2021-02-09)
--------------------------

* Fixed: use ``audeer.sort_versions()`` in ``audfactory.versions()``


Version 0.8.0 (2021-02-09)
--------------------------

* Deprecated: ``audfactory.sort_versions()``
* Deprecated: ``audfactory.dependencies()``
* Deprecated: ``audfactory.download_pom()``
* Deprecated: ``audfactory.exclude_dependencies()``
* Deprecated: ``audfactory.include_dependencies()``
* Deprecated: ``audfactory.list_artifacts()``
* Deprecated: ``audfactory.server_pom_url()``
* Deprecated: ``audfactory.transitive_dependencies()``
* Deprecated: ``audfactory.transitive_dependencies_as_string()``
* Deprecated: ``audfactory.pom`` module


Version 0.7.2 (2021-01-27)
--------------------------

* Fixed: copyright year in documentation


Version 0.7.1 (2021-01-27)
--------------------------

* Fixed: sorting of versions for, e.g. ``'10.0.0'`` > ``'9.0.0'``


Version 0.7.0 (2021-01-12)
--------------------------

* Added: ``audfactory.checksum()``
* Added: ``audfactory.deploy_artifact()``
* Added: ``md5``, ``sha1``, ``sha256``, ``parameters`` arguments
  to ``audfactory.upload_artifact()``


Version 0.6.3 (2020-10-01)
--------------------------

* Added: official support for Windows


Version 0.6.2 (2020-09-14)
--------------------------

* Added: extend documentation examples of ``audfactory.Lookup``


Version 0.6.1 (2020-09-10)
--------------------------

* Fixed: added documentation for ``audfactory.Lookup.__getitem__()``


Version 0.6.0 (2020-09-09)
--------------------------

* Added: static method ``audfactory.Lookup.generate_uid()``
  to generate UID by hashing a string
* Fixed: add documentation of attributes for ``audfactory.Lookup``


Version 0.5.9 (2020-09-08)
--------------------------

* Added: link to HTML documentation to ``setup.cfg``
* Added: cleanup after tests on Artifactory


Version 0.5.8 (2020-06-22)
--------------------------

* Fixed: repository argument of ``audfactory.list_artifacts()``
  was ignored before


Version 0.5.7 (2020-06-22)
--------------------------

* Added: documentation on how to convert ``audfactory.Lookup``
  to a ``pandas.Dataframe``
* Fixed: list string parameters that are not allowed to use as params
  in ``audfactory.Lookup``


Version 0.5.6 (2020-06-10)
--------------------------

* Added: ``audfactory.Lookup.columns``
* Added: ``audfactory.Lookup.ids``
* Added: nice ``repr`` and ``str`` output for ``audfactory.Lookup``
* Fixed: check for correct type of lookup parameters
  to avoid storing the same parameter twice in a lookup table


Version 0.5.5 (2020-06-06)
--------------------------

* Fixed: clear print line without new line


Version 0.5.4 (2020-06-05)
--------------------------

* Fixed: print line was not cleared at the end of
  ``audfactory.upload_artifact()``
  and ``audfactory.transitive_dependencies()``


Version 0.5.3 (2020-06-02)
--------------------------

* Changed: error message handling in ``audb.download_artifact()``
  is now handled inside ``dohq-artifactory``
* Fixed: broken ``jwt`` dependency due to bug in ``dohq-artifactory``


Version 0.5.2 (2020-05-25)
--------------------------

* Fixed: description of ``params`` argument of ``audfactory.Lookup.create()``
  in the documentation


Version 0.5.1 (2020-05-20)
--------------------------

* Added: ``audfactory.Lookup``


Version 0.5.0 (2020-05-19)
--------------------------

* Added: error messages to ``audb.download_artifact()``
* Added: error handling to ``audfactory.download_pom()``
* Changed: replace ``re.match()`` by ``re.search()`` inside
  ``audfactory.exclude_dependencies()``
  and ``audfactory.include_dependencies()``
* Changed: ``audfactory.versions()`` now returns empty list if no versions
  are found
* Fixed: parallel execution of tests
* Removed: deprecated ``audfactory.rest_api_request()``


Version 0.4.2 (2020-05-11)
--------------------------

* Changed: raise error if Artfactory config cannot be found for
  authentication


Version 0.4.1 (2020-04-22)
--------------------------

* Added: ``audfactory.path_to_group_id()``


Version 0.4.0 (2020-04-01)
--------------------------

* Added: test coverage
* Added: ``audfactory.rest_api_get()``
* Added: ``audfactory.`rest_api_search()``
* Added: ``audfactory.authentification()``
* Deprecated: ``audfactory.rest_api_request()``
* Removed: ``audfactory.download_artifacts()``


Version 0.3.2 (2020-03-06)
--------------------------

* Fixed: ``audfactory.pom.license()`` now doesn't fail for empty license
  entries


Version 0.3.1 (2020-02-14)
--------------------------

* Changed: improve progress bars for downloads


Version 0.3.0 (2020-02-14)
--------------------------

* Added: Python 3.8 support
* Added: ``audfactory.upload_artifact()``
* Added: ``audfactory.download_artifact()``
* Changed: add ``repository`` as optional argument instead config value
* Deprecated: ``audfactory.download_artifacts()``
* Removed: Python 3.5 support


Version 0.2.0 (2020-02-07)
--------------------------

* Added: ``audfactory.sort_versions()``


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
