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

from environment import CommandEnvironment
from lib import pass_environment
from manifest_checker.environment import CommandEnvironment, ManifestError
from manifest_checker import defaults

from manifest_checker.lib import pass_environment

# from create_manifest import get_sha224, walk_files

__version__ = "0.1"
__author__ = 'Tony Flury : anthony.flury@btinternet.com'
__created__ = '09 Feb 2016'

@click.command('check', help='Check local files against manifest')
@click.option('-m/-M', 'report_mismatch', is_flag=True, default='report_mismatch' in defaults.DEFAULT_REPORTON,
                help='Whether or not to report on files with mismatched checksums  - default Enabled.')
@click.option('-i/-I', 'report_missing', is_flag=True, default='report_missing' in defaults.DEFAULT_REPORTON,
                help='Whether or not to report on files with mismatched checksums - default Enabled.')
@click.option('-x/-X', 'report_extra', is_flag=True, default='report_extra' in defaults.DEFAULT_REPORTON,
                help='Whether or not to report on record_extra files - default Enabled.')
@click.option('-g/-G', 'group',is_flag=True, default = defaults.DEFAULT_REPORT_GROUP,
                help='Turns off grouping of reported files.  Files in error are reported as they are found.')
@pass_environment
def check(env, **kwargs ):
    try:
        check_manifest(env,**kwargs)
    except ManifestError as e:
        sys.stderr.write("Unable to read manifest file '{}' : {}\n".format(
            self._manifest_name, e))
        sys.exit(1)


def check_manifest(env, **kwargs):
    assert isinstance(env, CommandEnvironment)

    env.start_command(subcommand='check', **kwargs)
    env.load_manifest()

    for directory, files in env.walk():

        for file in files:

            # If there is no signature for this file in the manifest, then mark this as record_extra file
            if not env.is_file_in_manifest(directory=directory,file=file):
                env.record_extra(rel_path=os.path.join(directory, file))
                continue

            manifest_signature = env.get_signature(rel_path=os.path.join(directory, file), manifest=True)
            file_signature =  env.get_signature(rel_path=os.path.join(directory, file), manifest=False)

            # If the signatures don't match - mark this as a mismatch
            if manifest_signature != file_signature:
                env.record_mismatch(rel_path=os.path.join(directory, file))
                continue

            env.mark_processed(rel_path=os.path.join(directory, file))

        # Have processed all the files in the directory
        # so all non-processed files in this directory must be missing locally
        if env.is_directory_in_manifest(directory=directory):
            for file in env.get_non_processed(directory):
                env.record_missing(os.path.join(directory, file))

    env._finalise()

@click.command('create', help='Create a new manifest')
@pass_environment
def create(env, **kwargs):
    assert isinstance(env,CommandEnvironment)

    env.start_command(subcommand='create', **kwargs)

    for directory, files in env.walk():
        for file in files:
            signature = env.get_signature( rel_path=os.path.join(directory, file) )
            if signature:
                env.list(rel_path=os.path.join(directory, file), signature=signature)

    env._finalise()