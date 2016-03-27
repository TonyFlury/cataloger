================
Manifest Checker
================

.. image:: https://readthedocs.org/projects/manifest-checker/badge/?version=latest

:target: http://manifest-checker.readthedocs.org/en/latest/?badge=latest

:alt: Documentation Status

The manifest checker is a suite of easy to use tools which can be used confirm that a directory tree has been correctly copied/deployed.

The checker builds a manifest file, with a checksum against each file. The manifest file is then copied/deployed along with the rest of the directory tree - and the suite can be used to check the destination tree against the manifest.

During the check phase - the suite will report against :

- files which have different checksums in the destination directory tree compared to manifest file - i.e. the files are likely to be different.
- files which are missing from the destination directory tree but which have a checksum within the manifest file - i.e. files which haven't been deployed at all.
- files which exist in the destination tree but which are missing from the manifest file - these extra files may impact the behaviour of the deployed code.

These are called exceptions - and using the right command options you can control which exception result in failures

The manifest checker has :doc:`default options </Defaults>` which are ideal for checking deployment of a Django deployment, but it can be configured either by command line to look in other places, or other file types.

If you use non default configuration options on the command line to create your manifest, then you will need to ensure that you use the same options when you execute the checker against your destination, to ensure that the right files are checked.

.. note::
  Every care is taken to try to ensure that this code comes to you bug free.
  If you do find an error - please report the problem on :

    - `GitHub Issues`_
    - By email to : `Tony Flury`_


.. toctree::
    :maxdepth: 2

    GettingStarted
    CommandLineOptions
    Defaults



.. _Github Issues: https://github.com/TonyFlury/manifest-checker/issues/new
.. _Tony Flury : mailto:anthony.flury?Subject=manifest-checker%20Error
.. _default options: :doc:`Defaults`