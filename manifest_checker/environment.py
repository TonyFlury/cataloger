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
import click
import defaults

__version__ = "0.1"
_author__ = 'Tony Flury : anthony.flury@btinternet.com'
__created__ = '22 Mar 2016'


class CommandEnvironment(object):
    """The context object holds the full Environment for the command Execution

        All reporting and output is driven through this class, as are file matching functionality
    """

    def __init__(self, *args, **kwargs):
        """ Maintain the execution environment for the manifest creator/checker

            Will be initially instantiated by the generic options.

        """
        # Take a 'copy' of the Default Extensions and IgnoreDirectory settings
        self._extensions = defaults.DEFAULT_EXTENSIONS
        self._ignore_directories = defaults.DEFAULT_IGNOREDIRECTORY

        # All other attributes are set to their default by the command line processing
        # Includes - verbose,hash, root, report_skipped, report_extension, summary

        self._skipped_files = 0  # Skipped files are only a count - nothing else
        self._listed_files = 0  # Files output to manifest
        self._missing_files = []
        self._extra_files = []
        self._mismatched_files = []
        self._file_extensions = {}
        self._manifest_data = {}
        self._manifest_length = 0

        self._manifest = None
        self._subcommand = None
        self._report_mismatch = True
        self._report_missing = True
        self._report_extra = True
        self._report_skipped = False
        self._group = True

        self._error_code = 0  # Initially assume that the create/check will complete successfully

        self._manifest_name = kwargs['manifest']

        self._output = sys.stdout
        self._verbose = kwargs['verbose']
        self._hash = kwargs['hash']
        self._root = kwargs['root']
        self._report_skipped = kwargs['report_skipped']
        self._report_extension = kwargs['report_extensions']

        # Sort out the extensions - has the cli added any
        self._extensions = list(kwargs.get('extension', [])) + \
                           (self._extensions if not kwargs.get('clearextensions', False) else [])

        if not self._extensions:
            raise click.BadOptionUsage('Must specify at least one "-e"/"--extension" when you use --clearExtension')

        # Sort out the ignoredirectory - has the cli added any
        self._ignore_directories = list(kwargs.get('ignoredirectory', [])) + \
                                   (self._ignore_directories if not kwargs.get('cleardirectory', False) else [])

    def update(self, **kwargs):
        if kwargs.get('subcommand') == 'create':
            self._subcommand = 'create'
            self._manifest = open(self._manifest_name, 'w')

        elif kwargs.get('subcommand') == 'check':
            self._subcommand = 'check'
            self._manifest = open(self._manifest_name, 'r')

            self._report_mismatch = kwargs['report_mismatch']
            self._report_missing = kwargs['report_missing']
            self._report_extra = kwargs['report_extra']

            self._group = kwargs['group']

    def __str__(self):
        return str(self.__dict__)

    def load_manifest(self):

        try:
            for entry in self._manifest:
                name, signature = entry.split('\t')
                directory, file = os.path.split(name.strip())
                dirlist = self._manifest_data.setdefault(directory, {})
                dirlist[file] = signature
                self._manifest_length += 1
        except EnvironmentError as e:
            sys.stderr.write("Unable to read manifest file '{}' : {}\n".format(self._manifest_name, e))
            sys.exit(1)

    def _file_to_be_processed(self, directory, file_name):

        # Don't process the Manifest file itself
        if directory == self._root and file_name == self._manifest_name:
            return False

        ext = os.path.splitext(file_name)[1]

        # check extensions
        if ext not in self._extensions:
            return False

        return True

    def _record_extension(self, path):
        if self._report_extension:
            ext = os.path.splitext(path)[1]
            self._file_extensions[ext] = self._file_extensions.setdefault(ext, 0) + 1

    def list(self, rel_path, signature):
        self._manifest.write('{path}\t{signature}\n'.format(path=rel_path, signature=signature))
        self._listed_files += 1

        self._report_extension()

    def _final_create(self):
        if self._verbose == 0:
            return

        self._output.write('{} files processed'.format(self._listed_files))
        if self._report_skipped:
            self._output.write(' - {} files skipped\n'.format(self._skipped_files))
        else:
            self._output.write('\n')

        if self._report_extension:
            self._output.write('Processed by file type\n')
            for ext, count in self._file_extensions.iteritems():
                self._output.write("\t'{}' : {}\n".format(ext, count))

        sys.exit(self._error_code)

    def _final_check(self):
        if self._verbose == 0:
            sys.exit(self._error_code)

        self._output.write('{} files processed'.format(self._manifest_length))
        if self._report_skipped:
            self._output.write(' - {} files skipped\n'.format(self._skipped_files))
        else:
            self._output.write('\n')

        if self._report_extension:
            self._output.write('Processed by file type\n')
            for ext, count in self._file_extensions.iteritems():
                self._output.write("\t'{}' : {}\n".format(ext, count))

        if self._report_mismatch:
            self._output.write("{} files with mistmatched signatures\n".format(len(self._mismatched_files)))
            if self._group:
                for f in self._mismatched_files:
                    self._output.write('\t{}\n'.format(f))

        if self._report_missing:
            self._output.write("{} missing files\n".format(len(self._missing_files)))
            if self._group:
                for f in self._missing_files:
                    self._output.write('\t{}\n'.format(f))

        if self._report_extra:
            self._output.write("{} extra files\n".format(len(self._extra_files)))
            if self._group:
                for f in self._extra_files:
                    self._output.write('\t{}\n'.format(f))

        sys.exit(self._error_code)

    def _finalise(self):

        jump_table = {'create': self._final_create, 'check': self._final_check}

        jump_table[self._subcommand]()

        if self._manifest:
            self._manifest.close()

        if self._output:
            self._output.close()

    def abs_path(self, rel_path):
        return os.path.join(self._root, rel_path)

    def walk(self):
        """ Progress through the directory trees (multiple roots) filtering out files not required
        """
        for directory, sub_directories, files in os.walk(self._root):
            for file_name in files:
                if self._file_to_be_processed(directory, file_name):
                    yield os.path.relpath(os.path.join(directory, file_name), self._root)
                else:
                    self.skipping(directory, file_name)

            if directory in self._root:
                for ignored_dir in self._ignore_directories:
                    if ignored_dir in sub_directories:
                        sub_directories.remove(ignored_dir)

            # In theory we have been through every file in the directory
            if directory in self._manifest_data:
                for f in self._manifest_data[directory]:
                    self.missing(os.path.join(directory, f))

        self._finalise()

    def get_signature(self, rel_path=None, abs_path=None, manifest=False):
        if manifest:
            dir,name = os.path.split(rel_path)
            if dir not in self._manifest_data or name not in self._manifest_data[dir]:
                return None

            return self._manifest_data[dir][name].strip()

        if abs_path is None:
            abs_path = os.path.join(self._root, rel_path)

        m = hashlib.new(self._hash)
        try:
            with open(abs_path, 'rb') as f:
                m.update(f.read())
        except BaseException as e:
            sys.stderr.write("Error creating signature for '{}': {}\n".format(abs_path, e))
            return None

        return m.hexdigest().strip()

    def _file_name_to_record(self, abspath):
        return os.path.relpath(abspath, self._root)

    def skipping(self, directory, file_name):
        """Record a skipped file - the path to the skipped file is not recorded - ever"""
        if self._report_skipped:
            return

        if self._verbose == 0:
            return

        self._skipped_files += 1

    def missing(self, rel_path):
        if not self._report_missing:
            return

        self._error_code = 1

        if self._verbose == 0:
            return

        self._record_extension( rel_path)

        self._missing_files.append(self._file_name_to_record(rel_path))

        if not self._group:
            sys.stdout.write(
                    "MISSING : '{}'\n".format(self._file_name_to_record(rel_path)))

    def mark_processed(self, rel_path):
        if not self._manifest_data:
            return

        self._record_extension(rel_path)

        dir, name = os.path.split(rel_path)
        if dir not in self._manifest_data or name not in self._manifest_data[dir]:
            return
        else:
            del self._manifest_data[dir][name]

    def extra(self, rel_path):
        if not self._report_extra:
            return

        self._error_code = 1

        if self._verbose == 0:
            return

        self._record_extension( rel_path)

        self._extra_files.append(self._file_name_to_record(rel_path))

        if not self._group:
            sys.stdout.write(
                    "EXTRA : '{}'\n".format(self._file_name_to_record(rel_path)))

        self.mark_processed(rel_path)

    def mismatch(self, rel_path):
        if not self._report_mismatch:
            return

        self._error_code = 1

        if self._verbose == 0:
            return

        self._record_extension( rel_path)

        self._mismatched_files.append(self._file_name_to_record(rel_path))

        if not self._group:
            sys.stdout.write(
                    "MISMATCH : '{}'\n".format(self._file_name_to_record(rel_path)))

        self.mark_processed(rel_path)
