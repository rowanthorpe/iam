
# -*- coding: utf-8 -*-

# © Copyright 2014, 2015 Rowan Thorpe
#
# This file is part of iam
#
# iam is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iam is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iam.  If not, see <http://www.gnu.org/licenses/>.

import sys
try:
    import iam_sexp
except ImportError:
    sys.path.insert(0, '')
    import iam_sexp
import os

def _rmerge(original, update, resolve=lambda x, y: y):
    """
    Recursively merge two dictionaries non-destructively, using the "resolve" lambda to
    resolve conflicts (default to overwriting with the second option of the two).

    Args:
      original, update (dicts)
      resolve (routine)

    Returns:
      dict

    Doctests:
    >>> z = {'a': 1, 'c': 3, 'b': 2}
    >>> _merge(z, z)
    {u'a': 1, u'c': 3, u'b': 2}
    >>> _merge(z, z, lambda x,y: x+y)
    {u'a': 2, u'c': 6, u'b': 4}
    """
    result = dict(original)
    for key, value in dict(update).iteritems():
        if key in result:
            if isinstance(value, dict):
                result[key] = _rmerge(result[key], value)
            else:
                result[key] = resolve(result[key], value)
        else:
            result[key] = value
    return result

def conf_read(conf=None):
    confbuffer = {
        'defaults': {
            'port':      4004,
            'proto':     'http://',
            'user':      os.getlogin(),
            'browser':   'lynx',
            'use_xterm': False,
            'xterm':     'x-terminal-emulator',
            'nick':      'iambot',
        }
    }
    _configfiles = ['/etc/iam_config.l', '{}/iam_config.l'.format(os.path.expanduser('~'))]
    if conf:
        _configfiles.append(conf)
    else:
        _configfiles.append('./iam_config.l')
    _found_configfile = False
    for _configfile in _configfiles:
        try:
            with open(_configfile, 'r') as _cf:
                _content = _cf.read()
            if _content:
                _found_configfile = True
                confbuffer = _rmerge(confbuffer, iam_sexp.parse_sexp(_content))
        except IOError:
            pass
    if not _found_configfile:
        raise RuntimeError('No config file found in {}'.format(_configfiles))
    return confbuffer

def conf_get(conf, sect, key, type_=str, fallback=False):
    try:
        retval = conf[sect][key]
    except KeyError:
        if fallback:
            retval = conf['defaults'][key]
        else:
            raise
    if type_ is not None:
        retval = type_(retval)
    return retval
