================
Manifest Checker
================

The manifest checker is a suite of easy to use tools which are intended to be used confirm that a directory tree has been correctly copied/deployed.

The checker builds a manifest file, with a checksum against each file. The manifest file is then then copied/deployed along with the rest of the directory tree - and the destination tree can be checked against the manifest.

By Default the checker will report against :

- files which have different checksums in the destination directory tree
- files which are missing from the destination directory tree
- files which exist in the destination tree but which are missing from the manifest.

The manifest checker has default options which are ideal for checking deployment of a Django deployment, but it can be configured either by the command line, or via a configuration file to look in other places, or other file types, or even specific file names.

If you special configuration options on the command line to create your manifest, then you will need to ensure that you use the same options when you execute the checker against your destination, to ensure that the right files are checked. If you use the configuration file you will need to ensure that the configuration file is copied/deployed for the checker to work correctly.

.. note::
  Every care is taken to try to ensure that this code comes to you bug free.
  If you do find an error - please report the problem on :

    - `GitHub Issues`_
    - By email to : `Tony Flury`_

.. toctree::
    :maxdepth: 2

    GettingStarted
    CommandLineOptions
    ConfigurationFiles
    ExtraInfo

.. _Github Issues: https://github.com/TonyFlury/manifest-checker/issues/new
.. _Tony Flury : mailto:anthony.flury?Subject=manifest-checker%20Error