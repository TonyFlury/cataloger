#!/usr/bin/env python
# coding=utf-8
"""
# cataloger : Implementation of cataloger.py

Summary : 
    <summary of module/class being implemented>
Use Case : 
    As a <actor> I want <outcome> So that <justification>

Testable Statements :
    Can I <Boolean statement>
    ....
"""

import unittest
import sys
import re
import inspect
import click
import click.testing
import six
import hashlib
import os
import errno

# noinspection PyPackageRequirements
# Only needed for testing see test_requirements.txt & test27_requirements.txt
from pyfakefs.fake_filesystem_unittest import Patcher

import cataloger.processor as processor
import cataloger.defaults as defaults
import cataloger.commands as commands
import cataloger.main as cli_main

import pkg_resources

from tests.new_mock_open import new_mock_open

import six

if six.PY2:
    # noinspection PyPackageRequirements
    # mock is a separate package for Python2.7 - see test27_requirements.txt
    from mock import patch, mock_open, MagicMock, call
else:
    from unittest.mock import patch, mock_open, MagicMock, call

# noinspection Annotator
try:
    import builtins
except ImportError:
    import __builtin__ as builtins

def get_sig(data, hash='sha224'):
    return hashlib.new(hash, bytearray(data, 'utf-8')).hexdigest()


class OrderedTestSuite(unittest.TestSuite):
    def __iter__(self):
        return iter(sorted(self._tests, key=lambda x:str(x)))


class TestCatalogerCreation(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_000_000_basic_creation(self):
        """Test the basic creation of the Cataloger"""

        # Use fake file system so don't clash with any catalog.cfg written
        with Patcher() as patch:
            cat = processor.Cataloger(action='create')
            self.assertEqual(cat._catalog_name, defaults.DEFAULT_CATALOG_FILE)
            self.assertEqual(cat._verbose, defaults.DEFAULT_VERBOSE)
            self.assertEqual(cat._hash, defaults.DEFAULT_HASH)
            self.assertEqual(cat._root, '.' )
            self.assertEqual(cat._report_excluded, 'report_excluded' in defaults.DEFAULT_REPORTON)
            self.assertEqual(cat._report_extension, defaults.DEFAULT_REPORT_EXTENSIONS)
            self.assertEqual(cat._group, defaults.DEFAULT_REPORT_GROUP)
            self.assertEqual(cat._extensions, defaults.DEFAULT_EXTENSIONS)
            self.assertEqual(cat._ignore_directories, defaults.DEFAULT_IGNOREDIRECTORY)

    def test_000_001_start_create_command(self):
        """Test the start command"""
        with patch('cataloger.processor.open', mock_open()) as m:
            cat = processor.Cataloger(action='create')
            m.assert_called_once_with(defaults.DEFAULT_CONFIG_FILE,'r')

    def test_000_002_start_check_command(self):
        """Test the start command - empty catalog"""
        with patch('cataloger.processor.open', MagicMock(name='open')) as m:
            m.return_value = MagicMock(name='file')
            with six.assertRaisesRegex(self, processor.CatalogError, r'Empty catalog file : catalog\.cat'):
                cat = processor.Cataloger(action='check')
            m.assert_has_calls([call(defaults.DEFAULT_CATALOG_FILE, 'r'), call(defaults.DEFAULT_CONFIG_FILE, 'r')], any_order=True)
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or ('__enter__' in call_names and '__exit__' in call_names))

    def test_000_003_config_default_notthere(self):
        """No Explicit config file parameter, no default config - no warning"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            with patch('sys.stderr', six.StringIO()) as stderr:
                cat= processor.Cataloger()
                self.assertEqual(stderr.getvalue(), '')

    def test_000_003e_config_explicit_notthere(self):
        """Explicit config file parameter, no config file, warning generated"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            with patch('sys.stderr', six.StringIO()) as stderr:
                cat= processor.Cataloger(config=defaults.DEFAULT_CONFIG_FILE)
                six.assertRegex(self, stderr.getvalue(), 'Warning : Unable to open config file \'catalog.cfg\'; continuing with defaults')

    def test_000_004_config_default_noperm(self):
        """No Explicit config file parameter, config file exists but no perm"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE)
            os.chmod('/tmp/catalog.cfg', 0o007)
            with patch('sys.stderr', six.StringIO()) as stderr:
                with six.assertRaisesRegex(self, processor.ConfigError, r'Permission denied'):
                    cat= processor.Cataloger()

    def test_000_005_config_explicit_noperm(self):
        """Explicit config file parameter, config file exists but no perm"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE)
            os.chmod('/tmp/catalog.cfg', 0o007)
            with patch('sys.stderr', six.StringIO()) as stderr:
                with six.assertRaisesRegex(self, processor.ConfigError, r'Permission denied'):
                    cat= processor.Cataloger(config=defaults.DEFAULT_CONFIG_FILE)

    def test_000_006_config_odd_exception(self):
        """Explicit config file parameter, config file exists but no perm"""
        with patch('cataloger.processor.open', MagicMock() ) as m:
            m.side_effect = TypeError('What an odd Error')
            with six.assertRaisesRegex(self, processor.ConfigError, r'Unable to read config file \'catalog\.cfg\' : What an odd Error'):
                    cat= processor.Cataloger(config=defaults.DEFAULT_CONFIG_FILE)

    def test_000_010_new_mock_open(self):
        data = 'this is data\nspread over many lines\nto see if \n iter will work'
        if six.PY3:
            open_name = 'builtins.open'
        else:
            open_name = '__builtin__.open'
        with patch(open_name, new_mock_open(read_data=data)) as m:
            with open('a.b', 'r') as fp:
                self.assertEqual([i for i in six.StringIO(data)], [x for x in fp])

    def test_000_023_check_command_nonempty_catalog(self):
        """Test the start command"""
        catalog = """a.py\t787908798d
b.py\t787787ef7e
c.py\t7898798acd"""
        with patch('cataloger.processor.open', new_mock_open(read_data=catalog)) as m:
            cat = processor.Cataloger(action='check', no_config=True)
            m.assert_called_once_with(defaults.DEFAULT_CATALOG_FILE, 'r')
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or ('__enter__' in call_names and '__exit__' in call_names))

    def test_000_030_start_invalid_command(self):
        """Test the start command"""
        with six.assertRaisesRegex(self, ValueError,r'foobar'):
            cat = processor.Cataloger(action='foobar')

    def test_000_031_empty_extension_list(self):
        """Instantiate Command catironment with empty extension list"""
        with six.assertRaisesRegex(self, processor.CatalogError, r'No file extensions given to catalogue or check'):
            cat = processor.Cataloger(extensions=[])

class TestSignatureCreation(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_010_000_default_hash(self):
        """Assume a default command - i.e. no arguments other than create"""

        sample_text = b'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        cmd = processor.Cataloger(action='create')

        with patch('cataloger.processor.open',
                   mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_has_calls([call('./a.py', 'rb')])
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or
                             ('__enter__' in call_names and '__exit__' in call_names))

        non_lib_sig = hashlib.new(defaults.DEFAULT_HASH)
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())

    def test_010_001_sha1_hash_creation(self):
        """Assume a explicit create an sha1 hash"""

        sample_text = b'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        cmd = processor.Cataloger(action='create', hash='sha1')

        with patch('cataloger.processor.open',
                   mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_has_calls([call('./a.py', 'rb')])
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or
                             ('__enter__' in call_names and '__exit__' in call_names))

        non_lib_sig = hashlib.new('sha1')
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())

    def test_010_002_sha224_hash_creation(self):
        """Assume a explicit create an sha224 hash"""

        sample_text = b'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        cmd = processor.Cataloger(action='create', hash='sha224')

        with patch('cataloger.processor.open',
                   mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_has_calls([call('./a.py', 'rb')])
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or
                             ('__enter__' in call_names and '__exit__' in call_names))

        non_lib_sig = hashlib.new('sha224')
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())

    def test_010_003_sha384_hash_creation(self):
        """Explicit create an sha384 hash"""
        cmd = processor.Cataloger(hash='sha384')
        sample_text = b'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        with patch('cataloger.processor.open',
                   mock_open(read_data=sample_text,)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_has_calls([call('./a.py', 'rb')])
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or
                             ('__enter__' in call_names and '__exit__' in call_names))

        non_lib_sig = hashlib.new('sha384')
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())

    def test_010_010_hash_creation_error_on_open(self):
        """Generate an error while opening a file to create a hash"""
        cmd = processor.Cataloger(hash='sha384')
        sample_text = b'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        with patch('cataloger.processor.open',
                   mock_open(read_data=sample_text)) as m:
            with patch('cataloger.processor.sys.stderr', six.StringIO()) as err:
                m.side_effect = IOError(errno.EPERM,'No permission')
                this_signature = cmd.get_signature('a.py')
                self.assertEqual(err.getvalue(),'Error creating signature for '
                                                '\'./a.py\': [Errno 1] No permission\n')
                m.assert_has_calls([call('./a.py', 'rb')])
                # Exception will be raised on open - so no need to test for closure

    def test_010_012_hash_creation_error_on_read(self):
        """Generate an error while reading a file to create a hash"""
        cmd = processor.Cataloger(hash='sha384')
        sample_text = b'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        with patch('cataloger.processor.open',
                   mock_open(read_data=sample_text)) as m:
            with patch('cataloger.processor.sys.stderr', six.StringIO()) as err:
                m.return_value.read.side_effect = IOError(errno.ENOMEM,'Out of Memory')
                this_signature = cmd.get_signature('a.py')
                self.assertEqual(err.getvalue(),'Error creating signature for '
                                                '\'./a.py\': [Errno 12] Out of Memory\n')
                m.assert_has_calls([call('./a.py', 'rb')])
                m.return_value.read.assert_called_once_with()
                call_names = set(x[0] for x in m.return_value.mock_calls)
                self.assertTrue( 'close' in call_names or
                                 ('__enter__' in call_names and '__exit__' in call_names))

class TestWalk(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_020_000_WalkFlatDirectoryNoExclusions(self):
        """Test the walk function returns lists of files as appropriate with a flat directory"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')

            cat = processor.Cataloger()
            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py']})
        self.assertEqual(len(cat.excluded_files), 0)

    def test_020_001_WalkFlatDirectoryExclusions(self):
        """Test the walk function returns lists of files as appropriate with a flat directory with a file excluded"""
        dir = {}
#        self.maxDiff = None

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t1.pyc')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE)

            cat = processor.Cataloger()

            six.assertCountEqual(self, os.listdir(os.getcwd()), [defaults.DEFAULT_CATALOG_FILE, 't1.py', 't2.py', 't1.pyc'])

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py']})
        self.assertEqual(len(cat.excluded_files), 1) # catalog.cat isn't counted

    def test_020_002_WalkFlatDirectoryMultipleExclusions(self):
        """Test the walk function returns lists of files as appropriate with a flat directory with multiple file excluded"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')
            cat = processor.Cataloger()
            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t1.pyc')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('t2.pyc')

            six.assertCountEqual(self,os.listdir(os.getcwd()),['t1.py','t2.py','t1.pyc','t2.pyc'])

            for directory, files in cat.walk():
                dir[directory] = files

            six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py']})
            self.assertEqual(len(cat.excluded_files), 2)

    def test_020_010_Walk2DeepMultipleExclusions(self):
        """walk recurses into directories"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger()

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('t1.pyc')
            patcher.fs.CreateFile('t2.pyc')

            patcher.fs.CreateFile('test/test.py')
            patcher.fs.CreateFile('test/test.pyc')

            six.assertCountEqual(self,os.listdir(os.getcwd()),['test', 't1.py','t2.py','t1.pyc','t2.pyc'])
            six.assertCountEqual(self,os.listdir('/tmp/test'),['test.py','test.pyc'])

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['test.py']})
        self.assertEqual(len(cat.excluded_files), 3)

    def test_020_020_WalkExcludedDirectories(self):
        """walk method excluding the right directories"""

        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger()

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/test.py')

            for d in defaults.DEFAULT_IGNOREDIRECTORY:
                patcher.fs.CreateDirectory(os.path.join('/tmp',d))

            six.assertCountEqual(self,os.listdir(os.getcwd()), ['test', 't1.py','t2.py'] + list(defaults.DEFAULT_IGNOREDIRECTORY) )
            six.assertCountEqual(self,os.listdir('/tmp/test'),['test.py'])

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['test.py']})
        self.assertEqual(len(cat.excluded_files), 0)

    def test_020_050_single_exclude_filter_no_match(self):
        """Single filter argument, which shouldn't match anything"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(exclude_filter=['*wibble*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/test.py')
            patcher.fs.CreateFile('test/flump/test.py')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['test.py'], 'test/flump':['test.py']})
        self.assertEqual(len(cat.excluded_files), 0)

    def test_020_051_single_exclude_filter_match_file(self):
        """Single filter argument, which will match one file"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(exclude_filter=['*/tike.py'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/tike.py')
            patcher.fs.CreateFile('test/flump/test.py')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'], 'test/flump':['test.py']})
        self.assertEqual(len(cat.excluded_files), 1)

    def test_020_052_single_exclude_filter_match_directory(self):
        """Single filter argument, which will match one subdirectory"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(exclude_filter=['test/flump/*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/t1.py')
            patcher.fs.CreateFile('test/flump/test.py')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['t1.py']})
        self.assertEqual(len(cat.excluded_files), 1)

    def test_020_054_multiple_exclude_filters_no_matches(self):
        """Multiple filters which match nothing"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(exclude_filter=['*wibble*', '*wobble*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/t1.py')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['t1.py']})
        self.assertEqual(len(cat.excluded_files), 0)

    def test_020_056_multiple_exclude_filters_one_match(self):
        """Multiple filters where one places matches"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(exclude_filter=['*wibble*', '*/a?.*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/a1.py')
            patcher.fs.CreateFile('test/a3a.py')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['a3a.py']})
        self.assertEqual(len(cat.excluded_files), 1)

    def test_020_058_multiple_exclude_filters_multiple_match(self):
        """Multiple filters where one places matches"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(exclude_filter=['*wibble*', '*/a?.*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/a1.py')
            patcher.fs.CreateFile('test/a2.py')
            patcher.fs.CreateFile('test/a3a.py')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['a3a.py']})
        self.assertEqual(len(cat.excluded_files), 2)


    def test_020_060_single_include_filter_no_match(self):
        """Single filter argument, which shouldn't match anything"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(include_filter=['*wibble*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/test.py')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{})
        self.assertEqual(len(cat.excluded_files), 3)

    def test_020_061_single_include_filter_match_file(self):
        """Single filter argument, which will match one file"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(include_filter=['*/tike.py'])

            patcher.fs.CreateFile('tike.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/tike.py')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['tike.py'],'test':['tike.py']})
        self.assertEqual(len(cat.excluded_files), 1)

    def test_020_062_single_include_filter_match_directory(self):
        """Single filter argument, which will match one or more directories"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(include_filter=['test/*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/t1.py')
            patcher.fs.CreateFile('test/content/t1.py')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'test':['t1.py'], 'test/content':['t1.py']})
        self.assertEqual(len(cat.excluded_files), 2)

    def test_020_064_multiple_include_filters_no_matches(self):
        """Multiple filters which match nothing"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(include_filter=['*wibble*', '*wobble*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/t1.py')

            for directory, files in cat.walk():
                dir[directory] = files
        six.assertCountEqual(self,dir,{})
        self.assertEqual(len(cat.excluded_files), 3)

    def test_020_066_multiple_include_filters_one_match(self):
        """Multiple filters where one places matches"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(include_filter=['*wibble*', '*/a?.*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('a1.py')
            patcher.fs.CreateFile('test/a1.py')
            patcher.fs.CreateFile('test/a3a.py')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.':['a1.py'],'test':['a1.py']})
        self.assertEqual(len(cat.excluded_files), 3)

    def test_020_068_multiple_include_filters_multiple_match(self):
        """Root which is different from cwd
        """
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            cat = processor.Cataloger(include_filter=['test/*.*', '*/t?.*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/a1.py')
            patcher.fs.CreateFile('test/a2.py')
            patcher.fs.CreateFile('test/a3a.py')
            patcher.fs.CreateFile('test/t2.txt')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['a1.py', 'a2.py','a3a.py','t2.txt']})
        self.assertEqual(len(cat.excluded_files), 0)

    def test_020_070_walk_non_default_root(self):
        """Walk a directory structure offset from cwd
        """
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')


            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/a1.py')
            patcher.fs.CreateFile('test/a2.py')
            patcher.fs.CreateFile('test/a3a.py')
            patcher.fs.CreateFile('test/t2.txt')

            cat = processor.Cataloger(root='test')

            for directory, files in cat.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.':['a1.py', 'a2.py','a3a.py','t2.txt']})
        self.assertEqual(len(cat.excluded_files), 0)

class HelperFunctions(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_030_000_load_catalog(self):
        """Load Catalog"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('/tmp/catalog.cat', contents="""a.py\t889898aa898a1
b.py\t889898aa898a2
c.py\t889898aa898a3
sub/a1.py\t889898aa898a4""")
            cat = processor.Cataloger(action='check')

        self.assertTrue(cat.is_file_in_catalog('./a.py'))
        self.assertTrue(cat.is_file_in_catalog('./b.py'))
        self.assertTrue(cat.is_file_in_catalog('./c.py'))
        self.assertTrue(cat.is_file_in_catalog('sub/a1.py'))
        self.assertFalse(cat.is_file_in_catalog('test.py'))
        self.assertEqual(cat.processed_count, 4)

    def test_030_002_load_non_existant_catalog(self):
        """Attempt to load catalog file which doesn't exist"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            with six.assertRaisesRegex(self, processor.CatalogError, r'No such file or directory'):
                cat = processor.Cataloger(action='check')

    def test_030_003_load_catalog_no_permission_read(self):
        """Attempt to load catalog file which doesn't exist"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            cat = patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents='')
            os.chmod('/tmp/catalog.cat', mode=int('077',8))

            with six.assertRaisesRegex(self, processor.CatalogError, r'Permission denied'):
                cat = processor.Cataloger(action='check')

    def test_030_010_get_signature_from_catalog(self):
        """Load Catalog & fetch signature from catalog"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""a.py\t889898aa898a1
b.py\t889898aa898a2
c.py\t889898aa898a3
sub/a1.py\t889898aa898a4""")

            cat = processor.Cataloger(catalog='/tmp/catalog.cat', action='check')

            self.assertEqual(cat.get_signature('./a.py', from_catalog=True), '889898aa898a1')
            self.assertEqual(cat.get_signature('./b.py', from_catalog=True), '889898aa898a2')
            self.assertEqual(cat.get_signature('./c.py', from_catalog=True), '889898aa898a3')
            self.assertEqual(cat.get_signature('sub/a1.py', from_catalog=True), '889898aa898a4')
            self.assertIsNone(cat.get_signature('./test.py',
                                                from_catalog=True))

    def test_030_011_get_signature_from_catalog_blank_lines(self):
        """Load Catalog & fetch signature from catalog - ignore blank lines"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""
a.py\t889898aa898a1

b.py\t889898aa898a2

c.py\t889898aa898a3

sub/a1.py\t889898aa898a4""")

            cat = processor.Cataloger(catalog='/tmp/catalog.cat', action='check')

            self.assertEqual(cat.get_signature('./a.py', from_catalog=True),
                             '889898aa898a1')
            self.assertEqual(cat.get_signature('./b.py', from_catalog=True),
                             '889898aa898a2')
            self.assertEqual(cat.get_signature('./c.py', from_catalog=True),
                             '889898aa898a3')
            self.assertEqual(cat.get_signature('sub/a1.py', from_catalog=True),
                             '889898aa898a4')
            self.assertIsNone(cat.get_signature('./test.py', from_catalog=True))

    def test_030_012_load_catalog_empty(self):
        """Load Catalog & fetch signature from catalog - ignore blank lines"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents='')
            with six.assertRaisesRegex(self, processor.CatalogError, 'Empty catalog'):
                cat = processor.Cataloger(
                    catalog='/tmp/catalog.cat', action='check')

    def test_030_013_load_catalog_invalid_missing_tab(self):
        """Load Catalog & fetch signature from catalog - ignore blank lines"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""
a.py\t889898aa898a
b.py 889898aa898a
""")
            with six.assertRaisesRegex(self, processor.CatalogError, 'Invalid catalog format - missing tab on line 2'):
                cat = processor.Cataloger(
                    catalog='/tmp/catalog.cat', action='check')

    def test_030_014_load_catalog_invalid_signature(self):
        """Load Catalog & fetch signature from catalog - invalid signature hex string"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""
a.py\tWibbleZibble 
b.py\t889898aa898a
""")
            with six.assertRaisesRegex(self, processor.CatalogError,
                                       'Invalid catalog format - invalid signature on line 1'):
                cat = processor.Cataloger(
                    catalog='/tmp/catalog.cat', action='check')

    def test_030_020_record_extra(self):
        """functionality of record_extra method"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""
            a.py\t889898aa898a 
            b.py\t889898aa898a
            """)
            cat = processor.Cataloger(action='check')

            cat.record_extra('./y.py')
            cat.record_extra('./z.py')

        six.assertCountEqual(self,cat.extra_files,['y.py','z.py'])
        self.assertEqual(cat.extension_counts, {'.py':2})

    def test_030_021_record_mismatch(self):
        """functionality of record_mismatch method"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""
            a.py\t889898aa898a 
            b.py\t889898aa898a
            """)
            cat = processor.Cataloger(action='check')

            cat.record_mismatch('./a.py')
            cat.record_mismatch('./c.py')

        six.assertCountEqual(self,cat.mismatched_files,['a.py','c.py'])
        self.assertEqual(cat.extension_counts, {'.py':2})

    def test_030_022_record_missing(self):
        """functionality of record_missing method"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""
            a.py\t889898aa898a 
            b.py\t889898aa898a
            test/c.py\t7878abbabba
            """)
            cat = processor.Cataloger(action='check', root='/tmp')

            cat.record_missing('./a.py')
            cat.record_missing('test/c.py')

        six.assertCountEqual(self,cat.missing_files,['a.py','test/c.py'])
        self.assertEqual(cat.extension_counts, {'.py':2})

    def test_030_040_catalog_write(self):
        """Catalog_write with faked file and signature"""
        with Patcher() as patcher:
            file_name = './a.py'
            signature = 'bbacdss3'
            os.chdir('/tmp')
            cat = processor.Cataloger(action='create', verbose=0)
            cat.add_to_catalog(file_name, signature)
            self.assertEqual(cat.processed_count, 1)

            with patch('cataloger.processor.open', mock_open()) as m:
                cat.write_catalog()
                m.assert_has_calls([call(defaults.DEFAULT_CATALOG_FILE, 'w')], any_order=True)
                call_names = set(x[0] for x in m.return_value.mock_calls)
                self.assertTrue(
                        'close' in call_names or
                         ('__enter__' in call_names and '__exit__' in call_names))

                m.return_value.write.assert_has_calls([call('{}\t{}\n'.format(file_name, signature))])

    def test_030_045_catalog_open_error(self):
        """Catalog_write an error"""
        sig = hashlib.new('sha224',bytearray('a.py','utf-8')).hexdigest()
        cat = processor.Cataloger(action='create', verbose=0)
        cat.add_to_catalog('a.py', sig)
        self.assertEqual(cat.processed_count, 1)

        with patch('cataloger.processor.open', mock_open()) as m:
            m.side_effect = IOError(errno.EISDIR,'Is a directory')
            with six.assertRaisesRegex(self, processor.CatalogError,
                    r'Error opening/writing catalog file : \'catalog.cat\' - \[Errno 21\] Is a directory'):
                cat.write_catalog()
            m.assert_has_calls([call(defaults.DEFAULT_CATALOG_FILE, 'w')], any_order=True)

    def test_030_047_catalog_write_error(self):
        """Catalog_write an error"""
        sig = hashlib.new('sha224',bytearray('a.py','utf-8')).hexdigest()
        cat = processor.Cataloger(action='create', verbose=0)
        cat.add_to_catalog('a.py', sig)
        self.assertEqual(cat.processed_count, 1)

        with patch('cataloger.processor.open', mock_open()) as m:
            m.return_value.write.side_effect = IOError(errno.ENOSPC,'The disk is full')
            with six.assertRaisesRegex(self, processor.CatalogError,
                    r'Error opening/writing catalog file : \'catalog.cat\' - \[Errno 28\] The disk is full'):
                cat.write_catalog()

            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue(
                'close' in call_names or
                ('__enter__' in call_names and '__exit__' in call_names))

    def test_030_050_get_non_processed(self):
        """Test get_non_processed helper function"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""a.py\t787908798d
        b.py\t787787ef7e
        c.py\t7898798acd
        test/d.py\t7979abbde""")
            cat = processor.Cataloger(action='check')
            cat.record_missing('./b.py')
            self.assertEqual([f for f in cat.get_non_processed('test')],['d.py'])
            six.assertCountEqual(self, [f for f in cat.get_non_processed('.')],['a.py','c.py'])

    def test_030_060_is_directory_in_catalog(self):
        """Test is_directory_in_catalog helper function"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""a.py\t787908798d
        b.py\t787787ef7e
        c.py\t7898798acd
        test/d.py\t7979abbde""")
            cat = processor.Cataloger(action='check')
            self.assertTrue(cat.is_directory_in_catalog('test'))
            self.assertFalse(cat.is_directory_in_catalog('src'))

    def test_030_070_is_file_in_catalog(self):
        """Test is_file_in_catalog helper function"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""a.py\t787908798d
        b.py\t787787ef7e
        c.py\t7898798acd
        test/d.py\t7979abbde""")
            cat = processor.Cataloger(action='check')
            self.assertTrue(cat.is_file_in_catalog('test/d.py'))
            self.assertTrue(cat.is_file_in_catalog('./a.py'))
            self.assertTrue(cat.is_file_in_catalog('./b.py'))
            self.assertFalse(cat.is_file_in_catalog('a.pyc'))
            self.assertFalse(cat.is_file_in_catalog('a.py'))

@unittest.skip
class FinalReport(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_040_000_check_missing(self):
        """Test that missing files are reported correctly in the final report"""
        output = six.StringIO()
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""
        a.py\t3765aaababba 
        b.py\t889898aa898a
        """)
            cat = processor.Cataloger(catalog='/tmp/catalog.cat', output=output, action='check')
            cat.record_missing('test/a.py')
            cat.record_missing('test/a.html')
            cat.final_report()
            m = re.search(r'2 missing files', output.getvalue())

            self.assertTrue(re.search( r'\ttest/a\.py\n', output.getvalue()[m.end():]))
            self.assertTrue(re.search( r'\ttest/a\.html\n', output.getvalue()[m.end():]))

            m = re.search(r'Processed by file type\n', output.getvalue())
            self.assertTrue(re.search(r'\t\'.py\' : 1\n', output.getvalue()[m.end():]))
            self.assertTrue(re.search(r'\t\'.html\' : 1\n', output.getvalue()[m.end():]))


    def test_040_001_check_extra(self):
        """Test that extra files are reported correctly in the final report"""
        output = six.StringIO()
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""
        a.py\t3765aaababba 
        b.py\t889898aa898a
        """)
            cat = processor.Cataloger(catalog='/tmp/catalog.cat', output=output, action='check')
            cat.record_extra('test/a.js')
            cat.record_extra('test/a.html')
            cat.final_report()
            m = re.search(r'2 extra files\n', output.getvalue())

            self.assertTrue(re.search(r'\ttest/a\.js\n', output.getvalue()[m.end():]))
            self.assertTrue(re.search(r'\ttest/a\.html\n', output.getvalue()[m.end():]))

            m = re.search(r'Processed by file type\n', output.getvalue())
            self.assertTrue(re.search(r'\t\'.js\' : 1\n', output.getvalue()[m.end():]))
            self.assertTrue(re.search(r'\t\'.html\' : 1\n', output.getvalue()[m.end():]))

    def test_040_003_check_mimatched(self):
        """Test that mismatched files are reported correctly in the final report"""
        output = six.StringIO()
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CATALOG_FILE, contents="""
        a.py\t3765aaababba 
        b.py\t889898aa898a
        """)
            cat = processor.Cataloger(catalog='/tmp/catalog.cat', output=output, action='check')
            cat.record_mismatch('test/a.js')
            cat.record_mismatch('test/a.html')
            cat.final_report()
            m = re.search(r'2 files with mismatched signature', output.getvalue())

            self.assertTrue(re.search(r'\ttest/a\.js\n', output.getvalue()[m.end():]))
            self.assertTrue(re.search(r'\ttest/a\.html\n', output.getvalue()[m.end():]))

            m = re.search(r'Processed by file type\n', output.getvalue())
            self.assertTrue(re.search(r'\t\'.js\' : 1\n', output.getvalue()[m.end():]))
            self.assertTrue(re.search(r'\t\'.html\' : 1\n', output.getvalue()[m.end():]))


class TestCatalogConfig(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_000_catalog_line_present(self):
        """Test that the catalog section with a catalog= line is captured correctly"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [catalog]
    catalog=Catalog.mft
        """)
            cat = processor.Cataloger()
            cat._process_config()
            self.assertEqual(cat.catalog_file_name,'Catalog.mft')
            self.assertEqual(cat._hash, 'sha224')
            self.assertEqual(cat._root, '.')
            six.assertCountEqual(self, cat._extensions, defaults.DEFAULT_EXTENSIONS)

    def test_050_001_hash_line_present(self):
        """Test that the catalog section with a hash= line is captured correctly"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [catalog]
    hash=sha1
        """)
            cat = processor.Cataloger()
            self.assertEqual(cat.catalog_file_name, defaults.DEFAULT_CATALOG_FILE)
            self.assertEqual(cat._hash, 'sha1')
            self.assertEqual(cat._root, '.')
            six.assertCountEqual(self, cat._extensions, defaults.DEFAULT_EXTENSIONS)

    def test_050_001_root_line_present(self):
        """Test that the catalog section with a root= line is captured correctly"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [catalog]
    root=src
        """)
            cat = processor.Cataloger()
            self.assertEqual(cat.catalog_file_name, defaults.DEFAULT_CATALOG_FILE)
            self.assertEqual(cat._hash, 'sha224')
            self.assertEqual(cat._root, 'src')
            six.assertCountEqual(self, cat._extensions, defaults.DEFAULT_EXTENSIONS)

    def test_050_010_invalid_hash(self):
        """Test that the catalog section with an invalid hash value is detected"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [catalog]
    hash = gibberish
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value for hash : \'hash = gibberish\' on line 2'):
                cat = processor.Cataloger()

    def test_050_010_invalid_option(self):
        """Test that the catalog section with an invalid option name"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [catalog]
    extension=.py
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid config line in section \[catalog\] : \'extension=.py\' on line 2'):
                cat = processor.Cataloger()

    def test_050_020_comment_and_blank(self):
        """Test that the catalog section handles blank lines and comments"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        # Define the general catalog data
        [catalog]
        catalog=Catalog.man
        
        # Change the hash value
        hash=md5
        
        root=src
            """)
            cat = processor.Cataloger()
            self.assertEqual(cat.catalog_file_name, 'Catalog.man')
            self.assertEqual(cat._hash, 'md5')
            self.assertEqual(cat._root, 'src')

class TestExtensionConfig(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_100_equal(self):
        """Test that the extension section with an = operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    =.py,.html,.js
        """)
            cat = processor.Cataloger()
            six.assertCountEqual(self, cat._extensions, ['.py','.html','.js'])

    def test_050_101_minus(self):
        """Test that the extension section with an - operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    - .py,.html,.js
        """)
            cat = processor.Cataloger()
            six.assertCountEqual(self, cat._extensions, defaults.DEFAULT_EXTENSIONS - {'.py','.html','.js'} )

    def test_050_102_plus(self):
        """Test that the extension section with an + operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    + .jsx, .cfg, .com
        """)
            cat = processor.Cataloger()
            six.assertCountEqual(self, cat._extensions, defaults.DEFAULT_EXTENSIONS | {'.jsx', '.cfg', '.com'})

    def test_050_110_invalid_operator(self):
        """Test that the extension section with an invalid operator is correctly detected"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    * .jsx, .cfg, .com
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid operator in \[extension\] section : \'\* \.jsx, \.cfg, \.com\' on line 2'):
                cat = processor.Cataloger()

    def test_050_115_invalid_extension_missing_dot(self):
        """Test that the extension section with an extension missing a dot"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    + .jsx, .cfg, com
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[extension\] section : \'\+ \.jsx, \.cfg, com\' on line 2'):
                cat = processor.Cataloger()

    def test_050_115_invalid_extensions_null_string(self):
        """Test that the extension section with an null string extension"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    + .jsx, , .com
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[extension\] section : \'\+ \.jsx, , \.com\' on line 2'):
                cat = processor.Cataloger()

    def test_050_115_invalid_extensions_dot_only(self):
        """Test that the extension section with an extension which is just a dot"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    + .jsx, . , .com
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[extension\] section : \'\+ \.jsx, \. , \.com\' on line 2'):
                cat = processor.Cataloger()

    def test_050_120_empty_list_equal(self):
        """Test that a single equal in the extensions area sets the list empty"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    =
        """)
            with six.assertRaisesRegex(self, processor.CatalogError, r'No file extensions given to catalogue or check'):
                cat = processor.Cataloger()

    def test_050_122_empty_list_equal_with_and(self):
        """Test that a single equal in the extensions area sets the list empty"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    =
    + .py
        """)
            cat = processor.Cataloger()
            self.assertEqual(cat._extensions,{'.py'})

    def test_050_124_empty_list_add(self):
        """Test that the a single + is errored"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    +
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[extension\] section : \'\+\' on line 2'):
                cat = processor.Cataloger()

    def test_050_126_empty_list_minus(self):
        """Test that a single - is errored"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [extensions]
    -
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[extension\] section : \'\-\' on line 2'):
                cat = processor.Cataloger()

class TestDirectoryConfig(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_200_equal(self):
        """Test that the directories section with an = operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [directories]
    = docs, src, coverage
        """)
            cat = processor.Cataloger()
            six.assertCountEqual(self, cat._ignore_directories, {'docs', 'src', 'coverage'} )

    def test_050_201_minus(self):
        """Test that the directories section with an - operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [directories]
    - static, htmlcov, docs
        """)
            cat = processor.Cataloger()
            six.assertCountEqual(self, cat._ignore_directories, defaults.DEFAULT_IGNOREDIRECTORY - {'static', 'htmlcov', 'docs'} )

    def test_050_202_plus(self):
        """Test that the directories section with an + operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [directories]
    + build, dist
        """)
            cat = processor.Cataloger()
            six.assertCountEqual(self, cat._ignore_directories, defaults.DEFAULT_IGNOREDIRECTORY | {'build', 'dist'} )

    def test_050_210_invalid_operator(self):
        """Test that the directories section with an invalid operator is correctly detected"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [directories]
    * build, dist
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid operator in \[directories\] section : \'\* build, dist\' on line 2'):
                cat = processor.Cataloger()

    def test_050_215_null_string(self):
        """Test that the directories section with an null string directories"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [directories]
    + build, , dist
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[directories\] section : \'\+ build, , dist\' on line 2'):
                cat = processor.Cataloger()

    def test_050_216_empty_list(self):
        """directories section with = and no value list"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [directories]
    =
        """)
            cat = processor.Cataloger()
            self.assertEqual(cat._ignore_directories,set())


    def test_050_220_empty_list_add(self):
        """directories section with + and no value list"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [directories]
    +
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[directories\] section : \'\+\' on line 2'):
                cat = processor.Cataloger()

    def test_050_225_empty_list_minus(self):
        """directories section with - and no value list"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [directories]
    -
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[directories\] section : \'\-\' on line 2'):
                cat = processor.Cataloger()

class TestFilterConfig(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_300_include_line_present(self):
        """Test that the filters section with a includ = line"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [filters]
    include = *test*, splat*, blah/*
        """)
            cat = processor.Cataloger()
            six.assertCountEqual(self,  cat._include_filter, ['*test*','splat*','blah/*'])

    def test_050_301_exclude_line_present(self):
        """Test that the filters section with a exclude = line"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [filters]
    exclude = *test*, splat*, blah/*
        """)
            cat = processor.Cataloger()
            six.assertCountEqual(self,  cat._exclude_filter, ['*test*','splat*','blah/*'])

    def test_050_310_invalid_option(self):
        """Test that the filters section with a invalid option"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
    [filters]
    blah = gibberish
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid config line in section \[filters\] : \'blah = gibberish\' on line 2'):
                cat = processor.Cataloger()

class TestReportsConfig(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_400_excluded_true(self):
        """Reports section with excluded = True"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        excluded = true
            """)
            cat = processor.Cataloger()
            self.assertTrue(cat._report_excluded)

    def test_050_401_excluded_yes(self):
        """Reports section with excluded = yes"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        excluded = yes
            """)
            cat = processor.Cataloger()
            self.assertTrue(cat._report_excluded)

    def test_050_402_excluded_no(self):
        """Reports section with excluded = no"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        excluded = no
            """)
            cat = processor.Cataloger()
            self.assertFalse(cat._report_excluded)

    def test_050_403_excluded_false(self):
        """Reports section with excluded = false"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        excluded = false
            """)
            cat = processor.Cataloger()
            self.assertFalse(cat._report_excluded)

    def test_050_420_mismatch_true(self):
        """Reports section with mismatch = True"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        mismatch = true
            """)
            cat = processor.Cataloger()
            self.assertTrue(cat._report_mismatch)

    def test_050_421_mismatch_yes(self):
        """Reports section with mismatch = yes"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        mismatch = yes
            """)
            cat = processor.Cataloger()
            self.assertTrue(cat._report_mismatch)

    def test_050_422_mismatch_no(self):
        """Reports section with mismatch = no"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        mismatch = no
            """)
            cat = processor.Cataloger()
            self.assertFalse(cat._report_mismatch)

    def test_050_423_mismatch_false(self):
        """Reports section with mismatch = false"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        mismatch = false
            """)
            cat = processor.Cataloger()
            self.assertFalse(cat._report_mismatch)

    def test_050_440_missing_true(self):
        """Reports section with missing = true"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        missing = true
            """)
            cat = processor.Cataloger()
            self.assertTrue(cat._report_missing)

    def test_050_441_missing_yes(self):
        """Reports section with missing = yes"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        missing = yes
            """)
            cat = processor.Cataloger()
            self.assertTrue(cat._report_missing)

    def test_050_442_missing_no(self):
        """Reports section with missing = no"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        missing = no
            """)
            cat = processor.Cataloger()
            self.assertFalse(cat._report_missing)

    def test_050_443_missing_false(self):
        """Reports section with missing = false"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        missing = false
            """)
            cat = processor.Cataloger()
            self.assertFalse(cat._report_missing)

    def test_050_460_extra_true(self):
        """Reports section with extra = true"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        extra = true
            """)
            cat = processor.Cataloger()
            self.assertTrue(cat._report_extra)

    def test_050_461_extra_yes(self):
        """Reports section with extra = yes"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        extra = yes
            """)
            cat = processor.Cataloger()
            self.assertTrue(cat._report_extra)

    def test_050_462_extra_no(self):
        """Reports section with extra = no"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        extra = no
            """)
            cat = processor.Cataloger()
            self.assertFalse(cat._report_extra)

    def test_050_463_extra_false(self):
        """Reports section with extra = false"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        extra = false
            """)
            cat = processor.Cataloger()
            self.assertFalse(cat._report_extra)

    def test_050_480_extension_true(self):
        """Reports section with extension = true"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        extension = true
            """)
            cat = processor.Cataloger()
            self.assertTrue(cat._report_extension)

    def test_050_481_extension_yes(self):
        """Reports section with extension = yes"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        extension = yes
            """)
            cat = processor.Cataloger()
            self.assertTrue(cat._report_extension)

    def test_050_482_extension_no(self):
        """Reports section with extension = no"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        extension = no
            """)
            cat = processor.Cataloger()
            self.assertFalse(cat._report_extension)

    def test_050_483_extension_false(self):
        """Reports section with extension = false"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        extension = false
            """)
            cat = processor.Cataloger()
            self.assertFalse(cat._report_extension)

    def test_050_490_verbose_zero(self):
        """Reports section with verbose = 0"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        verbose = 0
            """)
            cat = processor.Cataloger()
            self.assertEqual(cat._verbose, 0)

    def test_050_491_verbose_one(self):
        """Reports section with verbose = 1"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        verbose = 1
            """)
            cat = processor.Cataloger()
            self.assertEqual(cat._verbose, 1)

    def test_050_492_verbose_two(self):
        """Reports section with verbose = 2"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        verbose = 2
            """)
            cat = processor.Cataloger()
            self.assertEqual(cat._verbose, 2)

    def test_050_493_verbose_invalid(self):
        """Reports section with verbose value invalid"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        verbose = wibble
            """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in section \[reports\] : \'verbose = wibble\' on line 2'):
                cat = processor.Cataloger()

    def test_050_495_invalid_option(self):
        """Reports section with invalid option"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
        [reports]
        wibble=3
            """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid option in section \[reports\] : \'wibble=3\' on line 2'):
                cat = processor.Cataloger()

class ConfigSectionError(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_500_incorrect_section(self):
        """Invalid Section name"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
            [wibble]
            verbose = 3
                """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Unknown section title in config file :  \'\[wibble\]\' on line 1'):
                cat = processor.Cataloger()

    def test_050_501_vaild_section_repeated(self):
        """Repeated valid section name"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
            [reports]
            verbose = 2
            
            [reports]
                """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Repeated section title in config file :  \'\[reports\]\' on line 4'):
                cat = processor.Cataloger()

    def test_050_501_missing_section(self):
        """directive outside section"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile(defaults.DEFAULT_CONFIG_FILE, contents="""
            verbose = 3

            [reports]
                """)
            with six.assertRaisesRegex(self, processor.ConfigError,
                                       r'Config line outside a section :  \'verbose = 3\' on line 1'):
                cat = processor.Cataloger()


class TestApi(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_100_000_default_create(self):
        """Test default create"""
        contents = {'./a.py':u'a'*20,
                    './b.py':u'b'*20,
                    './c.html':u'c'*20,
                    'static/d.png':u'd'*20,
                    'htmlcov/e.png':u'e'*20,
                    'src/f.png':u'f' * 20,
                    'src/g.pyc':u'g' * 20}
        with Patcher() as patcher:
            for file_name, data in contents.items():
                patcher.fs.CreateFile( file_name, contents=data)
            cat = commands.create_catalog()
            # Confirm that the relevant counts and lists are as expected
            self.assertTrue(os.path.exists(defaults.DEFAULT_CATALOG_FILE))
            self.assertEqual(cat.processed_count, 4)
            six.assertCountEqual(self, cat.extension_counts,
                                 {'.py':2,'.html':1,'.png':1})
            six.assertCountEqual(self, cat.excluded_files, ['src/g.pyc'])

            # Confirm the contents of the catalog.cat
            with open(defaults.DEFAULT_CATALOG_FILE, 'r') as man_fp:
                for idx, line in enumerate(man_fp):
                    name, sig = line.split('\t')
                    self.assertEqual(get_sig(contents[name]), sig.strip())
                else:
                    self.assertEqual(idx, 3) # WIll be equal to line count

    def test_100_010_default_check(self):
        """Test Default check"""
        contents = {'./a.py':'a'*20,
                    './b.py':'b'*20,
                    './c.html':'c'*20,
                    'static/d.png':'d'*20,
                    'htmlcov/e.png':'e'*20,
                    'src/f.png':'f' * 20,
                    'src/g.pyc':'g' * 20}
        with Patcher() as patcher:
            # Manually create a catalog file
            with open(defaults.DEFAULT_CATALOG_FILE, 'w') as fp:
                for file_name, data in contents.items():
                    fp.write(file_name + '\t' + get_sig(data) + '\n')
                    patcher.fs.CreateFile( file_name, contents=data)

            # Create an extra file
            patcher.fs.CreateFile('tests/a.py',contents='a'*20)

            # Create a missing file
            os.remove('./b.py')

            # Create a mismatch_file
            os.remove('./a.py')
            patcher.fs.CreateFile('./a.py', contents=contents['./a.py']*2)

            cat = commands.check_catalog()

            six.assertCountEqual(self, cat.extra_files, ['tests/a.py'] )
            six.assertCountEqual(self, cat.missing_files, ['b.py'] )
            six.assertCountEqual(self, cat.mismatched_files, ['a.py'] )
            six.assertCountEqual(self, cat.excluded_files, ['src/g.pyc'])


class TestCli(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_files(self, fs, fs_contents):
        for file_name, data in fs_contents.items():
            fs.CreateFile(file_name, contents=data)

    def test_200_000_basic_create(self):
        contents = {'./a.py':'a'*20,
                    './b.py':'b'*20,
                    './c.html':'c'*20,
                    'static/d.png':'d'*20,
                    'htmlcov/e.png':'e'*20,
                    'src/f.png':'f' * 20,
                    'src/g.pyc':'g' * 20}

        with Patcher() as patcher:
            patcher.fs.add_real_paths([pkg_resources.resource_filename('cataloger','templates')])
            os.chdir('/tmp')
            self.make_files(fs=patcher.fs, fs_contents = contents)


            runner = click.testing.CliRunner()
            result = runner.invoke(cli_main.main, ['create'])

            self.assertIsNone(result.exception)
            self.assertEqual(result.exit_code,0)

            six.assertRegex(self, result.output, r'4 files processed - 1 files excluded')
            six.assertRegex(self, result.output, r'Files processed by file types')
            m = re.search(r'Files processed by file types', result.output)

            six.assertRegex(self, result.output[m.end(0):], r'\.py : 2')
            six.assertRegex(self, result.output[m.end(0):], r'\.html : 1')
            six.assertRegex(self, result.output[m.end(0):], r'\.png : 1')

            # Confirm the contents of the catalog.cat
            with open(defaults.DEFAULT_CATALOG_FILE, 'r') as man_fp:
                for idx, line in enumerate(man_fp):
                    name, sig = line.split('\t')
                    self.assertEqual(get_sig(contents[name]), sig.strip())
                else:
                    self.assertEqual(idx, 3) # WIll be equal to line count

    def test_200_001_basic_check(self):
        contents = {'./a.py':'a'*20,
                    './b.py':'b'*20,
                    './c.html':'c'*20,
                    'src/f.png':'f' * 20}

        with Patcher() as patcher:
            patcher.fs.add_real_paths([pkg_resources.resource_filename('cataloger','templates')])
            os.chdir('/tmp')
            self.make_files(fs=patcher.fs, fs_contents = contents)

            # Confirm the contents of the catalog.cat
            with open(defaults.DEFAULT_CATALOG_FILE, 'w') as man_fp:
                for name, data in contents.items():
                    man_fp.write('{}\t{}\n'.format(name, get_sig(data)))

            runner = click.testing.CliRunner()
            result = runner.invoke(cli_main.main, ['check'])

            self.assertIsNone(result.exception)
            self.assertEqual(result.exit_code,0)

            six.assertRegex(self, result.output, r'4 files processed - 0 files excluded')
            six.assertRegex(self, result.output, r'Files processed by file types')
            m = re.search(r'Files processed by file types', result.output)

            six.assertRegex(self, result.output[m.end(0):], r'\.py : 2')
            six.assertRegex(self, result.output[m.end(0):], r'\.html : 1')
            six.assertRegex(self, result.output[m.end(0):], r'\.png : 1')

# noinspection PyMissingOrEmptyDocstring,PyUnusedLocal
def load_tests(loader, tests=None, patterns=None,excludes=None):
    """Load tests from all of the relevant classes, and order them"""
    classes = [cls for name, cls in inspect.getmembers(sys.modules[__name__],
                                                       inspect.isclass)
               if issubclass(cls, unittest.TestCase)]

    suite = OrderedTestSuite()
    for test_class in classes:
        tests = loader.loadTestsFromTestCase(test_class)
        if patterns:
            tests = [test for test in tests if all(re.search(pattern, test.id()) for pattern in patterns)]
        if excludes:
            tests = [test for test in tests if not any(re.search(exclude_pattern,test.id()) for exclude_pattern in excludes)]
        suite.addTests(tests)
    return suite

@click.command()
@click.option('-v', '--verbose', default=2, help='Level of output', count=True)
@click.option('-s', '--silent', is_flag=True, default=False, help='Supress all output apart from a summary line of dots and test count')
@click.option('-x', '--exclude', metavar='EXCLUDE', multiple=True, help='Exclude where the names contain the [EXCLUDE] pattern')
@click.argument('patterns', nargs=-1, required=False, type=str)
def main(verbose, silent, patterns, exclude):
    """Execute the unit test cases where the test id match the patterns

    Test cases are only included for execution if their names (the class name and the method name)
    contain any of the text in any of the [PATTERNS].
    Test cases are excluded from execution if their names contain any of the text in any of the [EXCLUSION]
    patterns

    Both [PATTERNS] and [EXCLUSION] can be regular expressions (using the re syntax)

    \b
    A single -v produces a single '.' for each test executed
    Using -v -v produces an output of the method name and 1st line of any
            doc string for each test executed
    """
    verbose = 0 if silent else verbose

    ldr = unittest.TestLoader()
    test_suite = load_tests(ldr, patterns=patterns, excludes=exclude)
    unittest.TextTestRunner(verbosity=verbose).run(test_suite)

if __name__ == '__main__':
    main()