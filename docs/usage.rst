Usage
=====


Authentication
--------------

To access an Artifactory server,
store your username and `API key`_ in :file:`~/.artifactory_python.cfg`

.. code-block:: cfg

    [artifactory.audeering.com/artifactory]
    username = MY_USERNAME
    password = MY_API_KEY

and replace ``artifactory.audeering.com/artifactory``
with your Artifactory server address.
You can add several server entries.

Alternatively, export the credentials as environment variables:

.. code-block:: bash

    export ARTIFACTORY_USERNAME="MY_USERNAME"
    export ARTIFACTORY_API_KEY="MY_API_KEY"

The environment variables will be applied to all servers,
which means you need to have the same username and API key
on every server.
You might lose access to artifacts on servers
that are setup for anonymous access
as it will always try to authenticate
with the given username and password.
In this case
it is recommended to not use the environment variables.


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
