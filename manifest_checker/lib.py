#!/usr/bin/env python
# coding=utf-8
"""
# manifest-checker : Implementation of lib.py

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
__created__ = '23 Mar 2016'

import click
import environment

pass_environment = click.make_pass_decorator(environment.CommandEnvironment)
