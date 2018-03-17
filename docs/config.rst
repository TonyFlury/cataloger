==================
Configuration file
==================

By default the config file is named 'catalog.cfg' and if that file exists the configuration options
there are used before those specified on the command line. The values specified in the config file are
used for both create and check commands; and thus using a config file can be very useful in ensuring
consistency without typing complex command lines.

Sections
========

The config file has a number of sections - none are mandatory - although an empty config file is pointless.

Each section has the following format :

.. code-block:: cfg

    [title]

    <optionline>


Sections can contain one or more `<optionline>`, and the exact form of these option lines depends on the section.

Leading and trailing whitespace on all lines within the section is ignored.

Lines within the config file that begin with a `#` are ignored - and can be used as comments

catalog Section
----------------
.. note::
    This section is equivalent to the `-m/--catalog`, `-h/--hash` and `-r/--root` command line options

This section configures the general options related to creation of the catalog

The format of this section is :

.. code-block:: cfg

    [catalog]

    catalog = <file name>
    hash = <hash name>
    root = <directory path>

where the ``<option>=<value>`` line can be provided for each option - if an option is repeated then the last value given is used. Options can be omitted in 
which case the system default for that option is used.

Available options are :

    catalog
        The name of the catalog file. Equivalent to the ``-m/--manifest`` command line option. If not provided defaults to ``catalog.cat``
    hash
        The name of the hash algorithm to use. The name does not need quotes. Equivalent to the ``-h/--hash`` command line option. Defaults to using sha224 hash.
    root
        The root directory to use - so that all files under the root will be analysed and catalogued. Equivalent to the ``-r/--root`` command line option. This can be either a relative or absolute path (although it makes more sense to be relative) Defaults to '.'

Spaces and tabs around the ``=`` are optional.

.. _extension-section:

Extensions Section
------------------
.. note::
    This section is equivalent to the +e/--add_extension and -e/--rm_extension command line options

This section configures the files extensions which are used when selecting files to be cataloged.

The format of this section is :

.. code-block:: cfg

    [extensions]

    = <new extension list>
    + <additional extension list>
    - <remove extension list>

The section can have one or more of each possible type of option line - and they can appear in any order. These lines are processed in order to 
build an list of file extensions which are to be cataloged or checked.

    = <new extension list>
        Reset the extension list from it's current value to just those items in the ``<new extensions list>``; There is no command line equivalent for this option.
        The extension list can be omitted from this option, in which case the extension list is emptied.
    \+ <additional extension list>
        Add those extensions listed in ``<additional extension list>`` to the extension list to be used; Equivalent to a one or more ``+e`` command line options
    \- <remove extension list>
        Remove the extensions list in the ``<remove extension listt>`` from the extension list to be used; Equivalent to a one or more ``-e`` command line options.

Each of these extension lists are comma separated, with each file extension in the list starting with a ``.`` (a dot).  Spaces and tabs around the individual file extensions are ignored.

Spaces after ``=``, ``+``, and ``-`` are optional

Lines in this section which start with any character other than ``=``, ``+``, ``-`` and ``#`` will be reported as an error.

.. warning::
    Within this section ordering matters. The lines are executed strictly in the order they appear; so for instance :

        - Using the ``+`` and ``-`` operators followed by an ``=`` operator will result in the changes implemented by the ``+`` & ``-`` operators being pointless. An error will not be raised.
        - Having multiple ``=``' operations within the section will result in only the latest one having an effect. An error will not be raised.

Examples
########

Using the + operator
~~~~~~~~~~~~~~~~~~~~

Assuming that the default extension list is ``.py, .html, .txt, .css, .js, .gif, .png, .jpg, .jpeg`` then :

.. code-block:: cfg

    [extensions]

    + .htm, .cfg, jsx

Would result in the extension list of ``.py, .html, .htx, .txt, .css, .cfg, .js, .jsx, .gif, .png, .jpg, .jpeg`` being used for both create and check operations.

.. note::
    It is not an error to use the ``+`` to add an extension that already exists in the current list.

Using the - operator
~~~~~~~~~~~~~~~~~~~~

Assuming that the default extension list is ``.py, .txt, .html, .css, .js, .gif, .png, .jpg, .jpeg`` then :

.. code-block:: cfg

    [extensions]

    - .html, .js, .css

Would result in the extension list of ``.py, .txt, .gif, .png, .jpg, .jpeg`` being used for both create and check operations.

.. note::
    It is not an error to use the ``-`` to attempt to remove an extension that doesn't exist in the current list.

Using the = operator
~~~~~~~~~~~~~~~~~~~~

Assuming that the default extension list is ``.py, .txt, .html, .css, .js, .gif, .png, .jpg, .jpeg`` then :

.. code-block:: cfg

    [extensions]

    = .html, .js, .css

Would result in only files with extensions of ``.html, .js`` and ``.css`` only being used for both create and check operations.


Directories Section
-------------------
.. note::
    This section is equivalent to the -d/--rm_directory and +d/--add_directory command line options

This section configures which :term:`top level directories <top level directory>` are to be excluded from the catalog.

The format of this section is :

.. code-block:: cfg

    [directories]

    = <new directory list>
    + <additional directory list>
    - <remove directory list>

The section can have one or more of each possible type of option line - and they can appear in any order. These lines are processed in order to
build an list of file extensions which are to be cataloged or checked.

    = <new directory list>
        Reset the directory list from it's current value to just those items in the ``<new directory list>``; There is no command line equivalent for this option.
        The directory list can be omitted from this option, in which case the directory list is emptied.
    \+ <additional directory list>
        Add those directory listed in ``<additional directory list>`` to the directory list to be used; Equivalent to a one or more ``+d`` command line options
    \- <remove extension list>
        Remove the directory list in the ``<remove directory listt>`` from the directory list to be used; Equivalent to a one or more ``-d`` command line options.

Each of these directory lists are comma separated, Spaces and tabs around the individual file extensions are ignored.

Spaces after ``=``, ``+``, and ``-`` are optional

Lines in this section which start with any character other than ``=``, ``+``, ``-`` and ``#`` will be reported as an error.

.. warning::
    Within this section ordering matters. The lines are executed strictly in the order they appear; so for instance :

        - Using the ``+`` and ``-`` operators followed by an ``=`` operator will result in the changes implemented by the ``+`` & ``-`` operators being pointless. An error will not be raised.
        - Having multiple ``=``' operations within the section will result in only the latest one having an effect. An error will not be raised.

Examples
########

Using the + operator
~~~~~~~~~~~~~~~~~~~~

Assuming that the default directory list is **static**, **env**, **htmlcov**, **media**, **build**, **dist**, **docs** then :

.. code-block:: cfg

    [extensions]

    + .tox

Would result in the top level directories  **static**, **env**,  **htmlcov**, **media**, **build**, **dist**, **docs** and **.tox** being excluded from the catalog.

.. note::
    It is not an error to use the ``+`` to add an directory that already exists in the current list.

Using the - operator
~~~~~~~~~~~~~~~~~~~~

Assuming that the default extension list is **static**, **env**, **htmlcov**, **media**, **build**, **dist**, **docs** then :

.. code-block:: cfg

    [extensions]

    - media, docs

Would result in the in the :term:`top level directories <top level directory>` **static**, **env**,  **htmlcov**, **build**, **dist**, and **.tox** only being entirely excluded from the catalog, with the contents of the **media** and **docs** directories being cataloged, subject to file extensions and filters

.. note::
    It is not an error to use the ``-`` to attempt to remove an director that doesn't exist in the current list.

Using the = operator
~~~~~~~~~~~~~~~~~~~~

Assuming that the default extension list is **static**, **env**, **htmlcov**, **media**, **build**, **dist**, **docs** then :

.. code-block:: cfg

    [extensions]

    = static, htmlcov

Would result in only files with extensions of **static**, **htmlcov** only being entirely excluded from the catalog, with the content of all other top level directions being cataloged, subject to file extensions and filters.


.. _include-filter:
.. _exclude-filter:

Filter Section
--------------
.. note::
    This section is equivalent to the -f/--exclude_filter and +f/--include_filter command line options


The format of this section is :

.. code-block:: cfg

    [filters]

    include = <glob pattern match list>
    exclude = <glob pattern match list>

The glob pattern match list is used as the full set of glob pattern matches to be used when identifying which specific files are to be cataloged. The normal rules of glob matching applies :

    ? matches any single character - for instance `?ython` will match `Python` as well as `\ython`
    * will match zero or more of any character - for instance `*ython` will match `ython`, `Python`, and `\ython`

The include and exclude patterns are applied to the individul files names (relative to the root directory) and not the directory names - so to specifically match against a directory and all of its contents (say the directory `templates`), it is recommended to use a form : `*\templates\*`

.. note::

    Files within the top level directory are cataloged with file names starting with `./`, and all other files are cataloged as file paths relative to the root, but without the './'

.. note::

    When selecting which files to catalog, any exclusion filters are applied first, and if the full file path matches any single exclusion filter it is not cataloged (regardless of it's file extension or whether it matches any inclusion filter): See :ref:`FileSelection` for a full description of how files are chosen for cataloging.

Reports Section
---------------
.. note::
    This section is equivalent to the -v/--verbose, -k/-K, -t/-T, -m/-M, -i/-I, -x/-X command line options

The report section format is :

.. code-block:: cfg

    [reports]

    verbose = <level>
    mismatch = <flag>
    missing = <flag>
    extra = <flag>
    excluded = <flag>
    extension = <flag>

The options are :

    verbose
        Equivalent to the `-v/--verbose` option; defines the verbosity level of the output. <level> is a numeric value one of 0, 1 or 2. Level 0 supresses all text output. Level 1 (the default) produces the final report only. Level 2 produces a summary for each directory where there are :term:`reportable anomalies <reportable anomaly>`, as well as the final report; applies on both `check` and `create` commands

    mismatch
        Whether or not to report on mismatched files (i.e. those files which have a diferent hash signature in the directory structure than is recorded in the catalog); equivalent to the `-m/-M` command line option; only applies on the ``check`` command

    missing
        Whether or not to report on missing files (i.e. those files which are recorded in the catalog but which don't exist within the directory structure); equivalent to the `-i/-I` command line option; only applies on the ``check`` command

    extra
        Whether or not to report on extra files (i.e. those files which exist within the directory structure, but which are not recorded in the catalog); equivalent to the `-x/-X` command line option; only applies on the ``check`` command

    excluded
        Whether or not to report on the number of files which are excluded (i.e. all files excluded due to a non cataloged file extension [see :ref:`extension-section`] and  all files exluded due to matching a defined exclude filter [see :ref:`exclude-filter`] and all files exluded due to not matching a defined inculde filter [see :ref:`include-filter`]; equivalent to the `-l/-L` command line option, applies on both `check` and `create` commands

    extension
        Whether or not to report on counts per file extensions which are cataloged (i.e. those files which either cataloged on a `create` command or checked on the `check` command); equivalent to the `-t/-T` command line option, applies on both `check` and `create` commands

For the mismatched, missing, extra, excluded, extension options :

    <flag> is a representation of a boolean value - a value of `True` or `Yes` (or any upper or lower case version of those - so for example `True`, `true`, `tRuE`, `yes`, `Yes` and `yeS` all qualify as a representation of `True`. Any value of False or No (or any upper of lower case version of those - for example `False`, `false`, `fAlSe` or `No`, `no`, `NO` will qualify as a representation of 'False').

