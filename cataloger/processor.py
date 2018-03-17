#!/usr/bin/env python
# coding=utf-8
"""
# cataloger : Implementation of environment.py

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
import errno
import click
from collections import OrderedDict

import re
from cataloger import defaults

__version__ = "0.1"
_author__ = 'Tony Flury : anthony.flury@btinternet.com'
__created__ = '22 Mar 2016'


class CatalogError(Exception):
    """An Error which occurs during the processing of the Manifest file"""
    pass


class ConfigError(Exception):
    """An Error which occurs during the processing of the Config file"""
    pass


class Cataloger(object):
    """General class for processing the catalog file

        Implements the low level API as documented and
            read the config file as documented

        Includes : Auto reading of the config file
            methods for walking through the directory - applying config rules
            methods for extracting hashes for the files
            helper methods for programatically recording
                missing files
                extra files
                mismatched files
                skipped/ignored files
    """

    _config_title = re.compile(r'^\[(.*?)\]$')

    # Dictionary of sections, and their options, and the attibutes and defaults
    # Top Level : k = section title, v = attribute dict
    # Attribute dict : k - attribute name, v = attribute info tuple
    # Attribute Info Tuple : [0] = instance attribute name, [1] = default value
    config_sections_and_attrs = \
        {'catalog':
             {'catalog': ('_catalog_name', defaults.DEFAULT_CATALOG_FILE),
              'root': ('_root', '.'),
              'hash': ('_hash', defaults.DEFAULT_HASH)},
         'extensions':
             {'extensions': ('_extensions', defaults.DEFAULT_EXTENSIONS)},
         'directories':
             {'directories': (
                 '_ignore_directories', defaults.DEFAULT_IGNOREDIRECTORY)},
         'filters':
             {'include': ('_include_filter', None),
              'exclude': ('_exclude_filter', None), },
         'reports':
             {'verbose': ('_verbose', defaults.DEFAULT_VERBOSE),
              'mismatch': ('_report_mismatch',
                           'report_mismatch' in defaults.DEFAULT_REPORTON),
              'missing': ('_report_missing',
                          'report_missing' in defaults.DEFAULT_REPORTON),
              'excluded': ('_report_excluded',
                          'report_excluded' in defaults.DEFAULT_REPORTON),
              'extra': (
                  '_report_extra',
                  'report_extra' in defaults.DEFAULT_REPORTON),
              'extension': (
                  '_report_extension', defaults.DEFAULT_REPORT_EXTENSIONS)
              }
         }

    def __init__(self, action='', verbose=0, **kwargs):
        """
            Capture and process the arguments - either from the command line -
            :param no_config: Boolean - if true the config file is ignored
                    Defaults to False

            :param config: The name of the config file to use
                    Defaults to ''. Unless a specific config file is provided
                    the processor will attempt to read defaults.DEFAULT_CONFIG_FILE as
                    the config file.

            :param action: One of create or check - no default

            :param catalog: The name of the catalog file to use
                    Defaults to catalog.cat
            :param hash: The name of the hash algorithm to use
                    Defaults to sha224
            :param root: The root directory to start the cataloguing
                            Can be an absolute path or relative path
                    Defaults to '.'

            :param extensions: A list or set of file extensions - where files
                    with this extensions are catalogued.
                    Defaults to .py, .html, .txt, .css, .js,
                                .gif, .png, .jpg, .jpeg

            :param rm_extension: A set of extensiions to remove from catalogue
                    No Default
            :param add_extension: A set of extensiions to add to catalogue
                    No Default

            :param ignore_directory: A set of directories under root which are
                    to be ignored and not catalogued
                    Defaults to static, htmlcov, media, build, dist, docs

            :param rm_directory: A set of directories to removed from the
                    ignore_directory set.
                    No Default
            :param add_directory: A list/set of directories to be added to the
                    ignore_directory set.
                    No Default

            :param include_filter: A glob file matching filter of files to
                    catalogue. Default behaviour is that all files which have
                    a file extension in the ``extensions`` set are catalogued

            :param exclude_filter: A glob file matching filter of files to
                    exclude from catalogue. Default behaviour is that no files
                    which have a file extension in the ``extensions`` set is
                    excluded from the catalogue.

            :param report_mismatch: Boolean - Whether to include reports on
                    mismatched files (i.e. files which exist in the catalog,
                    and the local directory tree but have different hash
                    values). Only relevant on a check action. Default - True

            :param report_missing: Boolean - Whether to report on missing
                    files (i.e. files which exist in the catalog but are
                    missing from the local directory tree). Only relevant on a
                    check action. Default - True

            :param report_extra: Boolean - Whether to report on extra files
                    (i.e. files which don't exist in the catalog but which
                    exist in the local directory tree). Only relevant on a
                    check action. Default - True

            :param report_skipped: Boolean - Whether to the report the counts
                    of excluded files. The count doesn't include files in top
                    level ignored directories. Default - True

            :param report_extensions: Boolean - whether to report on counts of
                    catalogued extensions. Default - True

            :param verbose: The level of detail to report during cataloguing
                    Default - 1

            Config file processing :
            ------------------------

            All of the arguments (and by extension the command line arguments)
            are processed after the config file if any.

            If the no_config flag is True, then all config files are ignored
            and only the parameters passed to the constructor are used.

            Assuming no_config is False :

                * If config is '' or None, then the default config file is
                used only if it exists, and no error is created if the file
                doesn't exist.

                * if config is not Null (even if it is the default name) then
                the file is used if it exists, but a warning is generated if
                the file doesn't exist - execution continues as if the config
                file is empty.
        """
        for section, section_data in self.config_sections_and_attrs.items():
            for option, attr_data in section_data.items():
                name, default = attr_data
                setattr(self, name, default)
        # Set the defaults for each attribute in each section
        # map(lambda n_d: setattr(self, n_d[0], n_d[1]),
        #     [n_d for section in self.config_sections_and_attrs
        #      for opt, n_d in
        #      self.config_sections_and_attrs[section].items()])

        self._config = kwargs.get('conifg', defaults.DEFAULT_CONFIG_FILE)
        self._config = defaults.DEFAULT_CONFIG_FILE if not self._config else self._config

        self._noconfig = kwargs.get('no_config', False)

        if not self._noconfig:
            self._process_config(
                explicit_config_file=kwargs.get('config', '') != '')

        # The catalog section - override defaults with kwargs if they exist
        self._catalog_name = kwargs.get('catalog', self._catalog_name)
        self._hash = kwargs.get('hash', self._hash)
        self._root = kwargs.get('root', self._root)

        # The report section
        self._verbose = kwargs.get('verbose', self._verbose)
        self._output = kwargs.get('output', sys.stdout)
        self._report_mismatch = kwargs.get('report_mismatch',
                                           self._report_mismatch)
        self._report_missing = kwargs.get('report_missing',
                                          self._report_missing)
        self._report_extra = kwargs.get('report_extra', self._report_extra)
        self._report_excluded = kwargs.get('report_excluded',
                                           self._report_excluded)
        self._report_extension = kwargs.get('report_extensions',
                                            self._report_extension)

        self._extensions = set(kwargs.get('extensions', self._extensions))
        self._extensions -= set(kwargs.get('rm_extension', []))
        self._extensions |= set(kwargs.get('add_extension', []))

        if not self._extensions:
            raise CatalogError(
                'No file extensions given to catalogue or check')

        self._ignore_directories = set(
            kwargs.get('ignore_directory', self._ignore_directories))
        self._ignore_directories -= set(kwargs.get('rm_directory', {}))
        self._ignore_directories |= set(kwargs.get('add_directory', {}))

        # Only use include_filter argument if it isn't blank
        if 'include_filter' in kwargs and kwargs['include_filter']:
            self._include_filter = kwargs['include_filter']

        # Only use exclude_filter argument if it isn't blank
        if 'exclude_filter' in kwargs and kwargs['exclude_filter']:
            self._exclude_filter = kwargs['exclude_filter']

        # ToDO Remove Report Grouping probably
        # Turns on grouped reporting - Do we need this.
        self._group = kwargs.get('group', defaults.DEFAULT_REPORT_GROUP)

        # Internal attributes for counting excluded files, etc.
        self._excluded_file_count = 0  # Skipped files are only a count
        self._catalog_data_count = 0  # Files output to catalog
        self._extra_files = []  # List of files that are record_extra
        self._mismatched_files = []  # List of mismatched files
        self._extension_counts = {}  # Count of each file extension
        self._excluded_files = []

        # catalog_data is a 2 level dictioanry:
        # top level of directories, key = directory, value is dictionary
        # 2nd level key = file name, value is 2-tuple (signature/status)
        self._catalog_data = OrderedDict()

        self._catalog_fp = None
        self._action = None

        self._error_code = 0

        if not action:
            return

        self._action = action

        self._start_command()

    @property
    def verbose(self):
        return int(self._verbose)

    def report_category(self, category):
        cat_to_attr = {'excluded':'_report_excluded','missing':'_report_missing',
                       'mismatch':'_report_mismatch','extra':'_report_extra',
                       'extension':'_report_extension'}
        try:
            return getattr(self, cat_to_attr[category])
        except Exception:
            return False

    @property
    def catalog_file_name(self):
        """The file name of the catalog file - provided for completeness"""
        return self._catalog_name

    @property
    def processed_count(self):
        return self._catalog_data_count

    @property
    def excluded_files(self):
        """The list of those files excluded due to exclude filters"""
        return self._files_by_status('excluded')

    @property
    def mismatched_files(self):
        """The list of mismatched files
            those where the signatures do not match
        """
        return self._files_by_status('mismatch')

    @property
    def extra_files(self):
        """The list of extra files
            those that exist locally but not in the catalog"""
        return self._files_by_status('extra')

    @property
    def missing_files(self):
        """The list of missing files
            those that exist in the catalog but not locally"""
        return self._files_by_status('missing')


    @property
    def catalog_summary_by_directory(self):
        for directory, files in self._catalog_data.items():
            yield {'path':directory,
                   'added':sum(1 for file, data in files.items() if data['processed'] == 'added'),
                   'processed': sum(1 for file, data in files.items() if
                                data['processed'] == 'processed'),
                   'excluded':sum(1 for file, data in files.items() if data['processed'] == 'excluded'),
                   'missing': sum(1 for file, data in files.items() if data['processed'] == 'missing'),
                   'mismatch': sum(1 for file, data in files.items() if data['processed'] == 'mismatch'),
                   'extra': sum(1 for file, data in files.items() if data['processed'] == 'extra'),}

    def _files_by_status(self, status):
        return [file_name if directory == '.'
                            else os.path.join(directory, file_name)
                for directory, files in self._catalog_data.items()
                    for file_name in files
                        if files[file_name]['processed'] == status]

    @property
    def extension_counts(self):
        """A dictionary the file extensions and their counts"""
        return self._extension_counts

    def _read_config(self, explicit_config_file=False):
        """A generator for the lines in the config file

            :param explicit_config_file: Boolean
                True if a config file was explicitly passed as an argument
                to the constructor

           Gracefully handle the following situations :

           1. Config fle exists
           2. Config file doesn't exist but one was not explicit requested
           3. Explicitly requested config file Config file doesn't exist.
           4. Some other error prevents the config file being raised
        """
        # Read and close the config file as quick as possible
        try:
            # Try to open the file and read it - case 1
            with open(self._config, 'r') as config_fp:
                for line in config_fp:
                    yield line
        except IOError as e:
            if e.errno == errno.ENOENT:
                # Config file doesn't exist
                if not explicit_config_file:
                    # No config file was explicity requested - case 2
                    raise StopIteration
                else:
                    # config file was explicity requested - case 3
                    click.echo(
                        'Warning : Unable to open config file \'{}\'; '
                        'continuing with defaults'.format(
                            self._config), err=True)
                    raise StopIteration
            else:
                # Some other IOError - case 4 -  permissions etc
                six.raise_from(ConfigError(
                    'Unable to read config file \'{}\' : {}1'.format(
                        self._config, e.strerror)), None)
        except Exception as e:
            # Some other IOError - case 4 -likely a catch all
            six.raise_from(ConfigError(
                'Unable to read config file \'{}\' : {}'.format(
                    self._config, str(e))), None)

    def _process_config(self, explicit_config_file=False):
        """Process the config file

        :param explicit_config_file: Boolean if an explicit config file was
                provided

        :raises : Config Error if the Config file is invalid

        Process the config file, line by line

        1) Identify unknown sections and raise exception
        """
        sections = set()
        current_section = ''

        for line_no, cfg_line in enumerate(
                self._read_config(explicit_config_file=explicit_config_file)):
            cfg_line = cfg_line.strip()

            # Ignore blank lines and comment lines
            if not cfg_line or cfg_line[0] == '#':
                continue

            # Identify a section title
            is_title = self._config_title.match(cfg_line)
            if is_title:
                section_title = is_title.group(1)

                # Are we looking at a section which shouldn't exist
                if section_title not in self.config_sections_and_attrs:
                    six.raise_from(ConfigError(
                        'Unknown section title in config file :'
                        '  \'{}\' on line {}'.format(
                            cfg_line, line_no)), None)

                # Are we looking at a section title which has already happened
                if section_title in sections:
                    six.raise_from(ConfigError(
                        'Repeated section title in config file :'
                        '  \'{}\' on line {}'.format(
                            cfg_line, line_no)), None)

                # Record this section title, and move on to the next line.
                sections.add(section_title)
                current_section = section_title
                continue
            else:
                if not current_section:
                    six.raise_from(ConfigError(
                        'Config line outside a section :'
                        '  \'{}\' on line {}'.format(
                            cfg_line, line_no)), None)

                # Call a specific processing function for the config
                # which function depends on which section we are in
                getattr(self, '_config_line_' + current_section + '_section')(
                    line=cfg_line, line_no=line_no)

    def _config_line_reports_section(self, line, line_no):
        """Called for each line in the directories section
           line is in one of 3 formats:
                = <new directory list>
                - <remove directory list>
                + <additional directory list

            :param line: The full line from the config file
            :param line_no : The line number in the config file

            :raises ConfigError: When an invalid line is detected"""
        attrs_options = self.config_sections_and_attrs['reports']
        try:
            option, _, value = (x.strip() for x in line.partition('='))
            # Try to identify what this option is - based on the attribute to set
            attr_name = attrs_options[option][0]
            if not hasattr(self, attr_name):
                raise KeyError
            try:
                if option != 'verbose':
                    if value.lower() in ['true', 'yes']:
                        value = True
                    elif value.lower() in ['false', 'no']:
                        value = False
                    else:
                        raise ValueError
                else:
                    value = int(value)
                    if value not in [0,1,2]:
                        raise ValueError
            except ValueError:
                    six.raise_from(ConfigError(
                        'Invalid value in section [reports] :'
                        ' \'{}\' on line {}'.format(
                            line, line_no)), None)
            setattr(self, attrs_options[option][0], value)
        except KeyError:
            six.raise_from(ConfigError(
                'Invalid option in section [reports] :'
                ' \'{}\' on line {}'.format(
                    line, line_no)), None)

    def _config_line_directories_section(self, line, line_no):
        """Called for each line in the directories section
           line is in one of 3 formats:
                = <new directory list>
                - <remove directory list>
                + <additional directory list

            :param line: The full line from the config file
            :param line_no : The line number in the config file

            :raises ConfigError: When an invalid line is detected
        """
        # Extract Attribute name from the config sections data
        attr_name = \
            self.config_sections_and_attrs['directories']['directories'][0]
        op, direct = line[0], set(
            d.strip() for d in line[1:].strip().split(','))

        direct = direct if direct != {''} else set()

        if direct:
            # Identify null strings or strings which are just dots
            if any(d == '' for d in direct):
                six.raise_from(ConfigError(
                    'Invalid value in [directories] section :'
                    ' \'{}\' on line {}'.format(
                        line, line_no)), None)

        self._config_operator_list_modifiers(
            attr_name, direct, line, line_no, op, 'directories')

    def _config_line_extensions_section(self, line, line_no):
        """Called for each line in the extensions section
            line is in one of 3 formats:
                 = <new directory list>
                 - <remove directory list>
                 + <additional directory list

             :param line: The full line from the config file
             :param line_no : The line number in the config file
         """
        # Extract Attribute name from the config sections data
        section_data = self.config_sections_and_attrs['extensions']
        attr_name = section_data['extensions'][0]

        op, ext = line[0], set(e.strip() for e in line[1:].strip().split(','))

        ext = ext if ext != {''} else set()

        if ext:
            # Identify null strings or strings which are just dots
            if any(len(e) <= 1 for e in ext):
                six.raise_from(ConfigError(
                    'Invalid value in [extension] section :'
                    ' \'{}\' on line {}'.format(
                        line, line_no)), None)

            # Identify extension values without a leading dot
            if any(e[0] != '.' for e in ext):
                six.raise_from(ConfigError(
                    'Invalid value in [extension] section :'
                    ' \'{}\' on line {}'.format(
                        line, line_no)), None)

        self._config_operator_list_modifiers(
            attr_name, ext, line, line_no, op, 'extension')

    def _config_operator_list_modifiers(self, attr_name, values, line, line_no,
                                        op,
                                        section):
        """Execute + <list>, -<list> or =<list> line in config file

            Used in the extension and directories section
            :param attr_name: The instance attribute to change
            :param values: The values from the config file
            :param line: The full line from the config file
            :param line_no: the line number of this line
            :param op: The actual operation (one of +,- or =)
            :param section: The section of the config file
        """
        if op == '=':
            setattr(self, attr_name, values)
            return

        if not values:
            six.raise_from(ConfigError(
                'Invalid value in [{section}] section :'
                ' \'{line}\' on line {line_no}'.format(
                    section=section, line=line, line_no=line_no)), None)

        if op == '+':
            setattr(self, attr_name, getattr(self, attr_name) | values)
        elif op == '-':
            setattr(self, attr_name, getattr(self, attr_name) - values)
        else:
            six.raise_from(ConfigError(
                'Invalid operator in [{section}] section :'
                ' \'{line}\' on line {line_no}'.format(
                    section=section, line=line, line_no=line_no)), None)

    def _config_line_filters_section(self, line, line_no):
        """Called for any line in the catalog section

            Each line can only be : <option>=<value>

            :param line: The full line from the config file
            :param line_no : The line number in the config file
        """
        attrs_options = self.config_sections_and_attrs['filters']
        try:
            option, _, value = (x.strip() for x in line.partition('='))
            setattr(self, attrs_options[option][0],
                    set(x.strip() for x in value.split(',')))
        except KeyError:
            # Error from finding the relevant atrribute name in the config dict
            six.raise_from(ConfigError(
                'Invalid config line in section [filters] :'
                ' \'{}\' on line {}'.format(
                    line, line_no)), None)

    def _config_line_catalog_section(self, line, line_no):
        """Called for any line in the catalog section

            Each line can only be : <option>=<value>

            :param line: The full line from the config file
            :param line_no : The line number in the config file
        """
        attrs_options = self.config_sections_and_attrs['catalog']
        try:
            option, _, value = (x.strip() for x in line.partition('='))
            setattr(self, attrs_options[option][0], value)
            try:
                getattr(self, '_config_validate_' + option)(line, line_no,
                                                            value)
            except ConfigError:
                raise
            except AttributeError:
                return
        except KeyError:
            six.raise_from(ConfigError(
                'Invalid config line in section [catalog] :'
                ' \'{}\' on line {}'.format(
                    line, line_no)), None)

    @staticmethod
    def _config_validate_hash(line, line_no, value):
        """Helper funvtion to validate the hash """
        if value not in hashlib.algorithms_available:
            raise six.raise_from(ConfigError(
                'Invalid value for hash :'
                ' \'{}\' on line {}'.format(line, line_no)),None)

    def _start_command(self):
        """Internal method to trigger the appropriate opening of the catalog file

        On a check action; the catalog is open to read -  and then loaded
        into memory for speed

        On a create action; the catalog is open to write
        """
        if self._action == 'check':
            try:
                with open(self._catalog_name, 'r') as self._catalog_fp:
                    self._load_catalog()
            except IOError as e:
                six.raise_from(CatalogError(
                    'Error opening catalog file : {} - {}'.format(
                        self._catalog_name, str(e))), None)
            except CatalogError as e:
                raise
            finally:
                self._catalog_fp = None
        elif self._action != 'create':
            six.raise_from(ValueError(
                'Invalid value for subcommand: {}'.format(self._action)), None)

    def _load_catalog(self):
        """Load the given catalog file, and analyse into a dictionary
            Top Level dict:  key is directory, value is 2nd level dictionary
                2nd level dictionary : key is file_name, value is signature
        """
        for line_num, entry in enumerate(self._catalog_fp):
            entry = entry.strip()

            if not entry:
                continue

            if '\t' not in entry:
                six.raise_from(CatalogError(
                    'Invalid catalog format - missing tab on line {}'.format(
                        line_num)), None)

            entry_name, signature = entry.strip().split('\t')

            directory, file_name = os.path.split(entry_name.strip())
            directory = directory if directory else '.'
            dirlist = self._catalog_data.setdefault(directory, {})

            if any(True for x in signature if x not in string.hexdigits):
                six.raise_from(CatalogError(
                    'Invalid catalog format -'
                    ' invalid signature on line {}'.format(
                        line_num)), None)
            else:
                dirlist[file_name] = OrderedDict([('signature', signature.strip()),
                                      ('processed', False)])

            self._catalog_data_count += 1
        else:
            if self._catalog_data_count == 0:
                six.raise_from(CatalogError(
                    'Empty catalog file : {}'.format(self._catalog_name)),
                    None)
            else:
                return

    def _is_file_to_be_processed(self, directory, file_name):
        """Return True if this file should be recorded/processed"""

        # Don't process the Manifest file itself
        if directory == self._root and file_name == self._catalog_name:
            return False

        full = os.path.join(directory, file_name)

        # Check any filters
        if self._exclude_filter:

            # Does the full path match any filter ?
            if any(fnmatch.fnmatch(full, pat) for pat in self._exclude_filter):
                return False

        if self._include_filter:
            if all(not fnmatch.fnmatch(full, pat) for pat in
                    self._include_filter):
                return False

        # check extensions

        ext = os.path.splitext(file_name)[1]

        if ext not in self._extensions:
            return False

        return True

    def _record_extension(self, path):
        """Record a count of each extension encountered"""
        ext = os.path.splitext(path)[1]
        self._extension_counts[ext] = self._extension_counts.setdefault(ext,0) + 1

    def add_to_catalog(self, rel_path, signature):
        """Add data to the catalog"""
        directory, file_name = os.path.split(rel_path)
        d_data = self._catalog_data.setdefault(directory, {})
        d_data[file_name] = {'signature':signature,
                                        'processed':'added'}

        self._catalog_data_count += 1
        self._record_extension(rel_path)

    def write_catalog(self):
        """Write the file data into the catalog"""

        try:
            with open(self._catalog_name, 'w') as catalog_fp:
                for directory, files in self._catalog_data.items():
                    for file_name, data in self._catalog_data[directory].items():
                        if data.get('processed',False) not in ['added']:
                            continue
                        catalog_fp.write(
                '{path}\t{signature}\n'.format(
                        path=os.path.join(directory, file_name),
                        signature=self._catalog_data[directory][file_name]['signature']))
        except IOError as e:
                six.raise_from(CatalogError(
                    'Error opening/writing catalog file : \'{}\' - {}'.format(
                        self._catalog_name, str(e))), None)

    def abs_path(self, rel_path):
        """Return an absolute path from a relative path based from the given root"""
        return os.path.join(self._root, rel_path)

    def walk(self):
        """ Progress through the directory tree

            Filtering out files not required
            yield the path of the file relative to self._root
            Used during the check and create process
        """
        for directory, sub_directories, files in os.walk(self._root):

            # Don't recurse into directories that should be ignored
            if self.abs_path(directory) == self.abs_path(self._root):
                sub_directories[:] = [sub for sub in sub_directories if
                                      sub not in self._ignore_directories]

            process_files = [file_name for file_name in files if
                             self._is_file_to_be_processed(directory,
                                                           file_name)]
            if process_files:
                yield os.path.relpath(directory, self._root), process_files

            # After yielding Look at every file and record those as excluded
            # Assumes that the consumer code records each file in some way
            for file_name in files:
                if file_name not in process_files:
                    self.record_excluded(directory, file_name)

    def is_file_in_catalog(self, file_path):
        """Return True if this directory and file is in the loaded catalog"""
        directory, file_name = os.path.split(file_path)
        return directory in self._catalog_data and \
               file_name in self._catalog_data.get(directory, {})

    def is_directory_in_catalog(self, directory):
        """Return True if this directory is in the loaded catalog"""
        return directory in self._catalog_data

    def get_non_processed(self, directory):
        """Whether this file has been processed by the checking procedure

           Only return False if the file data is in the catalog
           but hasn't been processed

           if the directory is missing from the catalog - then
           this directory is deliberately omitted

           if the file is in catalog then look at the 'processed' key ...
        """
        for file_name in self._catalog_data.get(directory, []):
            if not self._catalog_data[directory][file_name].get(
                    'processed', False):
                yield file_name

    def get_signature(self, rel_path=None, from_catalog=False):
        """Generate or fetch the signature for the given path

           :param rel_path: The relative path from this current directory
                    to the file
           :param from_catalog: Boolean - whether to fetch the data from
                    the catalog file.

            if from_catalog is True this fetches the signature for this file from
            the catalog file.

            if from_catalog is False this will generate the signature based
            on the file content
        """
        if from_catalog:
            directory, name = os.path.split(rel_path)
            if directory not in self._catalog_data or name not in \
                    self._catalog_data[directory]:
                return None

            return self._catalog_data[directory][name]['signature'].strip()

        abs_path = self.abs_path(rel_path)

        m = hashlib.new(self._hash)
        try:
            with open(abs_path, 'rb') as f:
                m.update(f.read())
        except BaseException as e:
            sys.stderr.write(
                "Error creating signature for '{}': {}\n".format(abs_path, e))
            return None
        return m.hexdigest().strip()

    def _path_rel_to_root(self, abspath):
        return os.path.relpath(abspath, self._root)

    def _mark_processed(self, rel_path, status='processed'):
        """Mark a file as having been processed"""
        if status not in ['excluded']:
            self._record_extension(rel_path)
        directory, file_name = os.path.split(rel_path)
        self._catalog_data.setdefault(directory, {})
        self._catalog_data[directory].setdefault(file_name, {})
        self._catalog_data[directory][file_name]['processed'] = status

    def record_ok(self, rel_path):
        self._mark_processed(rel_path=rel_path, status='processed')

    def record_excluded(self, directory, file_name):
        """Count the and Record the excluded files"""

        # Don't record the catalog file itself as being excluded
        if (self.abs_path(directory) == self.abs_path(self._root) and
                file_name == self._catalog_name):
            return

        self._excluded_file_count += 1

        self._mark_processed(os.path.join(directory, file_name), 'excluded')

    def record_missing(self, rel_path):
        self._mark_processed(rel_path, 'missing')

    def record_extra(self, rel_path):
        self._mark_processed(rel_path, 'extra')

    def record_mismatch(self, rel_path):
        self._mark_processed(rel_path, 'mismatch')