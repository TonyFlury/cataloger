=============
Cataloger API
=============

.. default-domain:: py

The cataloger package supports a fully featured programmatic API which allows Python scripts to build catalogs and check the directory structure against a previously built catalog.

.. contents::
    :local:
    :depth: 2

----

Exceptions
----------

.. module:: cataloger.processor

.. exception:: CatalogError

    Raised when there is an error within the catalog file itself (i.e. a formatting issue).

.. exception:: ConfigError

    Raised when there is an error within the :doc:`config file <config>`.

Command Methods
---------------

.. module:: cataloger.commands

.. py:function:: create_catalog( verbose=0, **kwargs )
.. py:function:: check_catalog( verbose=0, **kwargs )

    Using the directory structure, either create a catalog, or compare the directory structure against a cataloge. By default using settings defined in catalog.cfg if it exists. If a setting is defined in the :doc:`config file <config>` it can be overidden by argumensts passed to the function.

    Returns a :class:`Cataloger` instance.

    :param Boolean no_config: True if the config file should be ignored. Defaults to False
    :param str config: The name of the config file to use
        Defaults to ''. Unless a specific config file is provided
        the processor will attempt to read defaults.DEFAULT_CONFIG_FILE as
        the config file.
    :param str catalog: The name of the catalog file to use
            Defaults to catalog.cat
    :param str hash: The name of the hash algorithm to use
            Defaults to sha224
    :param str root: The root directory to start the creation or check process.
            Can be either a absolute or a path relative to the current working directory
            Defaults to '.'
    :param set extensions: The file extensions to catalog.
            Defaults to .py, .html, .txt, .css, .js, .gif, .png, .jpg, .jpeg
    :param set rm_extension: A set of extensiions to remove from catalogue
        No Default
    :param set add_extension: A set of extensiions to add to catalogue
        No Default
    :param set ignore_directory: A set of directories under root which are
        to be ignored and not catalogued
        Defaults to static, htmlcov, media, build, dist, docs
    :param set rm_directory: A set of directories to removed from the
        ignore_directory set.
        No Default
    :param set add_directory: A list/set of directories to be added to the
        ignore_directory set.
        No Default
    :param list include_filter: A glob file matching filter of files to
        catalogue. Default behaviour is that all files which have
        a file extension in the ``extensions`` set are catalogued
    :param list exclude_filter: A glob file matching filter of files to
        exclude from catalogue. Default behaviour is that no files
        which have a file extension in the ``extensions`` set is
        excluded from the catalogue.

    :raise processor.CatalogError: If an error exists within the catalog file itself (or it cannot be read).
    :raise processor.ConfigError: If an error exists within the config file itself.

Config file processing :
------------------------

All of the arguments (and by extension the command line arguments)
are processed after the config file if any.

If the `no_config` flag is True, then all `config` files are ignored
and only the parameters passed to the functions are used.

If `no_config` is False (the default), and `config` is '' or None, then the default config file is used only if it exists, and no error is created if the file doesn't exist.

If `no_config` is False, and `config` is provided (even if it is the default name) then the config file is used if it exists, but a warning is generated if the file doesn't exist - execution continues as if the config file is empty.

Cataloger class
---------------

.. class:: Cataloger

    An instance of the :class:`Cataloger` class is returned by both :func:`create_catalog` and :func:`check_catalog`. The :class:`Cataloger` class is not intended to be instantiated on it's own.

    The :class:`Cataloger` class contains a number of attributes and methods to enable programatic access to the results of the catalog creation or catalog checking tasks.

    .. attribute:: catalog_file_name

            The read only name of the catalog file created or being checked.

    .. attribute:: processed_count

             A read only count of the number files in the catalog.

    .. attribute:: extension_counts

            A read only dictionary of file extensions and the count for each extension.

            - key : file extension (with leading dot)
            - value : A count of the files within the catalog with this extension

    .. attribute:: excluded_files

             A read only list of the paths of all :ref:`excluded files <excluded-files>`. All file paths are relative to the `root` path parameter.

    .. attribute:: mismatched_files

            A read only list of the paths of all :term:`mismatched files <mismatch>`. All file paths are relative to the `root` path parameter.

    .. attribute:: extra_files

            A read only list of the paths of all :term:`extra files <extra>`.All file paths are relative to the `root` path parameter.

    .. attribute:: missing_files

            A read only list of the paths of all :term:`missing files <missing>`. All file paths are relative to the `root` path parameter.

    .. attribute:: catalog_summary_by_directory

            A generator method which yields a dictionary for each directory within the catalog - the dictionary has the following keys :

        - path: The relative path of the directory being reported on
        - processed: The count of all files in the catalog in this directory
        - excluded: The count of all :ref:`excluded files <excluded-files>` from this directory
        - mismatched: The count of the :term:`mismatched files <mismatch>` from this directory. Will always be zero after a :func:`create_catalog` call.
        - missing: The count of the :term:`missing files <missing>` from this directory. Will always be zero after a :func:`create_catalog` call.
        - extra: The count of the :term:`extra files <missing>` from this directory. Will always be zero after a :func:`create_catalog` call.

    .. method:: is_file_in_catalog( file_path )

        True if this file exists in the catalog

    .. method:: is_directory_in_catalog( directory )

        True if this directory exists in the catalog
