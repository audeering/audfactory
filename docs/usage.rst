Usage
=====


Authentication
--------------

Users have to create a file :file:`~/.artifactory_python.cfg`:

.. code-block:: cfg

    [artifactory.audeering.com/artifactory]
    username = MY_USERNAME
    password = MY_API_KEY

Alternatively, they can provide them as environment variables:

.. code-block:: bash

    $ export ARTIFACTORY_USERNAME="MY_USERNAME"
    $ export ARTIFACTORY_API_KEY="MY_API_KEY"


Artifactory
-----------

Artifacts are stored under the following name space on Artifactory:

* ``group_id``: group ID of an artifact, e.g. ``'com.audeering.data.timit'``
* ``name``: name of an artifact, e.g. ``'timit'``
* ``version``: version of an artifact, e.g. ``1.0.1``

Those three parts are arguments to most of the functions
inside :mod:`audfactory`.
They are also used in a slightly modified way to specify dependencies:

* ``group_id:name:version``, e.g. ``'com.audeering.data.timit:timit:1.0.1'``

Dependencies are arguments or return arguments of some functions as well.

For every artifact a POM file is stored on Artifactory as well.
It contains metadata and dependency information.


Examples
--------

You can query the available versions of an artifact:

.. literalinclude:: examples/versions.py

.. literalinclude:: examples/output/versions.txt

You can get a dictionary containing the `transitive dependencies`_
of an artifact:

.. literalinclude:: examples/get-deps.py

.. literalinclude:: examples/output/get-deps.txt

You can print the transitive dependencies as a nice dependency graph:

.. literalinclude:: examples/print-deps.py

.. literalinclude:: examples/output/print-deps.txt

Or you can get a list of all the artifacts included
in the dependency tree:

.. literalinclude:: examples/list-artifacts.py

.. literalinclude:: examples/output/list-artifacts.txt


.. _transitive dependencies:
    https://docs.gradle.org/current/userguide/dependency_management_terminology.html#sub:terminology_transitive_dependency
