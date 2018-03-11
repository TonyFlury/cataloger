#!/usr/bin/env python
# coding=utf-8
"""
# manifest-checker : Implementation of main.py

Implementation of the manifest-checker cli using click

The main CLI interface - implemented using the click framework.
"""

import os
import click
import hashlib
import defaults
import pkg_resources

from manifest_checker import version
import commands


def validate_report_out(ctx, param, value):
    if value is None:
        return None

    if value.name == '-':
        raise click.BadParameter("Cannot use stdout for this parameter : use '-v/--verbose 3' instead")
    else:
        return value

def validate_root(ctx, param, value):
    if os.path.isdir(value):
        return value
    else:
        raise click.BadParameter("Must be a existing directory")

def get_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('manifest : version {}'.format(
            pkg_resources.require("manifest-checker")[0].version))
    ctx.exit()


def validate_extension(ctx, param, value):
    if any(True for x in value if x[0] != "."):
        raise click.BadParameter("file extensions must start with a '.'")

    return value


@click.group()
@click.pass_context
@click.version_option(version=version.__version__, )
@click.option('--version', is_flag=True, callback=get_version, expose_value=False, is_eager=True)
@click.option('-v', '--verbose', type=click.Choice(['0', '1', '2', '3']), default=defaults.DEFAULT_VERBOSE)

@click.option('-h', '--hash',
              type=click.Choice(hashlib.algorithms_available),
              default=defaults.DEFAULT_HASH, help='The hash algorithm to use in order to compare file contents.')

@click.option('-m', '--manifest', envvar='MANIFEST',
              default=defaults.DEFAULT_MANIFEST_FILE,
              help='The manifest file to use - default is `{}`'.format(defaults.DEFAULT_MANIFEST_FILE))

@click.option('-r', '--root', metavar='ROOT', default=os.getcwd(), callback=validate_root,
              help='The root directory to create the manifest from, or check the manifest against.')

@click.option('-f','--exclude_filter', metavar='FILTER', multiple=True, default='',
              help='A standard file match wildcard - files/directories are excluded if they match this value')
@click.option('+f','--include_filter', metavar='FILTER', multiple=True, default='',
              help='A standard file match wildcard - files/directories are included if they match this value')

@click.option('+e', '--add_extension', multiple=True, metavar='EXTENSION', default='',
              help='Add an file extension to the to the set of those to be processed',
              callback=validate_extension)
@click.option('-e', '--rm_extension', multiple=True, metavar='EXTENSION', default='',
              help='remove an file extension to the set of those to be processed',
              callback=validate_extension)

@click.option('+d', '--add_directory', multiple=True, metavar='DIRECTORY', default='',
              help='Add a directory to the list of top level directories to be ignored',
              )
@click.option('-d', '--rm_directory', multiple=True, metavar='DIRECTORY', default='',
              help='Remove a directory to the list of top level directories to be ignored',
              )

@click.option('-k/-K', 'report_skipped', is_flag=True, default='report_skipped' in defaults.DEFAULT_REPORTON,
              help='Whether or not to report (in summary) on skipped files')

@click.option('-t/-T', 'report_extensions', is_flag=True, default=defaults.DEFAULT_REPORT_EXTENSIONS,
              help='Whether or not to report (in summary) on checked file extensions')

@click.option('-c', 'config', is_flag=False, default='',
              help='The file name of the config file')
@click.option('-N' 'no_config', is_flag=True, default = False,
              help='Ignore the config file and use the command line options only' )
def primary(ctx, **kwargs):
    """
    A utility to traverse a local directory tree under a given directory and either build or
    check against a manifest file with a hash value for each file within that directory tree.

    By default the manifest commands look for file types which are used by a typical Python or
    Django application :

    \b
        Default Extensions = ['.py','.html','.txt','.css','.js','.gif','.png','.jpg','.jpeg']

    Extra extensions can be included in the manifest by using the `-e, --extension` option.
    When the `-E, --clearExtensions` option is used this will ignore the default extensions above
    and ONLY use those extensions added by the `-e` option. Using `-E, --clearExtensions` without at
    least one `-e` option is an error.

    By default the manifest on creation and checking ignores a number of top level directories
    (i.e. those directly under the current directory). Typically these are directories which are
    used for development/testing, but which are not deployed (they are either recreated on deployment,
    they are dynamically created, or are present only for testing/development purposes). The default
    manifest_write of these ignore directories are :

    \b
        ['static','media','htmlcov','env','docs','build','dist']
        'htmlcov' is included in case you use the coverage tool with html reporting
        'env' is included in case you use the Pycharm IDE
        'build' & 'dist' are created by setuptools
        'docs' is a common directory for a number of documentation tools - including sphinx

    Extra top level directories can be ignored in the manifest by using the `-i,--ignoreDirectory` option.
    When the `-D,--clearDirectory` option is used this will ignore the default ignored directories above and
    ONLY use those extensions added by the `-e` option.

    If the file 'manifest.cfg' exists within the current directory the options specified in that file are used
    initially, with options specified on the command line being considered after those.

    The -c option can be used to give another file name for the config file.
    The -N option can be used to ignore the config file.
    """
#    if not kwargs['extension'] and defaults.DEFAULT_EXTENSIONS:
#        raise click.BadOptionUsage('-E should not be used on it\'s own - specify at least one -e option' )
#        sys.exit(1)

    ctx.obj = kwargs

@click.command('test')
@click.pass_context
def test(ctx,**kwargs):
    for k, v in ctx.obj.items():
        print(k, v)

def main():
    primary.add_command(test)
    primary.add_command(commands.check)
    primary.add_command(commands.create)
    primary()

if __name__ == '__main__':
    main()