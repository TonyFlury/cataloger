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
from create_manifest import get_sha224, walk_files

__version__ = "0.1"
__author__ = 'Tony Flury : anthony.flury@btinternet.com'
__created__ = '09 Feb 2016'


def read_manifest():
    manifest = {}
    try:
        with open('manifest.txt') as manifest_file:
            for entry in manifest_file:
                parts = entry.split('\t')
                manifest[parts[0].strip()] = parts[1].strip()
    except BaseException as e:
        print('Error reading manifest file : {}'.format(e))
        sys.exit(1)

    return manifest


if __name__ == "__main__":
    total, errors, extra, missing = 0,0,0,0
    manifest_dict = read_manifest()
    try:
        for file_path in walk_files():
            rel = os.path.relpath(file_path, os.getcwd())
            if rel in manifest_dict:
                signature = get_sha224(file_path)
                if not (signature == manifest_dict[rel]):
                    sys.stderr.write("Error : Signature mismatch for file '{}' {} {}\n".format(rel, signature, manifest_dict[rel])  )
                    del manifest_dict[rel]
                    errors += 1
                else:
                    total += 1
                    del manifest_dict[rel]
            else:
                sys.stderr.write("Warning : Extra local file detected - unable to verify: '{}'\n".format(rel))
                extra += 1
        if manifest_dict:
            for f in manifest_dict:
                sys.stderr.write("Error : Missing file '{}'\n".format(f))
                missing +=1

        sys.stdout.write("{} errors detected, {} extra local files, {} missing files\n".format(errors,extra,missing))
        sys.stdout.write("Verified {} Local files\n".format(total))

    except BaseException as e:
        sys.stderr('Fatal : Unable to verify local files : {}\n'.format(e))
        sys.exit(1)
