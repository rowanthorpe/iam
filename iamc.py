#!/usr/bin/python
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
    from iam_common import conf_read, conf_get
except ImportError:
    sys.path.insert(0, '')
    from iam_common import conf_read, conf_get
import socket, re, subprocess, termios

VERSION = '0.1'

##TODO: argparse, including --help, --version, --verbose, --no-sys-config, --no-home-config

if len(sys.argv) > 1:
    config = conf_read(sys.argv[1])
else:
    config = conf_read()
server = conf_get(config, 'common', 'server')
port = conf_get(config, 'common', 'port', type_=int, fallback=True)
proto = conf_get(config, 'common', 'proto', fallback=True)
user = conf_get(config, 'common', 'user', fallback=True)

##TODO:
#password = conf_get(config, 'common', 'password')

client_browser = conf_get(config, 'client', 'browser', fallback=True)
client_use_xterm = conf_get(config, 'client', 'use_xterm', type_=bool, fallback=True)
client_xterm = conf_get(config, 'client', 'xterm', fallback=True)

##NB:
## * User-specific views not implemented on server yet, so for now ":GETUID:[user]" just outputs
##   the same as ":GET"

def connect(content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, port))
    s.sendall(content)
    s.shutdown(socket.SHUT_WR)
    reply = ''
    while 1:
        data = s.recv(1024)
        if data == '':
            break
        reply += data
    if not reply:
        return('PROBLEM: no reply from server\n')
    else:
        return(reply)
    s.close()

def post_status(msg):
    reply = connect('STATUS\n{}\n{}\n'.format(user, msg))
    sys.stderr.write(reply)

def get_statuses(_user='index'):
    if _user == '':
        _user = user
    if client_browser in ('html2text', 'raw', 'less'):
        reply = ''.join(split_header.split(connect('GET /{}.html HTTP/1.0\r\n\r\n'.format(_user)))[1:])
        if client_browser == 'html2text':
            pipe = subprocess.Popen(('html2text', '-utf8'), stdin=subprocess.PIPE)
            pipe.communicate(input='{}\n'.format(reply))
        elif client_browser == 'less':
            pipe = subprocess.Popen(('sh', '-c', 'html2text -utf8 | less -S'), stdin=subprocess.PIPE)
            pipe.communicate(input='{}\n'.format(reply))
        elif client_browser == 'raw':
            sys.stdout.write('{}\n'.format(reply))
    else:
        url = '{}{}:{}/{}.html'.format(proto, server, port, _user)
        if client_browser in ['lynx', 'w3m', 'links']:
            if client_use_xterm:

##FIXME:
##                subprocess.Popen(('setsid', client_xterm, '-title', 'Statuses', '-e', client_browser, url))

                subprocess.call((client_browser, url))
                subprocess.call(('stty', 'sane'))
            else:
                subprocess.call((client_browser, url))
                subprocess.call(('stty', 'sane'))
        else:
            subprocess.Popen((client_browser, url))

if __name__ == '__main__':
    split_header = re.compile('\r\n\r\n')

    if len(sys.argv) < 2:
        finished = False
        while not finished:
            try:
                termios.tcflush(sys.stdin, termios.TCIOFLUSH)
                line = raw_input('I am >> ')
                if line:
                    if line == '.':
                        finished = True
                    elif line == ':GET':
                        get_statuses(None)
                    elif line[:8] == ':GETUID:':
                        get_statuses(line[8:])
                    else:
                        post_status(line)
            except KeyboardInterrupt:
                sys.stderr.write('* Ctrl-c\n'); finished = True
            except EOFError:
                sys.stderr.write('* Ctrl-d\n'); finished = True
    elif sys.argv[1] == ':GET':
        get_statuses(None)
    elif sys.argv[1][:8] == ':GETUID:':
        get_statuses(sys.argv[1][8:])
    else:
        post_status(' '.join(sys.argv[1:]))
