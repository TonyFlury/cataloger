#!/usr/bin/env python
"""
# manifest_check : Implementation of create and check commands

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

import cataloger.processor as processor
import cataloger.defaults as defaults
import pkg_resources

from templatelite import Renderer, registerModifier, UnexpectedFilterArguments

__version__ = "0.1"
__author__ = 'Tony Flury : anthony.flury@btinternet.com'
__created__ = '09 Feb 2016'

@click.command('check', help='Check local files against catalog')
@click.option('-m/-M', 'report_mismatch', is_flag=True, default='report_mismatch' in defaults.DEFAULT_REPORTON,
                help='Whether or not to report on files with mismatched checksums  - default Enabled.')
@click.option('-i/-I', 'report_missing', is_flag=True, default='report_missing' in defaults.DEFAULT_REPORTON,
                help='Whether or not to report on files with mismatched checksums - default Enabled.')
@click.option('-x/-X', 'report_extra', is_flag=True, default='report_extra' in defaults.DEFAULT_REPORTON,
                help='Whether or not to report on record_extra files - default Enabled.')
@click.pass_context
def check(ctx, **kwargs ):
    ctx.obj.update(kwargs)

    env = check_catalog(**ctx.obj)    # Indirect method to allow for API call

    if env.verbose > 0:
        report = Renderer( template_file=os.path.join(pkg_resources.resource_filename('cataloger','templates'),'final_check.tmpl'),
                           remove_indentation=False).from_context(
                                {'processed_count':env.processed_count},
                               {'report_excluded': env.report_category('excluded'),
                                'excluded_files':env.excluded_files},
                               {'report_extension': env.report_category('extension'),
                                'extensions':[ (e,c) for e,c in env.extension_counts.items()]},
                               {'report_mismatch' : env.report_category('mismatch'),
                                'mismatched': env.mismatched_files},
                                {'report_missing' : env.report_category('missing'),
                                 'missing': env.missing_files},
                                {'report_extra': env.report_category('exta'),
                                    'extra': env.extra_files},
                                {'verbose': env.verbose},
                                {'by_directory': env.catalog_summary_by_directory},
                            )
        kwargs.get('output', sys.stdout).write(report)

    if (env.report_category('mismatch') and len(env.mismatched_files) >0) or \
            (env.report_category('missing') and len(env.missing_files) > 0) or \
            (env.report_category('extra') and len(env.extra_files) > 0):
        sys.exit(1)

def check_catalog(**kwargs):
    try:
        env = processor.Cataloger(action='check', **kwargs)
    except processor.CatalogError as e:
        sys.stderr.write("Unable to read catalog file '{}' : {}\n".format(
                kwargs.get('catalog',defaults.DEFAULT_CATALOG_FILE), e))
        sys.exit(1)

    for directory, files in env.walk():

        for file in files:

            # If there is no signature for this file in the catalog, then mark this as record_extra file
            if not env.is_file_in_catalog(file_path=
                                          os.path.join(directory,file)):
                env.record_extra(rel_path=os.path.join(directory, file))
                continue

            catalog_signature = env.get_signature(rel_path=os.path.join(directory, file), from_catalog=True)
            file_signature =  env.get_signature(rel_path=os.path.join(directory, file), from_catalog=False)

            # If the signatures don't match - mark this as a mismatch
            if catalog_signature != file_signature:
                env.record_mismatch(rel_path=os.path.join(directory, file))
                continue

            env.record_ok(rel_path=os.path.join(directory, file))

        # Have processed all the files in the directory
        # so all non-processed files in this directory must be missing locally
        if env.is_directory_in_catalog(directory=directory):
            for file in env.get_non_processed(directory):
                env.record_missing(os.path.join(directory, file))

    return env

@registerModifier('format')
def format(var, *args, **kwargs):
    if len(args) > 1 or len(kwargs) >0:
        raise UnexpectedFilterArguments
    if var:
        return '{value:{format}}'.format(value=var, format=args[0])
    else:
        return '{value:{format}}'.format(value=' ', format=args[0] if args[0][-1] == 's' else (args[0][:-1]+'s' if args[0][-1]=='d' else args[0]))

@click.command('create', help='Create a new catalog')
@click.pass_context
def create(ctx, **kwargs):
    ctx.obj.update(kwargs)
    env = create_catalog(**ctx.obj)

    report = Renderer( template_file=os.path.join(pkg_resources.resource_filename('cataloger','templates'),'final_create.tmpl'),
                       remove_indentation=False).from_context(
                           {'processed_count': env.processed_count},
                           {'report_excluded': env.report_category('excluded'),
                            'excluded_files':env.excluded_files},
                           {'report_extension': env.report_category('extension'),
                            'extensions':[ (e,c) for e,c in env.extension_counts.items()] },
                           {'verbose': env.verbose},
                            {'by_directory': env.catalog_summary_by_directory},
                        )

    kwargs.get('output', sys.stdout).write(report)


def create_catalog(**kwargs):

    env = processor.Cataloger(action='create', **kwargs)

    for directory, files in env.walk():
        for file in files:
            signature = env.get_signature( rel_path=os.path.join(directory, file) )
            if signature:
                env.add_to_catalog(rel_path=os.path.join(directory, file), signature=signature)

    env.write_catalog()

    return env
