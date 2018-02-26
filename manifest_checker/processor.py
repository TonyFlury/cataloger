#!/usr/bin/env python
# coding=utf-8
"""
# manifest-checker : Implementation of environment.py

Summary : 
    <summary of module/class being implemented>
Use Case : 
    As a <actor> I want <outcome> So that <justification>

Testable Statements :
    Can I <Boolean statement>
    ....
"""

import sys
import os
import hashlib
import six
import string
import fnmatch

from manifest_checker import defaults

__version__ = "0.1"
_author__ = 'Tony Flury : anthony.flury@btinternet.com'
__created__ = '22 Mar 2016'

class ManifestError(Exception):
    pass

class ManifestProcessor(object):
    """The context object holds the full Environment for the command Execution

        All reporting and output is driven through this class, as are file matching functionality
    """

    def __init__(self, action='', *args,  **kwargs):
        """ Maintain the execution environment for the manifest creator/checker

            Will be initially instantiated by the generic options.

        """
        # Take a 'copy' of the Default Extensions and IgnoreDirectory settings
        self._extensions = kwargs.get('extension', defaults.DEFAULT_EXTENSIONS)
        if not self._extensions:
            raise ManifestError('No file extensions given to catalogue or check')

        self._ignore_directories = kwargs.get('ignoredirectory', defaults.DEFAULT_IGNOREDIRECTORY)

        self._manifest_name = kwargs.get('manifest', defaults.DEFAULT_MANIFEST_FILE)

        self._output = kwargs.get('output', sys.stdout)
        self._verbose = kwargs.get('verbose', defaults.DEFAULT_VERBOSE)
        self._hash = kwargs.get('hash', defaults.DEFAULT_HASH)
        self._root = kwargs.get('root', os.getcwd())

        # Whether the final report includes mismatched, missing, extra, skipped or file extensions
        # Does NOT control if the data is collected
        self._report_mismatch = kwargs.get('report_mismatch', 'report_mismatch' in defaults.DEFAULT_REPORTON)
        self._report_missing = kwargs.get('report_missing', 'report_missing' in defaults.DEFAULT_REPORTON)
        self._report_extra = kwargs.get('report_extra', 'report_extra' in defaults.DEFAULT_REPORTON)
        self._report_skipped = kwargs.get('report_skipped', 'report_skipped' in defaults.DEFAULT_REPORTON)
        self._report_extension = kwargs.get('report_extensions', defaults.DEFAULT_REPORT_EXTENSIONS)

        # Turns on grouped reporting - Do we need this.
        self._group = kwargs.get('group',defaults.DEFAULT_REPORT_GROUP)

        # Internal attributes for counting skipped files, etc.
        self._skipped_file_count = 0  # Skipped files are only a count - nothing else
        self._manifest_data_count = 0  # Files output to manifest
        self._missing_files = []    # List of files that are missed
        self._extra_files = []      # List of files that are record_extra
        self._mismatched_files = [] # List of files where signatures are different
        self._extension_counts = {}  # Count of occurrence of each file extension
        self._skipped_files = []
        self._manifest_data = {}    # 2 level dictioanry - top level of directories, 2nd level per file

        self._filter = kwargs.get('filter',[])

        self._manifest_fp = None
        self._action = None

        self._error_code = 0

        if not action:
            return

        self._action = action

        self._start_command()


    @property
    def manifest_file_name(self):
        """The file name of the manifest file - provided for completeness"""
        return self._manifest_name

    @property
    def skipped_files(self):
        return self._skipped_files

    @property
    def mismatched_files(self):
        """The list of mismatched files"""
        return self._mismatched_files

    @property
    def extra_files(self):
        """The list of extra files - i.e. those that exist locally but not in the manifest"""
        return self._extra_files

    @property
    def missing_files(self):
        """The list of missing files - i.e. those that exist in the manifest but not locally"""
        return self._missing_files

    @property
    def extension_counts(self):
        """A generator of tuples of the file extensions and their counts"""
        return ((name,count) for name,count in self._extension_counts.iteritems())

    def _start_command(self):
        """Internal method to trigger the appropriate opening of the manifest file

        On a check action; the manifest is open to read -  and then loaded into memory for speed

        On a create action; the manifest is open to write
        """

        if self._action == 'create':
            # Should we open late.

            try:
                self._manifest_fp = open(self._manifest_name, 'w')
            except IOError as e:
                six.raise_from(ManifestError('Error opening manifest file : {} - {}'.format(self._manifest_name, str(e))),None)
        elif self._action == 'check':
            try:
                with open(self._manifest_name, 'r') as self._manifest_fp:
                    self._load_manifest()
            except IOError as e:
                six.raise_from(ManifestError('Error opening manifest file : {} - {}'.format(self._manifest_name, str(e))), None)
            except ManifestError as e:
                raise
            finally:
                self._manifest_fp = None
        else:
            six.raise_from(ValueError('Invalid value for subcommand: {}'.format(self._action)), None)

    def __enter__(self):
        """Prototype for context manager - to be tested"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit for manifest file - ensure that the manifest file is closed."""
        if self._manifest_fp is not None:
            self._manifest_fp.close()

        if exc_type:
            return False

    def _load_manifest(self):
        """Load the given manifest file, and analyse into a dictionary
            Dictionary is self._manifest_data - key is directory, value is 2nd level dictionary
                2nd level dictionary : key is file_name, value is signature
        """
        if not self._manifest_fp:
            raise ManifestError('Manifest not loaded: action=\'check\' must be provided')

        for line_num, entry in enumerate(self._manifest_fp):
            entry = entry.strip()

            if not entry:
                continue

            if '\t' in entry:
                name, signature = entry.strip().split('\t')
            else:
                six.raise_from(ManifestError('Invalid manifest format - missing tab on line {}'.format(line_num)), None)

            directory, file = os.path.split(name.strip())
            directory = directory if directory else '.'
            dirlist = self._manifest_data.setdefault(directory, {})

            if any(True for x in signature if x not in string.hexdigits ):
                six.raise_from(ManifestError(
                    'Invalid manifest format - invalid signature on line {}'.format(
                        line_num)), None)
            else:
                dirlist[file] = {'signature':signature.strip(), 'processed':False}


            self._manifest_data_count += 1
        else:
            if self._manifest_data_count == 0:
                six.raise_from(ManifestError('Empty manifest file : {}'.format(self._manifest_name)), None)
            else:
                return

    def _is_file_to_be_processed(self, directory, file_name):
        """Return True if this file should be recorded/processed"""

        # Don't process the Manifest file itself
        if directory == self._root and file_name == self._manifest_name:
            return False

        # Check any filters
        if self._filter:

            full = os.path.join(directory,file_name)

            # Does the full path match any filter ?
            if any(fnmatch.fnmatch(full, pat) for pat in self._filter):
                return False

        # check extensions

        ext = os.path.splitext(file_name)[1]

        if ext not in self._extensions:
            return False

        return True

    def _record_extension(self, path):
        """Record a count of each extension encountered"""
        ext = os.path.splitext(path)[1]
        self._extension_counts[ext] = self._extension_counts.setdefault(ext, 0) + 1

    def manifest_write(self, rel_path, signature):
        """Enter the file into the manifest"""

        self._manifest_fp.write('{path}\t{signature}\n'.format(path=rel_path, signature=signature))
        self._manifest_data_count += 1

        self._record_extension( rel_path)

    def _final_create(self):
        """Wrap up the manifest creation process

            Report the number of files processed, files skipped
            and report files by file extension
        """

        if self._verbose == 0:
            return

        self._output.write('{} files processed'.format(self._manifest_data_count))
        if self._report_skipped:
            self._output.write(' - {} files skipped\n'.format(self._skipped_file_count))
        else:
            self._output.write('\n')

        if self._report_extension:
            self._output.write('Processed by file type\n')
            for ext, count in self._extension_counts.iteritems():
                self._output.write("\t'{}' : {}\n".format(ext, count))

        if self._manifest_fp:
            self._manifest_fp.close()

    def _final_check(self):
        """Wrap up the Check process

           Output the number of files processed, skipped, file extension count
           Output mismatches, missing and record_extra files as appropriate.
        """
        if self._verbose == '0':
            return

        self._output.write('{} files processed'.format(self._manifest_data_count))
        if self._report_skipped:
            self._output.write(' - {} files skipped\n'.format(self._skipped_file_count))
        else:
            self._output.write('\n')

        if self._report_extension:
            self._output.write('Processed by file type\n')
            for ext, count in self.extension_counts:
                self._output.write("\t'{}' : {}\n".format(ext, count))

        if self._report_mismatch:
            self._output.write("{} files with mismatched signatures\n".format(len(self.mismatched_files)))
            if self._group:
                for f in self.mismatched_files:
                    self._output.write('\t{}\n'.format(f))

        if self._report_missing:
            self._output.write("{} missing files\n".format(len(self.missing_files)))
            if self._group:
                for f in self.missing_files:
                    self._output.write('\t{}\n'.format(f))

        if self._report_extra:
            self._output.write("{} extra files\n".format(len(self.extra_files)))
            if self._group:
                for f in self.extra_files:
                    self._output.write('\t{}\n'.format(f))

    def final_report(self):
        """Close out the command"""
        jump_table = {'create': self._final_create, 'check': self._final_check}

        jump_table[self._action]()


    def abs_path(self, rel_path):
        """Return an absolute path from a relative path - based from the given root"""
        return os.path.join(self._root, rel_path)

    def walk(self):
        """ Progress through the directory trees (multiple roots) filtering out files not required

            yield the path of the file relative to self._root

            Used during the check and create process
        """
        for directory, sub_directories, files in os.walk(self._root):

            # Don't recurse into directories that should be ignored
            # Need to alter sub_directories in place for it to be used - hence slice assignment
            if directory == self._root:
                sub_directories[:] = [sub for sub in sub_directories if sub not in self._ignore_directories]

            process_files = [file_name for file_name in files if    self._is_file_to_be_processed(directory, file_name)]
            if process_files:
                yield os.path.relpath(directory,self._root), process_files

            # Look at every file and record those to be processed and those skip
            for file_name in files:
                if file_name not in process_files:
                    self.record_skipped(directory, file_name)

    def is_file_in_manifest(self,directory, file):
        """Return True if this directory and file is in the loaded manifest"""
        return directory in self._manifest_data and file in self._manifest_data.get(directory,{})

    def is_directory_in_manifest(self, directory):
        """Return True if this directory is in the loaded manifest"""
        return directory in self._manifest_data

    def get_non_processed(self, directory):
        """Return whether this file has been processed by the checking procedure

           Only return False if the file data is in the manifest but hasn't been processed

           if the directory is missing from the manifest - then this directory is deliberately omitted

           if the file is in manifest then look at the 'processed' key ...
        """
        for file in self._manifest_data[directory]:
            if not self._manifest_data[directory][file].get('processed', False):
                yield file

    def get_signature(self, rel_path=None, manifest=False):
        """Generate or fetch the signature for the given path

           :param rel_path: The relative path from this current directory to the file
           :param abs_path: The absolute path to this file (optional)
           :param manifest: Boolean - whether to fetch the data from the manifest file.

            if manifest is True this fetches the signature for this file from
            the manifest file.

            if manifest is False this will generate the signature based on the file content

            abs_path is only used when manifest is false - and it overrides the rel_path argument

           :return:
        """
        if manifest:
            dir,name = os.path.split(rel_path)
            if dir not in self._manifest_data or name not in self._manifest_data[dir]:
                return None

            return self._manifest_data[dir][name]['signature'].strip()

        abs_path = self.abs_path(rel_path)

        m = hashlib.new(self._hash)
        try:
            with open(abs_path, 'rb') as f:
                m.update((f.read()).encode('utf-8'))
        except BaseException as e:
            sys.stderr.write("Error creating signature for '{}': {}\n".format(abs_path, e))
            return None

        return m.hexdigest().strip()

    def _path_rel_to_root(self, abspath):
        return os.path.relpath(abspath, self._root)

    def record_skipped(self, directory, file_name):
        """Record a skipped file - the path to the skipped file is not recorded - ever"""
        self._skipped_file_count += 1
        self._skipped_files.append(os.path.join(directory,file_name))

    def mark_processed(self, rel_path, status='processed'):
        if not self._manifest_data:
            return

        dir, name = os.path.split(rel_path)
        if dir not in self._manifest_data or name not in self._manifest_data[dir]:
            return
        else:
            self._manifest_data[dir][name]['processed'] = status


    def record_missing(self, rel_path):

        self._record_extension( rel_path)

        self.missing_files.append(self._path_rel_to_root(rel_path))

        if not self._group and self._verbose != '0':
            sys.stdout.write(
                    "MISSING : '{}'\n".format(self._path_rel_to_root(rel_path)))

        self.mark_processed(rel_path, 'missing')

    def record_extra(self, rel_path):

        self._record_extension( rel_path)

        self.extra_files.append(self._path_rel_to_root(rel_path))

        if not self._group and self._verbose != '0':
            sys.stdout.write(
                    "EXTRA : '{}'\n".format(self._path_rel_to_root(rel_path)))

        self.mark_processed(rel_path, 'extra')

    def record_mismatch(self, rel_path):

        self._record_extension( rel_path)

        self.mismatched_files.append(self._path_rel_to_root(rel_path))

        if not self._group and self._verbose != '0':
            sys.stdout.write(
                    "MISMATCH : '{}'\n".format(self._path_rel_to_root(rel_path)))

        self.mark_processed(rel_path, 'mismatch')