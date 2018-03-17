========
Glossary
========

.. glossary::
    :sorted:

    reportable anomaly
        Anomalies are the potential results of the :term:`check` command. There are three types of anomaly : :term:`mismatch`, :term:`missing` and :term:`extra` files.

    mismatch
        Any file where the file within the directory structure has a different hash signature than the signature that exists in the catalog for the same file. The command line options -m/-M can be used to control if mismatch anomalies are reported on.

    missing
        A file which exists in the catalog but does not exist within the directory structure. The command line options -i/-I can be used to control if missing file anomalies are reported on.

    extra
        A file which exists within the directory structure but does not exist within the catalog. The command line options -x/-X can be used to control if extra file anomalies are reported on.

    create
        The sub-command to scan a directory structure and create a catalog of relevant files. The catalog contains the path to the file, and a signature hash value so that any subsequent changes can be reported.

    check
        The sub command to scan the local directory structure are create a report comparing the local directory structure with the previously :term:`created <create>` :term:`catalog`. The check command uses the data in the catalog to identfy :term:`mismatched <mismatch>` files, :term:`extra` files and :term:`missing` files.

    catalog
        A simple flat data store constructed by the :term:`create sub-command <create>`. The catalog provides a file path (stored as a path relative to the :term:`root` directory) for each :term:`selected file` within the directory structure, and a hash signature using the specified hash algorithm (sha224 is the default). The catalog is constructed recursively from the :term:`root` downwards.

    root
        An optional argument provided to the command line or the API to identify where the analysis of the directory structure should start. It defaults to '.' (i.e. the current working directory when the :term:`create` or :term:`check` sub-commands or APIs are executed.

    top level directory
        A directory contained within the :term:`root` directory. The catalog tool set and APIs has the feature of being able to entirely disregard named top-level directories without analyzing the contents.

    selected file
        A file which is identified as needing to be cataloged, or needing to be checked against the catalog.

            There are multiple mechanisms for including and excluding files from the
            catalog and they are applied In strict order :

            - All files within :term:`top level directories <top level directory>` (as modified using the -d/+d
              options and the [directories] section of the config file) are not cataloged
              regardless of their file extensions

            - Files whose files extension does not match one of the file extension list
              (as modified by -e/+e and the ``[extensions]`` section of the config file) are not
              cataloged.

            - Files which match any specific exclusion filter (the -f option or the
              ``exclude`` option in the config ``[filters]`` section) are not cataloged.

            - Files which do not match any specific included filter (the +f option or the
              ``include`` option in the config ``[filters]`` section) are not cataloged.