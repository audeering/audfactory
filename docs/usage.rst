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

    export ARTIFACTORY_USERNAME="MY_USERNAME"
    export ARTIFACTORY_API_KEY="MY_API_KEY"


Quickstart
----------

To use a database (e.g. emodb_) in your project do:

.. code-block:: python

    >>> import audb
    >>> db = audb.load('emodb')  # load database
    >>> db['emotion'].get()  # access annotations
                       emotion speaker sentence
    file
    wav/03a01Fa.wav  happiness       3      a01
    wav/03a01Nc.wav    neutral       3      a01
    wav/03a01Wa.wav      anger       3      a01
    ...
    >>> audb.exists('emodb')  # get root of database
    /home/user/audb/emodb/1
    >>> audb.remove('emodb')  # remove database

Note that when you request a database for the first time,
the following steps will be executed:

1. Annotations and audio files are loaded from Artifactory to
   ``<cache_root>/.archive``.

2. Annotations and data are unpacked and converted to
   ``<cache_root>/1/<name>``.

.. _emodb:
    https://gitlab.audeering.com/data/emodb


Data conversion
---------------

When loading a database, audio files can be automatically converted.
This creates a new *flavor* of the database.
The following properties can be changed:

.. code-block::

    File format: ['wav', 'flac']
    Sampling rate: [8000, 16000, 2250, 44100, 48000]
    Remix strategy: ['mono', 'left', 'right', 'stereo']

Example:

.. code-block:: python

    >>> db = audb.load('emodb', format='flac', mix='stereo')
    >>> audb.exists('emodb', format='flac', mix='stereo')
    /home/user/audb/emodb/2

This will convert the original files to FLAC
with a sampling rate of 44100 Hz.
For each flavor a sub-folder will be created (here ``2``).
The new audio format is added to the header of the converted database:

.. code-block:: yaml

    emodb:
      ...
      media:
        microphone: {type: audio, format: wav, sampling_rate: 16000, channels: 1}
        audb: {type: audio, format: flac, channels: 2, mix: stereo}
      ...


Metadata only
-------------

It is also possible to request only the metadata of a database.
In that case audio files are not loaded:

.. code-block:: python

    >>> db = audb.load('emodb', only_metadata=True)


Cache root
----------

``cache_root`` points to the local folder where the databases are stored.
By default, is set to ``~/audb``.

There are two ways to overwrite this location:

1. Explicitly, by setting the argument ``cache_root``
   during a call to :func:`audb.load`, e.g:

.. code-block:: python

  >>> db = audb.load('emodb', cache_root='/my/cache')

2. Implicitly, through the system variables ``AUDB_CACHE_ROOT``, e.g.:

.. code-block::

    export AUDB_CACHE_ROOT=/my/audb

Note that 1. overwrites 2.
