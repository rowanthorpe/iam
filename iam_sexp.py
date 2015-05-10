
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

# s-expression parser -> multilevel dict

import re
import itertools

t_re = r'''(?mx)
    \s*(?:
        (?P<bl>\()|
        (?P<br>\))|
        (?P<int>\-?\d+)|
        (?P<float>\-?\d+\.\d+)|
        (?P<str>"[^"]*")|
        (?P<none>NIL)|
        (?P<true>T)|
        (?P<atom>[^(^)\s]+)
       )'''

def parse_sexp(exp):
    exp = '\n'.join([x for x in exp.split('\n') if not re.match('^[ \t]*[;#]', x)])
    if exp[0] == "'":
        exp = exp[1:]
    stack = []
    buffer = []
    for termtypes in re.finditer(t_re, exp):
        term, value = [(t,v) for t,v in termtypes.groupdict().items() if v][0]
        if term == 'bl':
            stack.append(buffer)
            buffer = []
        elif term == 'br':
            if not stack:
                raise RuntimeError('Trouble with nesting of brackets')
            tmp, buffer = buffer, stack.pop(-1)
            buffer.append(tmp)
        elif term == 'int':
            buffer.append(int(value))
        elif term == 'float':
            buffer.append(float(value))
        elif term == 'str':
            buffer.append(value[1:-1])
        elif term == 'none':
            buffer.append(None)
        elif term == 'true':
            buffer.append(True)
        elif term == 'atom':
            buffer.append(value)
        else:
            raise NotImplementedError("Error: %r" % (term, value))
    if stack:
        raise RuntimeError('Trouble with nesting of brackets')
    dictbuffer = {}
    for sect in buffer[0]:
        sectkey = sect[0]
        sectval = sect[1:]
        dictbuffer[sectkey] = {}
        for opt in sectval:
            optkey = opt[0]
            if len(opt) == 2:
                optval = opt[1]
            else:
                optval = opt[1:]
            dictbuffer[sectkey][optkey] = optval
    return dictbuffer

def print_sexp(exp):

    ##TODO: the inverse of the above (dict->list on second layer down)

    exp = []
    for key, value in expdict.iteritems():
        exp.append([key, value])
    buffer = ''
    if type(exp) == type([]):
        buffer += '(' + ' '.join(print_sexp(x) for x in exp) + ')'
    elif type(exp) == type('') and re.search(r'[\s()]', exp):
        buffer += '"%s"' % repr(exp)[1:-1].replace('"', '\"')
    else:
        buffer += '%s' % exp
    return buffer
