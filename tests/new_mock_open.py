#!/usr/bin/env python
# coding=utf-8
"""
# manifest-checker : Implementation of new_mock_open

Summary : 
    <summary of module/class being implemented>
Use Case : 
    As a <actor> I want <outcome> So that <justification>

Testable Statements :
    Can I <Boolean statement>
    ....
"""
import six

if six.PY2:
    from mock import MagicMock, sentinel
else:
    from unittest.mock import MagicMock, sentinel

__version__ = "0.1"
__author__ = 'Tony Flury : anthony.flury@btinternet.com'
__created__ = '09 Mar 2018'

file_spec = None


def _iterate_read_data(read_data):
    # Helper for mock_open:
    # Retrieve lines from read_data via a generator so that separate calls to
    # readline, read, and readlines are properly interleaved
    sep = b'\n' if isinstance(read_data, bytes) else '\n'
    data_as_list = [l + sep for l in read_data.split(sep)]

    if data_as_list[-1] == sep:
        # If the last line ended in a newline, the list comprehension will have an
        # extra entry that's just a newline.  Remove this.
        data_as_list = data_as_list[:-1]
    else:
        # If there wasn't an extra newline by itself, then the file being
        # emulated doesn't have a newline to end the last line  remove the
        # newline that our naive format() added
        data_as_list[-1] = data_as_list[-1][:-1]

    for line in data_as_list:
        yield line


def new_mock_open(mock=None, read_data=''):
    """
    A helper function to create a mock to replace the use of `open`. It works
    for `open` called directly or used as a context manager.

    The `mock` argument is the mock object to configure. If `None` (the
    default) then a `MagicMock` will be created for you, with the API limited
    to methods or attributes available on standard file handles.

    `read_data` is a string for the `read` methoddline`, and `readlines` of the
    file handle to return.  This is an empty string by default.
    """
    def _readlines_side_effect(*args, **kwargs):
        if handle.readlines.return_value is not None:
            return handle.readlines.return_value
        return list(_state[0])

    def _read_side_effect(*args, **kwargs):
        if handle.read.return_value is not None:
            return handle.read.return_value
        return type(read_data)().join(_state[0])

    def _readline_side_effect():
        if handle.readline.return_value is not None:
            while True:
                yield handle.readline.return_value
        for line in _state[0]:
            yield line


    global file_spec
    if file_spec is None:
        # set on first use
        if six.PY3:
            import _io
            file_spec = list(set(dir(_io.TextIOWrapper)).union(set(dir(_io.BytesIO))))
        else:
            file_spec = file

    if mock is None:
        mock = MagicMock(name='open', spec=open)

    handle = MagicMock(spec=file_spec)
    handle.__enter__.return_value = handle

    _state = [_iterate_read_data(read_data), None]

    handle.write.return_value = None
    handle.read.return_value = None
    handle.readline.return_value = None
    handle.readlines.return_value = None

    handle.read.side_effect = _read_side_effect
    _state[1] = _readline_side_effect()
    handle.readline.side_effect = _state[1]
    handle.readlines.side_effect = _readlines_side_effect

    handle.__iter__.side_effect = _readline_side_effect

    def reset_data(*args, **kwargs):
        _state[0] = _iterate_read_data(read_data)
        if handle.readline.side_effect == _state[1]:
            # Only reset the side effect if the user hasn't overridden it.
            _state[1] = _readline_side_effect()
            handle.readline.side_effect = _state[1]
        return sentinel.DEFAULT

    mock.side_effect = reset_data
    mock.return_value = handle
    return mock