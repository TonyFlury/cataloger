#!/usr/bin/env python
# coding=utf-8
"""
# cataloger : Implementation of defaults.py

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
__created__ = '22 Mar 2016'

import hashlib

DEFAULT_EXTENSIONS = {u'.py', u'.html', u'.txt', u'.css', u'.js', u'.gif', u'.png', u'.jpg', u'.jpeg'}
DEFAULT_IGNOREDIRECTORY = {u'static', u'htmlcov', u'media',u'build', u'dist', u'docs'}
DEFAULT_CATALOG_FILE = 'catalog.cat'
DEFAULT_CONFIG_FILE = 'catalog.cfg'
DEFAULT_HASH = 'sha224' if 'sha224' in hashlib.algorithms_available else list(hashlib.algorithms_available)[0]
DEFAULT_REPORTON = ['report_missing','report_extra','report_mismatch','report_excluded']
DEFAULT_VERBOSE = '1'
DEFAULT_REPORT_EXTENSIONS = True
DEFAULT_REPORT_GROUP = True
ALL_REPORTON_OPTIONS = ['report_missing','report_extra','report_mismatch', 'report_excluded']
