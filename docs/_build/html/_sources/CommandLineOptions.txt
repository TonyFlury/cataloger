Command Line Options
====================

The full command with options is :

.. code-block:: bash

    manifest [-h] [-v, --verbose {0,1,2,3}]
                    [-r,--root ROOT]
                    [-o,--out REPORT-OUT]
                    [-a,--hash {sha224,md5,sha1,sha256,sha384,sha512}]
                    [-o, --out REPORT-OUT]
                    [-f,--manifest MANIFEST]
                    [-E, --resetExtensions] [-e EXTENSION]
                    [-D, --resetDirectories] [-d DIRECTORY]
                    [-t/-T]
                    [-k/-K]

            create

            check   [-m/-M ]
                    [-i/-I ]
                    [-e/-E ]
                    [-g/-G ]
                    [-s, --summary]

.. code-block:: bash

    General options for all commands

    -h, --help :            Show the full help page

    -v, --verbose :         The verbose reporting level from 0 or 1. The default is 1.
                            Level 0 : No output, except execution error messages.
                            Level 1 : Full output.

    -a, --hash HASH         Choose an alternative hash algorithm. Can be one of
                            sha224, md5, sha1, sha256, sha384, sha512 - the default is sha224.
                            On a standard default installation the above algorithms will be
                            available. Some packages - such as OpenSSL will make more
                            algorithms available - check the help page of the manifest suite
                            on your installation to check what is available locally.

    -f,--manifest MANIFEST  The Manifest file to create or to check against
                            This option will create or use the manifest file with the specified
                            name, rather than the default ``manifest.txt``

    -r, --root ROOT         The root directory to create the manifest from, or check the manifest against.

    -E,--clearExtensions    Clears the internal list of file extensions.
                            Using this option without at least one corresponding
                            ``-e EXTENSION`` option will mean that no files will be
                            included in the manifest.

    -e EXTENSION :          Add a file extension to the internal list.
                            The EXTENSION must start with a dot ``.`` character otherwise
                            an error will be raised.

    -D, --clearDirectories  Clears the internal list of ignored Directories.
                            Using this option without at least on corresponding
                            ``-d DIRECTORY`` option will mean that all top level directories
                            will be included in the manifest.

    -d DIRECTORY :          Add a directory to the internal list of ignored top level directories.
                            It is not an error if the name given does not exist

    Output Flags
        -t/-T               Acts as a flag to enable or disable counting and reporting of file extensions.
        -k/-K               Acts as a flag to enable or disable counting and reporting of skipped files.

        For these flags the lowercase option enables the report, and an uppercase option disables the report.


.. code-block:: bash

    General options for the check command - these must occur after the check command.

    Exception reporting flags

        -m/-M                Whether or not to report on mismatched files
        -i/-I                Whether or not to report on missing files
        -x/-X                Whether or not to report on extra files

        For these flags the lowercase option enables the report, and an uppercase option disables the report.
        If a particular exception type is disabled then any occurrence of this type of exception will not be reported
        and the command will not exit with a failure status. By default all of these reports are enabled.

    Other options

        -g/-G               Enables/disables grouping of exception reports files. If grouping is
                            disabled (using -G) then exceptions are reported immediately they are found,


