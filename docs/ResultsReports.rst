===================
Results and Reports
===================

Create command Report
---------------------

By default a create command will generate a report to stdout similar to this :

.. code-block:: bash

    12 files processed - 10 files excluded

    Files processed by file types:
        .py : 6
        .txt : 3
        .rst : 3


.. _excluded-files:

Counting excluded files
~~~~~~~~~~~~~~~~~~~~~~~

The count of excluded files is :

    - All files excluded due to a non cataloged file extension
    - All files exluded due to matching a defined exclude filter
    - All files exluded due to not matching a defined inculde filter

Files in :term:`top level directories <top level directory>` (see -d/+d options) are not counted
as being excluded.

Impact of verbosity settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The above report is the default from the command line, when the verbosity of 1 is use. The is the default for the command line.

If verbosity = 0 (i.e. the command line option `-v 0` is used), then the above
report is suppressed

if verbosity = 2  or 3 (command line option `-v 2`, or `-v 3`) then the report will also contain a table with a row for every directory; the table will count the number of files in that directory which are cataloged from that directory, and also a count of those excluded. The difference between the verbosity levels is that at verbosity level 2, directories are only included in the table if at least one file from that directory was included in the catalog. At verbosity level 3, all directories that were analyzed will be included in the table.

.. note::
    The table for verbosity level 2 & 3

check command Report
---------------------

By default a check command will generate a report to stdout similar to this :

.. code-block:: bash

    12 files processed - 10 files excluded

    Files processed by file types:
        .py : 6
        .txt : 3
        .rst : 3
    0 files with mismatched signatures
    0 missing files
    0 extra files

Impact of verbosity settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The above report is the default from the command line, when the verbosity of 1 is use. The is the default for the command line.

If verbosity = 0 (i.e. the command line option `-v 0` is used), then the above
report is suppressed

if verbosity = 2  or 3 (command line option `-v 2`, or `-v 3`) then the report will also contain a table with a row for every directory; the table will count the number of files in that directory which are cataloged from that directory, and also counts of mimatched, missing, extra, and excluded files. The difference between the verbosity levels is that at verbosity level 2, directories are only included in the table if at least one file from that directory was included in the catalog. At verbosity level 3, all directories that were analyzed will be included in the table.

Command line exit status
------------------------

When the check command is executed then command will exit with a status of 0 when there are no :term:`reportable anomalies <reportable anomaly>`, and a status of 1 when at least one :term:`reportable anomalies <reportable anomaly>` exists.

if this means it is entirely possible to use the check command in a bash script or similar :

.. code-block:: bash

    if ! catalog check >check_output ; then
        echo 'Integrity check failed :'
        more check_output
        exit 1


