Command Line Options
====================

.. contents::
    :local:
    :depth: 2

----

Summary
-------

The full command line options are:

.. code-block:: bash

    manifest [-h] [-v, --verbose {0,1,2,3}]
                    [-r,--root ROOT]
                    [-o,--out REPORT-OUT]
                    [-a,--hash {sha224,md5,sha1,sha256,sha384,sha512 - and possibly more}]
                    [-m,--catalog MANIFEST]
                    [-c, --config CONFIG]
                    [-N, --no_config ]
                    [-e, --rm_extension EXTENSION]
                    [+e, --add_extension EXTENSION]
                    [-d, --rm_directory DIRECTORY]
                    [+d, --add_directory DIRECTORY]
                    [-f, --exclude_filter FILTER]
                    [+f, --include_filter FILTER]
                    [-t/-T]
                    [-k/-K]

            create

            check   [-m/-M ]
                    [-i/-I ]
                    [-e/-E ]
                    [-g/-G ]
                    [-s, --summary]

General options for all commands
--------------------------------

    \-h, --help :
            Show the full help page and exit

    \-v, --verbose :
            The verbose reporting level from 0 or 1. The default is 1.
            Level 0 : No output, except execution error messages.
            Level 1 : Full output.
            Level 2 : Extended output for each directory.

General processing
~~~~~~~~~~~~~~~~~~

    \-a, --hash HASH
            Choose a hash algorithm to be used to create the signature.
            Can at least be one of sha224, md5, sha1, sha256, sha384, sha512
            the default is sha224.
            On a standard default installation at least the above algorithms
            listed will be available, and some packages - such as OpenSSL will
            make more algorithms available - Check the help page of the
            catalog suite on your installation to check what is available
            on your system.
            If you are using the catalog on two different systems ensure that
            you use a hash algorithm which is available on both.

            This option is included for completeness - there is very little
            practical benefit to use anything other than sha224

    \-m, --catalog CATALOG
            The name of the catalog file to create or to check against.
            This option will create or use the catalog file
            with the specified name, rather than the default ``catalog.cat``

    \-c, -config CONFIG
            Specify a config file to use, rather than the default ``catalog.cfg``
            If a config file is specified which does not exist or cannot be opened
            a warning is generated to stderr, and execution continues using
            the :doc:`defaults values <Defaults>` only (modified by any command
            line options).
            If the -c option is not used and the default ``catalog.cfg`` does
            not exist or cannot be opened, then no warning is generated.

    \-N, --no_config
            A flag to suppress reading of the default config file ``catalog.cfg``,
            and use just the :doc:`defaults values <Defaults>` only (modified
            by any command line options).

    \-r, --root ROOT
            The root directory to create the manifest from, or check the
            manifest against.

File Selection
~~~~~~~~~~~~~~

    \-e, --rm_extension EXTENSION
            Remove one or more file extensions from the list of those to be cataloged.
            All the EXTENSION must start with a dot character otherwise an
            error will be raised.

    \+e, --add_extension EXTENSION
            Add one or more file extensions to the list of those to be cataloged.
            All the EXTENSION must start with a dot character otherwise an
            error will be raised.

    \-d, --rm_directory DIRECTORY
            Remove one or more directory from the list of those
            :term:`top level directories <top level directory>` (relative to the root) which are ignored

    \+d, --add_directory DIRECTORY
            Add one or more directory from the list of those
            :term:`top level directories <top level directory>` (relative to the root) which are ignored.

    \-f, --exclude_filter FILTER
            Add one or more glob filters to exclude files from
            being cataloged. If a file matches any of the
            exclude filters then it will not be cataloged or
            checked against the catalog.

    \+f, --include_filter FILTER
            Add one or more glob filters to include files into
            the catalog. If a file matches any of the
            include filters then it will be cataloged and checked

General Output Flags
~~~~~~~~~~~~~~~~~~~~

    \-t/-T
            A flag to enable or disable counting and reporting of file extensions.

    \-l/-L
            A flag to enable or disable counting and reporting of excluded files.
            See :ref:`excluded-files` for more details

For these flags the lowercase option enables the report, and the
uppercase option disables the report.


Check Command options
---------------------

    General options for the check command only -
            If specified these must occur after the `check` command :

    Exception reporting flags

    \-m/-M
            Whether or not to report on mismatched files
            Those files where the file in the directory being checked has a
            different hashed signature compared to the signature recorded in
            catalog for that file

    \-i/-I
            Whether or not to report on missing files
            Those files which exist in the catalog but do not exist within the
            directory structure being checked

     \-x/-X
            Whether or not to report on record_extra files
            Those files which exist within the directory structure being
            checked but do not exist in the catalog

For these flags the lowercase option enables the report, and an
uppercase option disables the report.

If a particular exception type is disabled then no occurrence of this
type of exception will not be reported and the command will not exit
with a failure status. By default all of these reports are enabled.

----

Notes and Other Information
---------------------------

Relationship between System Defaults, Config file and command line options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With the exception of the --help option above all of the command line options
have a system wide Default value and a counterpart option which can be used
within a :doc:`config file<config>`.

When identifying the values to be used for each option the following ordered
process is executed :

  1. The System wide defaults are applied in all cases

  1. Assuming a config file exists (see -c option above) then the values and
     options from the config file are then applied either overridding or modifiying
     the values derived from the System wide defaults

  1. Any options specified from the command line are then applied, further
     overiding or modifying the values generate previously.


.. _FileSelection:

Selection of files to be cataloged
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since there are multiple mechanisms for including and excluding files from the
catalog it is worth exploring the rules in details to avoid confusion.

In strict order :

    - All files within top level directories (as modified using the -d/+d
      options and the [directories] section of the config file) are not cataloged
      regardless of their file extensions

    - Files whose files extension does not match one of the file extension list
      (as modified by -e/+e and the ``[extensions]`` section of the config file) are not
      cataloged.

    - Files which match any specific exclusion filter (the -f option or the
      ``exclude`` option in the config ``[filters]`` section) are not cataloged.

    - Files which do not match any specific included filter (the +f option or the
      ``include`` option in the config ``[filters]`` section) are not cataloged.

All other files are cataloged.



