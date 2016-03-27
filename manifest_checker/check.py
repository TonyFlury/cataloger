#!/usr/bin/env python
"""
# SuffolkCycleDjango : Implementation of check_manifest.py

Summary : 
    <summary of module/class being implemented>
Use Case : 
    As a <actor> I want <outcome> So that <justification>

Testable Statements :
    Can I <Boolean statement>
    ....
"""
import os
import os.path
import sys
import click
import defaults
from environment import CommandEnvironment

from lib import pass_environment

# from create_manifest import get_sha224, walk_files

__version__ = "0.1"
__author__ = 'Tony Flury : anthony.flury@btinternet.com'
__created__ = '09 Feb 2016'

@click.command('check', help='Check local files against manifest')
@click.option('-m/-M', 'report_mismatch', is_flag=True, default=True,
                help='Whether or not to report on files with mismatched checksums  - default Enabled.')
@click.option('-i/-I', 'report_missing', is_flag=True, default=True,
                help='Whether or not to report on files with mismatched checksums - default Enabled.')
@click.option('-x/-X', 'report_extra', is_flag=True, default=True,
                help='Whether or not to report on extra files - default Enabled.')
@click.option('-g/-G', 'group',is_flag=True, default = True,
                help='Turns off grouping of reported files.  Files in error are reported as they are found.')
@pass_environment
def check(env, **kwargs ):
    assert isinstance(env, CommandEnvironment)
    env.update(subcommand='check', **kwargs)
    env.load_manifest()
    for rel_path in env.walk():
        manifest_signature = env.get_signature(rel_path=rel_path, manifest=True)
        file_signature =  env.get_signature(rel_path=rel_path, manifest=False)
        if not manifest_signature:
            env.extra(rel_path=rel_path)
            continue

        if manifest_signature != file_signature:
            env.mismatch( rel_path=rel_path )
            continue
        else:
            env.mark_processed(rel_path=rel_path)