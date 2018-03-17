===========================
Cataloger - an Introduction
===========================

.. image:: https://readthedocs.org/projects/manifest-checker/badge/?version=latest
    :target: http://manifest-checker.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

The cataloger is an easy to use tool to create a catalog of the contents of a directory tree, and then later use that same catalog to confirm that contents of the directory tree has been correctly copied/deployed. The catalog contains a hex-string signature created for each selected file within the directory tree, and the tools can identify files which been added, removed or are different (different content) within the directory tree.

Selecting Files
---------------
The tool has a comprehensive set of tools for selecting which files are selected for inclusion in the catalog :

 - selection by file extension
 - de-selection of :term:`top level directories <top level directory>`
 - fine grained inclusion and exclusions of files based on glob pattern matching.

Information about the directory tree (directory and file names) are captured relative to a defined `root` when the catalog is created, which means that the absolute location of the directory tree on the platform is not relevant to the cataloger - what is relevant is the directory structure under the `root`.

For more details see :doc:`CommandLineOptions` and :doc:`config` for more information on how to select files for cataloging.

Reportable Exceptions
---------------------

The identification of additional files, missing files and files with different contents are termed to be :term:`reportable anomalies <reportable anomaly>`; and using command options exist to determine what type of reportable anomaly results are actually reported or are classed as failures; it is entirely possible therefore for the tool to be used in an environment where the additional files are acceptable for instance. See :doc:`Results and Reports <ResultsReports>` for more information.


Defaults, Command lines and Configuration files
-----------------------------------------------
The catalog tool has a set of :doc:`default options <Defaults>` which are ideal for cataloging the deployment of a Django project, since Django projects have the same directory structure when deployed as they have on development (i.e. a hierarchical structure of a Project with multiple apps); but the catalog tool can be used in other environments as well by overriding the defaults file types, ignored directories and other options. See :doc:`Use Case <usecase>` for more information.

If you use non default options to create your catalog, then you will need to ensure that you use the same options when you check your destination directory structure to ensure that the right files are cataloged; this is easily enabled by the use of a configuration file which holds all of the options used to both create and check the catalog; see :doc:`Configuration File <config>` for more information on how to write these configuration files.

APIs
----

Although primarily the catalog tool is provided as a command line tool, the software also includes APIs so that the cataloging functionality can be accessed from other python application. see :doc:`Catalog APIs <apis>` for more information on the two APIs provided.

.. note::
  Every care is taken to try to ensure that this code comes to you bug free.
  If you do find an error - please report the problem on :

    - `GitHub Issues`_
    - By email to : `Tony Flury`_


.. toctree::
    :maxdepth: 2

    GettingStarted
    CommandLineOptions
    ResultsReports
    Defaults
    config
    usecase
    apis
    glossary


.. _Github Issues: https://github.com/TonyFlury/manifest-checker/issues/new
.. _Tony Flury : mailto:anthony.flury?Subject=manifest-checker%20Error
.. _default options: :doc:`Defaults`