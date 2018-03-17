#!/usr/bin/env python
# coding=utf-8
"""
# cataloger : Implementation of cataloger

Summary : 
    Simple to use tools to create and check directory contents - ideal for integrity checking
Use Case : 
    As a <actor> I want <outcome> So that <justification>

Testable Statements :
    Can I <Boolean statement>
    ....
"""

# Always prefer setuptools over distutils
import sys
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

from cataloger.version import __version__, __author__, __created__

if sys.version_info.major == 2:
    test_extra = ['mock']
else:
    test_extra = []


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

author, author_email = [p.strip() for p in __author__.split(':')]

setup(
        name='cataloger',

        # Versions should comply with PEP440.  For a discussion on single-sourcing
        # the version across setup.py and the project code, see
        # https://packaging.python.org/en/latest/single_source_version.html
        version= __version__,

        description='Simple to use tools to create and check directory contents - ideal for integrity checking',
        long_description=long_description,

        # The project's main homepage.
        url='https://upload.pypi.org/legacy/',

        # Author details
        author = author,
        author_email = author_email,

        # Choose your license
        license='MIT License',

        # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            # How mature is this project? Common values are
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 5 - Production/Stable',

            # Indicate who your project is intended for
            'Intended Audience :: Developers',
            'Framework :: Django',
            'Topic :: Software Development :: Quality Assurance',

            # Pick your license as you wish (should match "license" above)
            'License :: OSI Approved :: MIT License',

            # Specify the Python versions you support here. In particular, ensure
            # that you indicate whether you support Python 2, Python 3 or both.
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
        ],

        # What does your project relate to?
        keywords='Development, Deployment, Integrity Checking',

        # You can just specify the packages manually here if your project is
        # simple. Or you can use find_packages().
        packages=find_packages(exclude=['test*']),

        # List run-time dependencies here.  These will be installed by pip when
        # your project is installed. For an analysis of "install_requires" vs pip's
        # requirements files see:
        # https://packaging.python.org/en/latest/requirements.html
        install_requires=['Click','six','templatelite'],

        include_package_data=True,

        # List additional groups of dependencies here (e.g. development
        # dependencies). You can install these using the following syntax,
        # for example:
        # $ pip install -e .[dev,test]
        extras_require={
            'dev': [],
            'test': ['pyfakefs'] + test_extra,
        },

        # If there are data files included in your packages that need to be
        # installed, specify them here.  If using Python 2.6 or less, then these
        # have to be included in MANIFEST.in as well.
        # Using include_package_data instead - and setuptools-git
        package_data={ 'cataloger': ['templates/*.tmpl']
        },

        # Although 'package_data' is the preferred approach, in some case you may
        # need to place data files outside of your packages. See:
        # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
        # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
        data_files=[],

#        test_suite='tests.test_manifest',
        test_suite='tests',

        # To provide executable scripts, use entry points in preference to the
        # "scripts" keyword. Entry points provide cross-platform support and allow
        # pip to create the appropriate form of executable for the target platform.
        entry_points={
        'console_scripts' : ['catalog=cataloger.main:main']
        },
)