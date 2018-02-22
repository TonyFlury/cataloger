Manifest Checker
================

The manifest checker is a command line tool for the creation and checking of manifest files. Typically it is intended to be
used to confirm that a directory structure can be deployed/copied in a consistent way from a source to a target.

There is a two step process for confirming consistency :

1. A manifest is created (using the `manifest create` command). This command scans the directory tree, looking for known source code files. A manifest file is created, which is a simple text file listing every source code file found, and a checksum/hash for each file - thus recording a reasonable mark of the file contents.

2. Following deployment of the directory tree (including the manifest file), the manifest can be checked against the deployed copy, by executing the `manifest check` command. This command scans the directory tree, looking for the source code files, and checking the found files against the manifest file is created. During this check 3 types of exception can be reported :

   - mismatched files - where the signature of the deployed file is not the same as that in the manifest file
   - missing files - where files are listed in the manifest but not in the deployed directory tree
   - record_extra files - where files exist in the deployed directory tree but don't exist in the manifest file

The toolset was initially designed to check a deployment of a Django based website, and therefore many of the defaults are set for DJango projects including : The source files to look for, and also which sub-directories to ignore. All of these can be overidden by command line options, and there are early plans for a configuration file as well.


.. warning::
    Versions early than 0.0.2rc6 incorrectly ignores missing files - this has now been fixed.


Links :

- `Full Documentation`_
- `Source Code`_


.. _Full Documentation: http://manifest-checker.readthedocs.org/en/latest/
.. _Source Code: https://