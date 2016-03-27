Defaults
========

By default the manifest suite with the default options as above will create a manifest for a Django projects (typically these projects exist as a nested set of directories which containt various types of source code, including python css, javascript and html files (and templates), as well as image files (gif, jpeg, png etc). A Django project will also contain directories and files which aren't part of the deployment, which don't need to be included in the integrity check by default.

If you don't use Django, you can still use the manifest suite to check your copies/deployments. Various options command line and Configuration File options exist to make the manifest suite usable including :

- check for different files types
- ignoring different directories

File Extension
        [u'.py', u'.html', u'.txt', u'.css', u'.js', u'.gif', u'.png', u'.jpg', u'.jpeg']

Top Level directories which are ignored :
    [u'static', u'env', u'htmlcov', u'media',u'build', u'dist', u'docs']

Default manifest file
    'manifest.txt'

Default hash/checksum algorithm.
        'sha224' if 'sha224' in hashlib.algorithms else hashlib.algorithms[0]

Reporting options
    skipped files and file extension totals are not reported on, but they can be included by using -k and -t options
    on the manifest command.

Checking options
    mismatched, missing and extra files are included in the reports. These checks can be disabled by using the
    -M, -I and -X options respectively.


