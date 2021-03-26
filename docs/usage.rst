Usage
=====


Authentication
--------------

Users have to create a config file :file:`~/.artifactory_python.cfg`,
that assigns a username and `API key`_
for every Artifactory server they want to use:

.. code-block:: cfg

    [audeering.jfrog.io/artifactory]
    username = MY_USERNAME
    password = MY_API_KEY

Alternatively, they can provide them as environment variables:

.. code-block:: bash

    $ export ARTIFACTORY_USERNAME="MY_USERNAME"
    $ export ARTIFACTORY_API_KEY="MY_API_KEY"

If you want to use multiple Artifactory users
and environment variables
instead of the config file
you need to have the same username and API key
on every server.

.. _API key: https://www.jfrog.com/confluence/display/JFROG/User+Profile#UserProfile-APIKey


Artifactory
-----------

Artifacts are stored under the following name space on Artifactory:

* ``group_id``: group ID of an artifact, e.g. ``'com.audeering.models'``
* ``name``: name of an artifact, e.g. ``'timit'``
* ``version``: version of an artifact, e.g. ``1.0.1``

Those three parts are arguments to most of the functions
inside :mod:`audfactory`.


Examples
--------

You can query the available versions of an artifact:

.. jupyter-execute::

    import audfactory

    audfactory.versions(
        'https://audeering.jfrog.io/artifactory',
        'data-public',
        'emodb',
        'db',
    )
