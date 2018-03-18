Cataloger
=========

The Cataloger is a command line tool for the creation of catalogs and then checking files against that catalog. Typically it is intended to be used to confirm that a directory structure can be deployed/copied in a consistent way from a source to a target.

There is a two step process for confirming consistency :

1. A catalog is created (using the `catalog create` command). This command scans the directory tree, looking for appropriate files. The catalog contains the path to the file and a checksum/hash of the file. The checksum recorded is sufficient to stop changes in that file..

2. Following deployment of the directory tree (including the catalog file and any configuration file), the catalog is be checked against the deployed directory structure, by using the `catalog check` command. This command scans the directory tree, looking for files using the same criteria as the catalog was constructed, and checking the found files against the cate file. During this check 3 types of exception can be reported :

   - mismatched files - where the signature of the deployed file is not the same as that in the catalog.
   - missing files - where files are listed in the catalog but not in the deployed directory tree
   - record_extra files - where files exist in the deployed directory tree but don't exist in the catalog

The toolset was initially designed to check a deployment of a Django based website, and therefore many of the defaults are set for DJango projects including : The source files to look for, and also which sub-directories to ignore. All of these can be overidden by command line options,in configuration file as well (from 0.1.0rc4)


.. warning::
    Versions early than 0.0.2rc6 incorrectly ignores missing files - this has now been fixed.


Links :

- `Full Documentation`_
- `Source Code`_


.. _Full Documentation: http://cataloger.readthedocs.org/en/latest/
.. _Source Code: https://github.com/TonyFlury/cataloger