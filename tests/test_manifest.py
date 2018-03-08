#!/usr/bin/env python
# coding=utf-8
"""
# manifest-checker : Implementation of test_manifest-check.py

Summary : 
    <summary of module/class being implemented>
Use Case : 
    As a <actor> I want <outcome> So that <justification>

Testable Statements :
    Can I <Boolean statement>
    ....
"""

__version__ = "0.1"
__author__ = 'Tony Flury : anthony.flury@btinternet.com'
__created__ = '16 Feb 2018'

import unittest
import sys
import re
import inspect
import click
import six
import hashlib
import os

if six.PY2:
    from mock import patch, mock_open, MagicMock, call, sentinel
else:
    from unittest.mock import patch, mock_open, MagicMock, call, sentinel


from pyfakefs.fake_filesystem_unittest import Patcher

import manifest_checker.processor as processor
import manifest_checker.defaults as defaults

file_spec = None

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

def _iterate_read_data(read_data):
    # Helper for mock_open:
    # Retrieve lines from read_data via a generator so that separate calls to
    # readline, read, and readlines are properly interleaved
    sep = b'\n' if isinstance(read_data, bytes) else '\n'
    data_as_list = [l + sep for l in read_data.split(sep)]

    if data_as_list[-1] == sep:
        # If the last line ended in a newline, the list comprehension will have an
        # extra entry that's just a newline.  Remove this.
        data_as_list = data_as_list[:-1]
    else:
        # If there wasn't an extra newline by itself, then the file being
        # emulated doesn't have a newline to end the last line  remove the
        # newline that our naive format() added
        data_as_list[-1] = data_as_list[-1][:-1]

    for line in data_as_list:
        yield line

def new_mock_open(mock=None, read_data=''):
    """
    A helper function to create a mock to replace the use of `open`. It works
    for `open` called directly or used as a context manager.

    The `mock` argument is the mock object to configure. If `None` (the
    default) then a `MagicMock` will be created for you, with the API limited
    to methods or attributes available on standard file handles.

    `read_data` is a string for the `read` methoddline`, and `readlines` of the
    file handle to return.  This is an empty string by default.
    """
    def _readlines_side_effect(*args, **kwargs):
        if handle.readlines.return_value is not None:
            return handle.readlines.return_value
        return list(_state[0])

    def _read_side_effect(*args, **kwargs):
        if handle.read.return_value is not None:
            return handle.read.return_value
        return type(read_data)().join(_state[0])

    def _readline_side_effect():
        if handle.readline.return_value is not None:
            while True:
                yield handle.readline.return_value
        for line in _state[0]:
            yield line


    global file_spec
    if file_spec is None:
        # set on first use
        if six.PY3:
            import _io
            file_spec = list(set(dir(_io.TextIOWrapper)).union(set(dir(_io.BytesIO))))
        else:
            file_spec = file

    if mock is None:
        mock = MagicMock(name='open', spec=open)

    handle = MagicMock(spec=file_spec)
    handle.__enter__.return_value = handle

    _state = [_iterate_read_data(read_data), None]

    handle.write.return_value = None
    handle.read.return_value = None
    handle.readline.return_value = None
    handle.readlines.return_value = None

    handle.read.side_effect = _read_side_effect
    _state[1] = _readline_side_effect()
    handle.readline.side_effect = _state[1]
    handle.readlines.side_effect = _readlines_side_effect

    handle.__iter__.side_effect = _readline_side_effect

    def reset_data(*args, **kwargs):
        _state[0] = _iterate_read_data(read_data)
        if handle.readline.side_effect == _state[1]:
            # Only reset the side effect if the user hasn't overridden it.
            _state[1] = _readline_side_effect()
            handle.readline.side_effect = _state[1]
        return sentinel.DEFAULT

    mock.side_effect = reset_data
    mock.return_value = handle
    return mock


class OrderedTestSuite(unittest.TestSuite):
    def __iter__(self):
        return iter(sorted(self._tests, key=lambda x:str(x)))


class TestEnvCreation(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_000_000_basic_creation(self):
        """Test the basic creation of the ManifestProcessor"""
        env = processor.ManifestProcessor(action='create')
        self.assertEqual(env._manifest_name, defaults.DEFAULT_MANIFEST_FILE)
        self.assertEqual(env._verbose, defaults.DEFAULT_VERBOSE)
        self.assertEqual(env._hash, defaults.DEFAULT_HASH)
        self.assertEqual(env._root, '.' )
        self.assertEqual(env._report_skipped, 'report_skipped' in defaults.DEFAULT_REPORTON)
        self.assertEqual(env._report_extension, defaults.DEFAULT_REPORT_EXTENSIONS)
        self.assertEqual(env._group, defaults.DEFAULT_REPORT_GROUP)
        self.assertEqual(env._extensions, defaults.DEFAULT_EXTENSIONS)
        self.assertEqual(env._ignore_directories, defaults.DEFAULT_IGNOREDIRECTORY)

    def test_000_001_start_create_command(self):
        """Test the start command"""
        with patch('manifest_checker.processor.open', mock_open()) as m:
            env = processor.ManifestProcessor(action='create')
            m.assert_has_calls([call('manifest.txt','w'),call('manifest.cfg','r')],any_order=True)

    def test_000_002_start_check_command(self):
        """Test the start command - empty manifest"""
        with patch('manifest_checker.processor.open', MagicMock(name='open')) as m:
            m.return_value = MagicMock(name='file')
            with six.assertRaisesRegex(self, processor.ManifestError, r'Empty manifest file : manifest\.txt'):
                env = processor.ManifestProcessor(action='check')
            m.assert_has_calls([call('manifest.txt','r'),call('manifest.cfg','r')],any_order=True)
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or ('__enter__' in call_names and '__exit__' in call_names))

    def test_000_003_config_default_notthere(self):
        """No Explicit config file parameter, no default config - no warning"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            with patch('sys.stderr', six.StringIO()) as stderr:
                env= processor.ManifestProcessor()
                self.assertEqual(stderr.getvalue(), '')

    def test_000_003e_config_explicit_notthere(self):
        """Explicit config file parameter, no config file, warning generated"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            with patch('sys.stderr', six.StringIO()) as stderr:
                env= processor.ManifestProcessor(config='manifest.cfg')
                six.assertRegex(self, stderr.getvalue(), 'Warning : Unable to open config file \'manifest.cfg\'; continuing with defaults')

    def test_000_004_config_default_noperm(self):
        """No Explicit config file parameter, config file exists but no perm"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg')
            os.chmod('/tmp/manifest.cfg', 007)
            with patch('sys.stderr', six.StringIO()) as stderr:
                with six.assertRaisesRegex(self, processor.ConfigError, r'Permission denied'):
                    env= processor.ManifestProcessor()

    def test_000_004e_config_explicit_noperm(self):
        """Explicit config file parameter, config file exists but no perm"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg')
            os.chmod('/tmp/manifest.cfg', 007)
            with patch('sys.stderr', six.StringIO()) as stderr:
                with six.assertRaisesRegex(self, processor.ConfigError, r'Permission denied'):
                    env= processor.ManifestProcessor(config='manifest.cfg')

    def test_000_010_new_mock_open(self):
        data = 'this is data\nspread over many lines\nto see if \n iter will work'
        if six.PY3:
            open_name = 'builtins.open'
        else:
            open_name = '__builtin__.open'
        with patch(open_name, new_mock_open(read_data=data)) as m:
            with open('a.b', 'r') as fp:
                self.assertEqual([i for i in six.StringIO(data)], [x for x in fp])

    def test_000_023_check_command_nonempty_manifest(self):
        """Test the start command"""
        manifest = """a.py\t787908798d
b.py\t787787ef7e
c.py\t7898798acd"""
        with patch('manifest_checker.processor.open', new_mock_open(read_data=manifest)) as m:
            env = processor.ManifestProcessor(action='check', no_config=True)
            m.assert_called_once_with('manifest.txt', 'r')
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or ('__enter__' in call_names and '__exit__' in call_names))

    def test_000_030_start_invalid_command(self):
        """Test the start command"""
        with six.assertRaisesRegex(self, ValueError,r'foobar'):
            env = processor.ManifestProcessor(action='foobar')

    def test_000_031_empty_extension_list(self):
        """Instantiate Command environment with empty extension manifest_write"""
        with six.assertRaisesRegex(self, processor.ManifestError, r'No file extensions given to catalogue or check'):
            env = processor.ManifestProcessor(extensions=[])

class TestSignatureCreation(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_010_000_default_hash(self):
        """Assume a default command - i.e. no arguments other than create"""

        sample_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        cmd = processor.ManifestProcessor(action='create')

        with patch('manifest_checker.processor.open',
                   mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_has_calls([call('./a.py', 'r')])
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or
                             ('__enter__' in call_names and '__exit__' in call_names))

        non_lib_sig = hashlib.new(defaults.DEFAULT_HASH)
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())

    def test_010_001_sha1_hash_creation(self):
        """Assume a explicit create an sha1 hash"""

        sample_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        cmd = processor.ManifestProcessor(action='create', hash='sha1')

        with patch('manifest_checker.processor.open',
                   mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_has_calls([call('./a.py', 'r')])
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or
                             ('__enter__' in call_names and '__exit__' in call_names))

        non_lib_sig = hashlib.new('sha1')
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())

    def test_010_002_sha224_hash_creation(self):
        """Assume a explicit create an sha224 hash"""

        sample_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        cmd = processor.ManifestProcessor(action='create', hash='sha224')

        with patch('manifest_checker.processor.open',
                   mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_has_calls([call('./a.py', 'r')])
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or
                             ('__enter__' in call_names and '__exit__' in call_names))

        non_lib_sig = hashlib.new('sha224')
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())

    def test_010_003_sha384_hash_creation(self):
        """Explicit create an sha384 hash"""
        cmd = processor.ManifestProcessor(hash='sha384')
        sample_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        with patch('manifest_checker.processor.open',
                   mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_has_calls([call('./a.py', 'r')])
            call_names = set(x[0] for x in m.return_value.mock_calls)
            self.assertTrue( 'close' in call_names or
                             ('__enter__' in call_names and '__exit__' in call_names))

        non_lib_sig = hashlib.new('sha384')
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())


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

            env = processor.ManifestProcessor()
            for directory, files in env.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py']})
        self.assertEqual(env._skipped_file_count, 0)

    def test_020_001_WalkFlatDirectoryExclusions(self):
        """Test the walk function returns lists of files as appropriate with a flat directory with a file excluded"""
        dir = {}
        self.maxDiff = None

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t1.pyc')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('manifest.txt')

            env = processor.ManifestProcessor()

            six.assertCountEqual(self,os.listdir(os.getcwd()),['manifest.txt','t1.py','t2.py','t1.pyc'])

            for directory, files in env.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py']})
        self.assertEqual(env._skipped_file_count, 2)

    def test_020_002_WalkFlatDirectoryMultipleExclusions(self):
        """Test the walk function returns lists of files as appropriate with a flat directory with multiple file excluded"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')
            env = processor.ManifestProcessor()
            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t1.pyc')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('t2.pyc')

            six.assertCountEqual(self,os.listdir(os.getcwd()),['t1.py','t2.py','t1.pyc','t2.pyc'])

            for directory, files in env.walk():
                dir[directory] = files

            six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py']})
            self.assertEqual(env._skipped_file_count, 2)

    def test_020_010_Walk2DeepMultipleExclusions(self):
        """walk recurses into directories"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            env = processor.ManifestProcessor()

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('t1.pyc')
            patcher.fs.CreateFile('t2.pyc')

            patcher.fs.CreateFile('test/test.py')
            patcher.fs.CreateFile('test/test.pyc')

            six.assertCountEqual(self,os.listdir(os.getcwd()),['test', 't1.py','t2.py','t1.pyc','t2.pyc'])
            six.assertCountEqual(self,os.listdir('/tmp/test'),['test.py','test.pyc'])

            for directory, files in env.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['test.py']})
        self.assertEqual(env._skipped_file_count, 3)

    def test_020_020_WalkExcludedDirectories(self):
        """walk method excluding the right directories"""

        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            env = processor.ManifestProcessor()

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/test.py')

            for d in defaults.DEFAULT_IGNOREDIRECTORY:
                patcher.fs.CreateDirectory(os.path.join('/tmp',d))

            six.assertCountEqual(self,os.listdir(os.getcwd()), ['test', 't1.py','t2.py'] + list(defaults.DEFAULT_IGNOREDIRECTORY) )
            six.assertCountEqual(self,os.listdir('/tmp/test'),['test.py'])

            for directory, files in env.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['test.py']})
        self.assertEqual(env._skipped_file_count, 0)

    def test_020_050_single_exclude_filter_no_match(self):
        """Single filter argument, which shouldn't match anything"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            env = processor.ManifestProcessor(exclude_filter=['*wibble*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/test.py')

            for directory, files in env.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['test.py']})
        self.assertEqual(env._skipped_file_count, 0)

    def test_020_051_single_exclude_filter_match_file(self):
        """Single filter argument, which will match one file"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            env = processor.ManifestProcessor(exclude_filter=['*/tike.py'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/tike.py')

            for directory, files in env.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py']})
        self.assertEqual(env._skipped_file_count, 1)

    def test_020_052_single_exclude_filter_match_directory(self):
        """Single filter argument, which will match one file"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            env = processor.ManifestProcessor(exclude_filter=['test/*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/t1.py')

            for directory, files in env.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py']})
        self.assertEqual(env._skipped_file_count, 1)

    def test_020_054_multiple_exclude_filters_no_matches(self):
        """Multiple filters which match nothing"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            env = processor.ManifestProcessor(exclude_filter=['*wibble*','*wobble*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/t1.py')

            for directory, files in env.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['t1.py']})
        self.assertEqual(env._skipped_file_count, 0)

    def test_020_056_multiple_exclude_filters_one_match(self):
        """Multiple filters where one places matches"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            env = processor.ManifestProcessor(exclude_filter=['*wibble*','*/a?.*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/a1.py')
            patcher.fs.CreateFile('test/a3a.py')

            for directory, files in env.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['a3a.py']})
        self.assertEqual(env._skipped_file_count, 1)

    def test_020_058_multiple_exclude_filters_multiple_match(self):
        """Multiple filters where one places matches"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            env = processor.ManifestProcessor(exclude_filter=['*wibble*','*/a?.*'])

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/a1.py')
            patcher.fs.CreateFile('test/a2.py')
            patcher.fs.CreateFile('test/a3a.py')

            for directory, files in env.walk():
                dir[directory] = files

        six.assertCountEqual(self,dir,{'.': ['t1.py', 't2.py'],'test':['a3a.py']})
        self.assertEqual(env._skipped_file_count, 2)

class HelperFunctions(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_030_000_load_manifest(self):
        """Load Manifest"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('/tmp/manifest.txt', contents="""a.py\t889898aa898a1
b.py\t889898aa898a2
c.py\t889898aa898a3
sub/a1.py\t889898aa898a4""")
            env = processor.ManifestProcessor(action='check')

        self.assertTrue(env.is_file_in_manifest('.','a.py'))
        self.assertTrue(env.is_file_in_manifest('.','b.py'))
        self.assertTrue(env.is_file_in_manifest('.','c.py'))
        self.assertTrue(env.is_file_in_manifest('sub','a1.py'))
        self.assertFalse(env.is_file_in_manifest('test','test.py'))

    def test_030_002_load_non_existant_manifest(self):
        """Attempt to load manifest file which doesn't exist"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            with six.assertRaisesRegex(self, processor.ManifestError, r'No such file or directory'):
                env = processor.ManifestProcessor(action='check')

    def test_030_003_load_manifest_no_permission_read(self):
        """Attempt to load manifest file which doesn't exist"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            env = patcher.fs.CreateFile('manifest.txt', contents='')
            os.chmod('/tmp/manifest.txt', mode=int('077',8))

            with six.assertRaisesRegex(self, processor.ManifestError, r'Permission denied'):
                env = processor.ManifestProcessor(action='check')

    def test_030_004_load_manifest_no_permission_write(self):
        """Attempt to load manifest file which doesn't exist"""

        with Patcher() as patcher:
            os.chdir('/tmp')

            mocked_open = MagicMock(wraps=processor.__builtins__['open'])

            env = patcher.fs.CreateFile('manifest.txt', contents='')
            os.chmod('/tmp/manifest.txt', mode=int('077',8))

            with six.assertRaisesRegex(self, processor.ManifestError, r'Permission denied'):
                env = processor.ManifestProcessor(action='create')
                mocked_open.assert_called_once_with('\tmp\manifest.text','w')

    def test_030_010_get_signature_from_manifest(self):
        """Load Manifest & fetch signature from manifest"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.txt', contents="""a.py\t889898aa898a1
b.py\t889898aa898a2
c.py\t889898aa898a3
sub/a1.py\t889898aa898a4""")

            env = processor.ManifestProcessor(manifest='/tmp/manifest.txt', action='check')

            self.assertEqual(env.get_signature('./a.py',manifest=True), '889898aa898a1' )
            self.assertEqual(env.get_signature('./b.py',manifest=True), '889898aa898a2' )
            self.assertEqual(env.get_signature('./c.py',manifest=True), '889898aa898a3' )
            self.assertEqual(env.get_signature('sub/a1.py',manifest=True), '889898aa898a4' )
            self.assertIsNone(env.get_signature('./test.py',manifest=True))

    def test_030_011_get_signature_from_manifest_blank_lines(self):
        """Load Manifest & fetch signature from manifest - ignore blank lines"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.txt', contents="""
a.py\t889898aa898a1

b.py\t889898aa898a2

c.py\t889898aa898a3

sub/a1.py\t889898aa898a4""")

            env = processor.ManifestProcessor(manifest='/tmp/manifest.txt', action='check')

            self.assertEqual(env.get_signature('./a.py', manifest=True),
                             '889898aa898a1')
            self.assertEqual(env.get_signature('./b.py', manifest=True),
                             '889898aa898a2')
            self.assertEqual(env.get_signature('./c.py', manifest=True),
                             '889898aa898a3')
            self.assertEqual(env.get_signature('sub/a1.py', manifest=True),
                             '889898aa898a4')
            self.assertIsNone(env.get_signature('./test.py', manifest=True))

    def test_030_012_load_manifest_empty(self):
        """Load Manifest & fetch signature from manifest - ignore blank lines"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.txt', contents='')
            with six.assertRaisesRegex(self, processor.ManifestError, 'Empty manifest'):
                env = processor.ManifestProcessor(
                    manifest='/tmp/manifest.txt', action='check')

    def test_030_013_load_manifest_invalid_missing_tab(self):
        """Load Manifest & fetch signature from manifest - ignore blank lines"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.txt', contents="""
a.py\t889898aa898a
b.py 889898aa898a
""")
            with six.assertRaisesRegex(self, processor.ManifestError, 'Invalid manifest format - missing tab on line 2'):
                env = processor.ManifestProcessor(
                    manifest='/tmp/manifest.txt', action='check')

    def test_030_014_load_manifest_invalid_signature(self):
        """Load Manifest & fetch signature from manifest - invalid signature hex string"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.txt', contents="""
a.py\tWibbleZibble 
b.py\t889898aa898a
""")
            with six.assertRaisesRegex(self, processor.ManifestError,
                                       'Invalid manifest format - invalid signature on line 1'):
                env = processor.ManifestProcessor(
                    manifest='/tmp/manifest.txt', action='check')

    def test_030_020_record_extra(self):
        """functionality of record_extra method"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            env = processor.ManifestProcessor(action='create')

            env.record_extra('./a.py')
            env.record_extra('./c.py')

        six.assertCountEqual(self,env.extra_files,['a.py','c.py'])
        self.assertEqual(dict([(k,v) for k,v in env.extension_counts]), {'.py':2})

    def test_030_021_record_mismatch(self):
        """functionality of record_mismatch method"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            env = processor.ManifestProcessor(action='create')

            env.record_mismatch('./a.py')
            env.record_mismatch('./c.py')

        six.assertCountEqual(self,env.mismatched_files,['a.py','c.py'])
        self.assertEqual(dict([(k,v) for k,v in env.extension_counts]), {'.py':2})

    def test_030_022_record_missing(self):
        """functionality of record_missing method"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            env = processor.ManifestProcessor(action='create', root='/tmp')

            env.record_missing('./a.py')
            env.record_missing('./c.py')

        six.assertCountEqual(self,env.missing_files,['a.py','c.py'])
        self.assertEqual(dict([(k,v) for k,v in env.extension_counts]), {'.py':2})

    def test_030_040_manifest_write(self):
        """Manifest_write with faked file and signature"""
        file_name = './a.py'
        signature = 'bbacdss3'
        with patch('manifest_checker.processor.open', mock_open()) as m:
            os.chdir('/tmp')
            env = processor.ManifestProcessor(action='create', verbose=0)
            env.manifest_write(file_name, signature)
            env.final_report()
            m.assert_has_calls([call('manifest.txt','w'),call('manifest.cfg','r')],any_order=True)
            m.return_value.write('{}\t{}\n'.format(file_name, signature))

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
            patcher.fs.CreateFile('manifest.txt', contents="""
        a.py\t3765aaababba 
        b.py\t889898aa898a
        """)
            env = processor.ManifestProcessor(manifest='/tmp/manifest.txt', output=output, action='check')
            env.record_missing('test/a.py')
            env.record_missing('test/a.html')
            env.final_report()
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
            patcher.fs.CreateFile('manifest.txt', contents="""
        a.py\t3765aaababba 
        b.py\t889898aa898a
        """)
            env = processor.ManifestProcessor(manifest='/tmp/manifest.txt', output=output, action='check')
            env.record_extra('test/a.js')
            env.record_extra('test/a.html')
            env.final_report()
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
            patcher.fs.CreateFile('manifest.txt', contents="""
        a.py\t3765aaababba 
        b.py\t889898aa898a
        """)
            env = processor.ManifestProcessor(manifest='/tmp/manifest.txt', output=output, action='check')
            env.record_mismatch('test/a.js')
            env.record_mismatch('test/a.html')
            env.final_report()
            m = re.search(r'2 files with mismatched signature', output.getvalue())

            self.assertTrue(re.search(r'\ttest/a\.js\n', output.getvalue()[m.end():]))
            self.assertTrue(re.search(r'\ttest/a\.html\n', output.getvalue()[m.end():]))

            m = re.search(r'Processed by file type\n', output.getvalue())
            self.assertTrue(re.search(r'\t\'.js\' : 1\n', output.getvalue()[m.end():]))
            self.assertTrue(re.search(r'\t\'.html\' : 1\n', output.getvalue()[m.end():]))


class TestManifestConfig(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_000_manifest_line_present(self):
        """Test that the manifest section with a manifest= line is captured correctly"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [manifest]
    manifest=manifest.mft
        """)
            env = processor.ManifestProcessor()
            env._process_config()
            self.assertEqual(env.manifest_file_name,'manifest.mft')
            self.assertEqual(env._hash, 'sha224')
            self.assertEqual(env._root, '.')
            six.assertCountEqual(self, env._extensions, defaults.DEFAULT_EXTENSIONS)

    def test_050_001_hash_line_present(self):
        """Test that the manifest section with a hash= line is captured correctly"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [manifest]
    hash=sha1
        """)
            env = processor.ManifestProcessor()
            self.assertEqual(env.manifest_file_name,'manifest.txt')
            self.assertEqual(env._hash, 'sha1')
            self.assertEqual(env._root, '.')
            six.assertCountEqual(self, env._extensions, defaults.DEFAULT_EXTENSIONS)

    def test_050_001_root_line_present(self):
        """Test that the manifest section with a root= line is captured correctly"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [manifest]
    root=src
        """)
            env = processor.ManifestProcessor()
            self.assertEqual(env.manifest_file_name,'manifest.txt')
            self.assertEqual(env._hash, 'sha224')
            self.assertEqual(env._root, 'src')
            six.assertCountEqual(self, env._extensions, defaults.DEFAULT_EXTENSIONS)

    def test_050_010_invalid_hash(self):
        """Test that the manifest section with an invalid hash value is detected"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [manifest]
    hash = gibberish
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value for hash : \'hash = gibberish\' on line 2'):
                env = processor.ManifestProcessor()

    def test_050_010_invalid_option(self):
        """Test that the manifest section with an invalid option name"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [manifest]
    extension=.py
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid config line in section \[manifest\] : \'extension=.py\' on line 2'):
                env = processor.ManifestProcessor()

class TestExtensionConfig(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_100_equal(self):
        """Test that the extension section with an = operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [extensions]
    =.py,.html,.js
        """)
            env = processor.ManifestProcessor()
            six.assertCountEqual(self, env._extensions, ['.py','.html','.js'])

    def test_050_101_minus(self):
        """Test that the extension section with an - operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [extensions]
    - .py,.html,.js
        """)
            env = processor.ManifestProcessor()
            six.assertCountEqual(self, env._extensions, defaults.DEFAULT_EXTENSIONS - {'.py','.html','.js'} )

    def test_050_102_plus(self):
        """Test that the extension section with an + operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [extensions]
    + .jsx, .cfg, .com
        """)
            env = processor.ManifestProcessor()
            six.assertCountEqual(self, env._extensions, defaults.DEFAULT_EXTENSIONS | {'.jsx', '.cfg', '.com'})

    def test_050_110_invalid_operator(self):
        """Test that the extension section with an invalid operator is correctly detected"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [extensions]
    * .jsx, .cfg, .com
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid operator in \[extension\] section : \'\* \.jsx, \.cfg, \.com\' on line 2'):
                env = processor.ManifestProcessor()

    def test_050_115_invalid_extension_missing_dot(self):
        """Test that the extension section with an extension missing a dot"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [extensions]
    + .jsx, .cfg, com
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[extension\] section : \'\+ \.jsx, \.cfg, com\' on line 2'):
                env = processor.ManifestProcessor()

    def test_050_115_invalid_extensions_null_string(self):
        """Test that the extension section with an null string extension"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [extensions]
    + .jsx, , .com
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[extension\] section : \'\+ \.jsx, , \.com\' on line 2'):
                env = processor.ManifestProcessor()

    def test_050_115_invalid_extensions_dot_only(self):
        """Test that the extension section with an extension which is just a dot"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [extensions]
    + .jsx, . , .com
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[extension\] section : \'\+ \.jsx, \. , \.com\' on line 2'):
                env = processor.ManifestProcessor()

class TestDirectoryConfig(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_200_equal(self):
        """Test that the directories section with an = operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [directories]
    = docs, src, coverage
        """)
            env = processor.ManifestProcessor()
            six.assertCountEqual(self, env._ignore_directories, {'docs', 'src', 'coverage'} )

    def test_050_201_minus(self):
        """Test that the directories section with an - operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [directories]
    - static, htmlcov, docs
        """)
            env = processor.ManifestProcessor()
            six.assertCountEqual(self, env._ignore_directories, defaults.DEFAULT_IGNOREDIRECTORY - {'static', 'htmlcov', 'docs'} )

    def test_050_202_plus(self):
        """Test that the directories section with an + operator is correct"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [directories]
    + build, dist
        """)
            env = processor.ManifestProcessor()
            six.assertCountEqual(self, env._ignore_directories, defaults.DEFAULT_IGNOREDIRECTORY | {'build', 'dist'} )

    def test_050_210_invalid_operator(self):
        """Test that the directories section with an invalid operator is correctly detected"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [directories]
    * build, dist
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid operator in \[directories\] section : \'\* build, dist\' on line 2'):
                env = processor.ManifestProcessor()

    def test_050_215_null_string(self):
        """Test that the directories section with an null string directories"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [directories]
    + build, , dist
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid value in \[directories\] section : \'\+ build, , dist\' on line 2'):
                env = processor.ManifestProcessor()

    def test_050_216_empty_list(self):
        """Test that the directories section with an null string directories"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [directories]
    =
        """)
            env = processor.ManifestProcessor()
            self.assertEqual(env._ignore_directories,set())

class TestFilterConfig(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_300_include_line_present(self):
        """Test that the manifest section with a manifest= line is captured correctly"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [filters]
    include = *test*, splat*, blah/*
        """)
            env = processor.ManifestProcessor()
            six.assertCountEqual(self,  env._include_filter, ['*test*','splat*','blah/*'])

    def test_050_301_exclude_line_present(self):
        """Test that the manifest section with a manifest= line is captured correctly"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [filters]
    exclude = *test*, splat*, blah/*
        """)
            env = processor.ManifestProcessor()
            six.assertCountEqual(self,  env._exclude_filter, ['*test*','splat*','blah/*'])

    def test_050_310_invalid_option(self):
        """Test that the manifest section with an invalid hash value is detected"""
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
    [filters]
    blah = gibberish
        """)
            with six.assertRaisesRegex(self, processor.ConfigError, r'Invalid config line in section \[filters\] : \'blah = gibberish\' on line 2'):
                env = processor.ManifestProcessor()

class TestReportsConfig(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_050_400_skipped_true(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        skipped = true
            """)
            env = processor.ManifestProcessor()
            self.assertTrue(env._report_skipped)

    def test_050_401_skipped_yes(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        skipped = yes
            """)
            env = processor.ManifestProcessor()
            self.assertTrue(env._report_skipped)

    def test_050_402_skipped_no(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        skipped = no
            """)
            env = processor.ManifestProcessor()
            self.assertFalse(env._report_skipped)

    def test_050_403_skipped_false(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        skipped = false
            """)
            env = processor.ManifestProcessor()
            self.assertFalse(env._report_skipped)

    def test_050_420_mismatch_true(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        mismatch = true
            """)
            env = processor.ManifestProcessor()
            self.assertTrue(env._report_mismatch)

    def test_050_421_mismatch_yes(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        mismatch = yes
            """)
            env = processor.ManifestProcessor()
            self.assertTrue(env._report_mismatch)

    def test_050_422_mismatch_no(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        mismatch = no
            """)
            env = processor.ManifestProcessor()
            self.assertFalse(env._report_mismatch)

    def test_050_423_mismatch_false(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        mismatch = false
            """)
            env = processor.ManifestProcessor()
            self.assertFalse(env._report_mismatch)

    def test_050_440_missing_true(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        missing = true
            """)
            env = processor.ManifestProcessor()
            self.assertTrue(env._report_missing)

    def test_050_441_missing_yes(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        missing = yes
            """)
            env = processor.ManifestProcessor()
            self.assertTrue(env._report_missing)

    def test_050_442_missing_no(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        missing = no
            """)
            env = processor.ManifestProcessor()
            self.assertFalse(env._report_missing)

    def test_050_443_missing_false(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        missing = false
            """)
            env = processor.ManifestProcessor()
            self.assertFalse(env._report_missing)

    def test_050_460_extra_true(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        extra = true
            """)
            env = processor.ManifestProcessor()
            self.assertTrue(env._report_extra)

    def test_050_461_extra_yes(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        extra = yes
            """)
            env = processor.ManifestProcessor()
            self.assertTrue(env._report_extra)

    def test_050_462_extra_no(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        extra = no
            """)
            env = processor.ManifestProcessor()
            self.assertFalse(env._report_extra)

    def test_050_463_extra_false(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        extra = false
            """)
            env = processor.ManifestProcessor()
            self.assertFalse(env._report_extra)

    def test_050_480_extension_true(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        extension = true
            """)
            env = processor.ManifestProcessor()
            self.assertTrue(env._report_extension)

    def test_050_481_extension_yes(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        extension = yes
            """)
            env = processor.ManifestProcessor()
            self.assertTrue(env._report_extension)

    def test_050_482_extension_no(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        extension = no
            """)
            env = processor.ManifestProcessor()
            self.assertFalse(env._report_extension)

    def test_050_483_extension_false(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        extension = false
            """)
            env = processor.ManifestProcessor()
            self.assertFalse(env._report_extension)

    def test_050_490_verbose_zero(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        verbose = 0
            """)
            env = processor.ManifestProcessor()
            self.assertEqual(env._verbose, 0)

    def test_050_491_verbose_one(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        verbose = 1
            """)
            env = processor.ManifestProcessor()
            self.assertEqual(env._verbose, 1)

    def test_050_492_verbose_two(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        verbose = 2
            """)
            env = processor.ManifestProcessor()
            self.assertEqual(env._verbose, 2)

    def test_050_493_verbose_three(self):
        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.cfg', contents="""
        [reports]
        verbose = 3
            """)
            env = processor.ManifestProcessor()
            self.assertEqual(env._verbose, 3)


class TestCases(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_000_000_something(self):
        pass


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