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
    from mock import patch, mock_open, MagicMock
else:
    from unittest.mock import patch, mock_open, MagicMock

from pyfakefs.fake_filesystem_unittest import Patcher

import manifest_checker.environment as environment
import manifest_checker.defaults as defaults


class OrderedTestSuite(unittest.TestSuite):
    def __iter__(self):
        return iter(sorted(self._tests, key=lambda x:str(x)))


class TestEnvCreation(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_000_000_basic_creation(self):
        """Test the basic creation of the CommandEnvironment"""
        env = environment.CommandEnvironment()
        self.assertEqual(env._manifest_name, defaults.DEFAULT_MANIFEST_FILE)
        self.assertEqual(env._verbose, defaults.DEFAULT_VERBOSE)
        self.assertEqual(env._hash, defaults.DEFAULT_HASH)
        self.assertEqual(env._root, os.getcwd() )
        self.assertEqual(env._report_skipped, defaults.DEFAULT_REPORT_SKIPPED)
        self.assertEqual(env._report_extension, defaults.DEFAULT_REPORT_EXTENSIONS)
        self.assertEqual(env._group, defaults.DEFAULT_REPORT_GROUP)
        self.assertEqual(env._extensions, defaults.DEFAULT_EXTENSIONS)
        self.assertEqual(env._ignore_directories, defaults.DEFAULT_IGNOREDIRECTORY)

    def test_000_001_start_create_command(self):
        """Test the start command"""
        env = environment.CommandEnvironment()
        with patch('manifest_checker.environment.open', mock_open()) as m:
            env.start_command(subcommand='create')
            m.assert_called_once_with('manifest.txt','w')

    def test_000_002_start_check_command(self):
        """Test the start command"""
        env = environment.CommandEnvironment()
        with patch('manifest_checker.environment.open', mock_open()) as m:
            env.start_command(subcommand='check')
            m.assert_called_once_with('manifest.txt','r')

    def test_000_003_start_invalid_command(self):
        """Test the start command"""
        env = environment.CommandEnvironment()
        with six.assertRaisesRegex(self, ValueError,r'foobar'):
            env.start_command(subcommand='foobar')

    def test_000_004_empty_extension_list(self):
        """Instantiate Command environment with empty extension list"""
        with six.assertRaisesRegex(self, environment.ManifestError, r'No file extensions given to catalogue or check'):
            env = environment.CommandEnvironment(extension=[])

class TestSignatureCreation(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_010_000_default_hash(self):
        """Assume a default command - i.e. no arguments other than create"""

        cmd = environment.CommandEnvironment()
        sample_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        with patch('manifest_checker.environment.open', mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature(rel_path='a.py')
            m.assert_called_once_with(os.path.join(os.getcwd(), 'a.py'), 'rb')

        non_lib_sig = hashlib.new(defaults.DEFAULT_HASH)
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())

    def test_010_001_sha1_hash_creation(self):
        """Assume a explicit create an sha1 hash"""
        cmd = environment.CommandEnvironment(hash='sha1')

        sample_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        with patch('manifest_checker.environment.open', mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_called_once_with(os.path.join(os.getcwd(), 'a.py'), 'rb')

        non_lib_sig = hashlib.new('sha1')
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())

    def test_010_002_sha224_hash_creation(self):
        """Assume a explicit create an sha224 hash"""
        cmd = environment.CommandEnvironment(hash='sha224')

        sample_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        with patch('manifest_checker.environment.open', mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_called_once_with(os.path.join(os.getcwd(), 'a.py'), 'rb')

        non_lib_sig = hashlib.new('sha224')
        non_lib_sig.update(sample_text)
        self.assertEqual(this_signature, non_lib_sig.hexdigest().strip())

    def test_010_003_md5_hash_creation(self):
        """Explicit create an md5 hash"""
        cmd = environment.CommandEnvironment(hash='md5')
        sample_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit'

        with patch('manifest_checker.environment.open',
                   mock_open(read_data=sample_text)) as m:
            this_signature = cmd.get_signature('a.py')
            m.assert_called_once_with(os.path.join(os.getcwd(), 'a.py'), 'rb')

        non_lib_sig = hashlib.new('md5')
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

            env = environment.CommandEnvironment()
            for directory, files in env.walk():
                dir[directory] = files

        self.assertItemsEqual(dir,{'.': ['t1.py', 't2.py']})
        self.assertEqual(env._skipped_files, 0)

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

            env = environment.CommandEnvironment()

            self.assertItemsEqual(os.listdir(os.getcwd()),['manifest.txt','t1.py','t2.py','t1.pyc'])

            for directory, files in env.walk():
                dir[directory] = files

        self.assertItemsEqual(dir,{'.': ['t1.py', 't2.py']})
        self.assertEqual(env._skipped_files, 2)

    def test_020_002_WalkFlatDirectoryMultipleExclusions(self):
        """Test the walk function returns lists of files as appropriate with a flat directory with multiple file excluded"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')
            env = environment.CommandEnvironment()
            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t1.pyc')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('t2.pyc')

            self.assertItemsEqual(os.listdir(os.getcwd()),['t1.py','t2.py','t1.pyc','t2.pyc'])

            for directory, files in env.walk():
                dir[directory] = files

            self.assertItemsEqual(dir,{'.': ['t1.py', 't2.py']})
            self.assertEqual(env._skipped_files, 2)

    def test_020_010_Walk2DeepMultipleExclusions(self):
        """walk recurses into directories"""
        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            env = environment.CommandEnvironment()

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('t1.pyc')
            patcher.fs.CreateFile('t2.pyc')

            patcher.fs.CreateFile('test/test.py')
            patcher.fs.CreateFile('test/test.pyc')

            self.assertItemsEqual(os.listdir(os.getcwd()),['test', 't1.py','t2.py','t1.pyc','t2.pyc'])
            self.assertItemsEqual(os.listdir('/tmp/test'),['test.py','test.pyc'])

            for directory, files in env.walk():
                dir[directory] = files

        self.assertItemsEqual(dir,{'.': ['t1.py', 't2.py'],'test':['test.py']})
        self.assertEqual(env._skipped_files, 3)

    def test_020_020_WalkExcludedDirectories(self):
        """walk method excluding the right directories"""

        dir = {}

        with Patcher() as patcher:
            os.chdir('/tmp')

            env = environment.CommandEnvironment()

            patcher.fs.CreateFile('t1.py')
            patcher.fs.CreateFile('t2.py')
            patcher.fs.CreateFile('test/test.py')

            for d in defaults.DEFAULT_IGNOREDIRECTORY:
                patcher.fs.CreateDirectory(os.path.join('/tmp',d))

            self.assertItemsEqual(os.listdir(os.getcwd()), ['test', 't1.py','t2.py'] + defaults.DEFAULT_IGNOREDIRECTORY)
            self.assertItemsEqual(os.listdir('/tmp/test'),['test.py'])

            for directory, files in env.walk():
                dir[directory] = files

        self.assertItemsEqual(dir,{'.': ['t1.py', 't2.py'],'test':['test.py']})
        self.assertEqual(env._skipped_files, 0)


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

            env = environment.CommandEnvironment()
            env.start_command(subcommand='check')
            env.load_manifest()

        self.assertTrue(env.is_file_in_manifest('.','a.py'))
        self.assertTrue(env.is_file_in_manifest('.','b.py'))
        self.assertTrue(env.is_file_in_manifest('.','c.py'))
        self.assertTrue(env.is_file_in_manifest('sub','a1.py'))
        self.assertFalse(env.is_file_in_manifest('test','test.py'))

    def test_030_002_load_non_existant_manifest(self):
        """Attempt to load manifest file which doesn't exist"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            env = environment.CommandEnvironment()
            with six.assertRaisesRegex(self, environment.ManifestError, r'No such file or directory'):
                env.start_command(subcommand='check')

    def test_030_003_load_manifest_no_permission_read(self):
        """Attempt to load manifest file which doesn't exist"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            env = patcher.fs.CreateFile('manifest.txt', contents='')
            os.chmod('/tmp/manifest.txt', mode=int('077',8))

            env = environment.CommandEnvironment()
            with six.assertRaisesRegex(self, environment.ManifestError, r'Permission denied'):
                env.start_command(subcommand='check')

    def test_030_003_load_manifest_no_permission_write(self):
        """Attempt to load manifest file which doesn't exist"""

        with Patcher() as patcher:
            os.chdir('/tmp')

            mocked_open = MagicMock(wraps=environment.__builtins__['open'])

            env = patcher.fs.CreateFile('manifest.txt', contents='')
            os.chmod('/tmp/manifest.txt', mode=int('077',8))

            env = environment.CommandEnvironment()
            with six.assertRaisesRegex(self, environment.ManifestError, r'Permission denied'):
                env.start_command(subcommand='create')
                mocked_open.assert_called_once_with('\tmp\manifest.text','w')

    def test_030_010_get_signature_from_manifest(self):
        """Load Manifest & fetch signature from manifest"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.txt', contents="""a.py\t889898aa898a1
b.py\t889898aa898a2
c.py\t889898aa898a3
sub/a1.py\t889898aa898a4""")

            env = environment.CommandEnvironment(manifest='/tmp/manifest.txt')
            env.start_command(subcommand='check')
            env.load_manifest()

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
            env = environment.CommandEnvironment(manifest='/tmp/manifest.txt')
            env.start_command(subcommand='check')
            env.load_manifest()

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
            env = environment.CommandEnvironment(manifest='/tmp/manifest.txt')
            env.start_command(subcommand='check')
            with six.assertRaisesRegex(self, environment.ManifestError, 'Empty manifest'):
                env.load_manifest()

    def test_030_013_load_manifest_invalid_missing_tab(self):
        """Load Manifest & fetch signature from manifest - ignore blank lines"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.txt', contents="""
a.py\t889898aa898a
b.py 889898aa898a
""")
            env = environment.CommandEnvironment(manifest='/tmp/manifest.txt')
            env.start_command(subcommand='check')
            with six.assertRaisesRegex(self, environment.ManifestError, 'Invalid manifest format - missing tab on line 2'):
                env.load_manifest()

    def test_030_014_load_manifest_invalid_signature(self):
        """Load Manifest & fetch signature from manifest - invalid signature hex string"""

        with Patcher() as patcher:
            os.chdir('/tmp')
            patcher.fs.CreateFile('manifest.txt', contents="""
a.py\tWibbleZibble 
b.py\t889898aa898a
""")
            env = environment.CommandEnvironment(manifest='/tmp/manifest.txt')
            env.start_command(subcommand='check')
            with six.assertRaisesRegex(self, environment.ManifestError,
                                       'Invalid manifest format - invalid signature on line 1'):
                env.load_manifest()

    def test_030_020_record_extra(self):
        """functionality of record_extra method"""
        env = environment.CommandEnvironment()
        env.record_extra('./a.py')
        env.record_extra('./c.py')
        self.assertItemsEqual(env.extra_files,['a.py','c.py'])
        self.assertEqual(env.extension_counts, {'.py':2})

    def test_030_021_record_mismatch(self):
        """functionality of record_mismatch method"""
        env = environment.CommandEnvironment()
        env.record_mismatch('./a.py')
        env.record_mismatch('./c.py')
        self.assertItemsEqual(env.mismatched_files,['a.py','c.py'])
        self.assertEqual(env.extension_counts, {'.py':2})

    def test_030_022_record_missing(self):
        """functionality of record_missing method"""
        env = environment.CommandEnvironment()
        env.record_missing('./a.py')
        env.record_missing('./c.py')
        self.assertItemsEqual(env.missing_files,['a.py','c.py'])
        self.assertEqual(env.extension_counts, {'.py':2})



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