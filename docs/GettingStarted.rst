Getting Started
===============

Installation
------------

Manifest checker can be installed using pip :

.. code-block::bash

    pip install cataloger


The cataloger tool and APIs are compatible with both Python 2 (2.7 and later) and Python 3 (3.5 and later)

Simple Usage
------------

Using the cataloger command line tool with the default arguments is easy :

To create the manifest

.. code-block:: bash

    $ cd <tree root>
    $ catalog create

This will create a catalog.cat - detailing all the source code files in the current directory tree, with a sha224 hash created for each file. You can then deploy/copy your source code to the destination and execute

.. code-block:: bash

    $ cd <tree root>
    $ catalog check

By default, the check subcommand rescursively searches the directory tree under the current directory, and computes the hash for each file - and compares that against the computed has in the manifest file.

.. note::
    Make sure you copy/deploy your catalog.cat file along with your source code - if you don't the ``catalog check`` command will fail immediately.

By default the ``catalog check`` will detect and report on three different types of issue :

- missing files : files listed in the manifest file, but which don't exist in the local directory tree.
- record_extra files : files which are not listed in the manifest file, but which exist in the local directory tree.
- incorrect hashes : files where there is a discrepancy between the hash created for the local file, and the hash listed in the manifest.

Further Reading
---------------

 - Complete details of all the command line options : doc:`CommandLine Options`
 - Details of how to write config files : doc:`config`
 - Details of the default options that are applied : doc`Defaults`
 - Detailed use cases of typical usage and suggested configurations : doc:`UseCases`