#!/usr/bin/env python
"""
# SuffolkCycleDjango : Implementation of create_manifest.py

Summary : 
    <summary of module/class being implemented>
Use Case : 
    As a <actor> I want <outcome> So that <justification>

Testable Statements :
    Can I <Boolean statement>
    ....
"""
import sys
import os
import hashlib
import click
import defaults
from environment import CommandEnvironment

from lib import pass_environment


__version__ = "0.1"
__author__ = 'Tony Flury : anthony.flury@btinternet.com'
__created__ = '09 Feb 2016'


@click.command('create', help='Create a new manifest')
@pass_environment
def create(env, **kwargs):
    assert isinstance(env,CommandEnvironment)

    env.update(subcommand='create', **kwargs)

    for rel_path in env.walk():
        signature = env.get_signature( rel_path=rel_path )
        if signature:
            env.list(rel_path=rel_path, signature=signature)