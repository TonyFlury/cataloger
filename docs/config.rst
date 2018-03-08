===========================
Configuration file settings
===========================

By default the config file is named 'manifest.cfg' and if that file exists the configuration options
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


Sections can contain one or more `optionline`, and the exact form of these option lines depends on the section.

Leading and trailing whitespace within the section is ignored.

Lines within the config file that begin with a `#` are ignored - and can be used as comments

Manifest Section
----------------
.. note::
	This section is equivalent to the `-m/--manifest`, `-h/--hash` and `-r/--root` command line options

The format of this section is :

.. code-block:: cfg

	[manifest]

	manifest = <file name>
	hash = <hash name>
	root = <directory path>

where the ``<option>=<value>`` line can be provided for each option - if an option is repeated then the last value given is used.
Available options are :

	manifest
		The name of the manifest file. Equivalent to the ``-m/--manifest`` command line option. If not provided defaults to ``manifest.txt``
	hash
		The name of the hash algorithm to use. The name does not need quotes. Equivalent to the ``-h/--hash`` command line option. Defaults to using sha224 hash.
	root
		The root directory to use - so that all files under the root will be analysed and catalogued. Equivalent to the ``-r/--root`` command line option. This can be either a relative or absolute path (although it makes more sense to be relative) Defaults to '.'

Spaces and tabs around the ``=`` are optional.

Extensions Section
------------------
.. note::
	This section is equivalent to the -E/--clearExtensions and the +e/--add_extension and -e/--rm_extension command line options

The format of this section is :

.. code-block:: cfg

	[extensions]

	= <new extension list>
	+ <additional extension list>
	- <remove extension list>

The section can have one or more of each possible type of option line - and they can appear in any order. These lines are processed in order to build an list of file extensions which are to be analysed.

	= <new extension list>
		Reset the extension list from it's current value to just those items in the ``<new extensions list>``; Equivalent to ``-E`` followed by one or more ``-e`` command line options
	\+ <additional extension list>
		Add those extensions listed in ``<additional extension list>`` to the extension list to be used; Equivalent to a one or more ``+e`` command line options
	\- <remove extension list>
		Remove the extensions list in the ``<remove extension listt>`` from the extension list to be used; Equivalent to a one or more ``-e`` command line options.


Each of these extension lists are comma separated, with each file extension in the list starting with a ``.`` (a dot).  Spaces and tabs around the individual file extensions are ignored

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


Ignore Directories Section
--------------------------
.. note::
	This section is equivalent to the -D/--clearDirectory and -d/--ignoreDirectory command line options


Filter Section
--------------
.. note::
	This section is equivalent to the -f/--filter command line option


Reports Section
---------------
.. note::
	This section is equivalent to the -v/--verbose, -k/-K, -t/-T, -m/-M, -i/-I, -x/-X and -g/-G command line options