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

import manifest_checker.processor as environment
import manifest_checker.defaults as defaults

from templatelite import Renderer

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
@click.pass_context
def check(ctx, **kwargs ):
    ctx.obj.update(kwargs)

    check_manifest(**ctx.obj)    # Indirect method to allow for API call


def check_manifest(**kwargs):
    try:
        env = environment.ManifestProcessor(action='check', **kwargs)
    except environment.ManifestError as e:
        sys.stderr.write("Unable to read manifest file '{}' : {}\n".format(
                kwargs.get('manifest',defaults.DEFAULT_MANIFEST_FILE), e))
        sys.exit(1)

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

    report = Renderer( template_file=os.path.join(os.path.dirname(__file__,),'templates','final_check.tmpl'),
                       remove_indentation=False).from_context(
                           {'report_skipped': env._report_skipped,
                            'skipped_files':env.skipped_files},
                           {'report_extension': env._report_extension,
                            'extensions':env.extension_counts},
                           {'report_mismatch' : env._report_mismatch,
                            'mismatched': env.mismatched_files},
                            {'report_missing' : env._report_missing,
                             'missing': env.missing_files},
                            {'report_extra': env._report_extra,
                                'extra': env.extra_files}, )

    kwargs.get('output', sys.stdout).write(report)

    print('-'*80)

    env.final_report()

@click.command('create', help='Create a new manifest')
@click.pass_context
def create(ctx, **kwargs):
    ctx.obj.update(kwargs)
    create_manifest(**ctx.obj)

def create_manifest(**kwargs):

    env = environment.ManifestProcessor( action='create', **kwargs )

    for directory, files in env.walk():
        for file in files:
            signature = env.get_signature( rel_path=os.path.join(directory, file) )
            if signature:
                env.manifest_write(rel_path=os.path.join(directory, file), signature=signature)

    env.final_report()