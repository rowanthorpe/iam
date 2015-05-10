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
import socket, xmpp, jabberbot

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

bot_room = conf_get(config, 'bot', 'room')
bot_user = conf_get(config, 'bot', 'user')
bot_password = conf_get(config, 'bot', 'password')
bot_nick = conf_get(config, 'bot', 'nick', fallback=True)

##NB:
## * chat-server IP must have access to iamd-server
## * bot-server's IP and user/pass must have access to chat-server
## * bot-server must have python-jabberbot installed (python-xmpp is a dependency of it so we
##   know we'll have that)

##TODO:
## * Presently the server only returns all statuses (not just latest!) for everyone for now,
##   regardless the request-type or args. Once it does though, this bot is already sending the
##   right requests for it ;-)

class IamJabberBot(jabberbot.JabberBot):

    def __connect(self, content):

##TODO: other protocols, SSL, etc

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('{}{}'.format(proto, server), port))
        s.sendall(content)
        reply = ''
        while 1:
            data = s.recv(1024)
            if data == '':
                break
            reply += data
        s.shutdown(socket.SHUT_WR)
        s.close()
        if not reply:
            return('ERROR: no reply from server\n')
        else:
            return(reply)

    def __reply(self, msg, response):

##NB: Deliberately do this for manually forced plaintext, rather than circuitous/heuristic
##    text->html->text baked-in method

        to_send = xmpp.protocol.Message(body=response)
        to_send.setTo(self.get_sender_username(msg))
        to_send.setThread(msg.getThread())
        to_send.setType(msg.getType())
        self.send_message(to_send)

    @jabberbot.botcmd
    def status(self, msg, args):
        """Push an update to iamd, return server response"""
        if args:
            response = self.__connect('STATUS\n{}\n{}\n'.format(self.get_sender_username(msg), args))
        else:
            response = 'ERROR: specify text to send'
        self.__reply(msg, response)

    @jabberbot.botcmd
    def get(self, msg, args):
        """
        Get output from iamd:
          args:
            'latest [user|-]': get latest statuses for 'user' ('-' = self, '' = all users)
            'all [user|-]': get all non-archived statuses for 'user' ('-' = self, '' = all users)
            'byuser': get all non-archived statuses, grouped by user
        """
        args_list = args.split(' ')
        if len(args_list > 1) and args_list[1] == '-':
            args_list[1] = self.get_sender_username(msg)
        response = self.__connect('GET /{}.html HTTP/1.0\r\n\r\n'.format('/'.join(args_list)))
        response = '\r\n\r\n'.join(response.split('\r\n\r\n')[1:])
        response = Popen(['html2text', '-utf8'], stdin=PIPE).communicate(input=response)
        self.__reply(msg, response)

if __name__ == '__main__':
    bot = IamJabberBot(bot_user, bot_password, command_prefix='!')

##TODO: check if this is better (can even work?)...
##    bot.serve_forever(connect_callback=lambda: bot.muc_join_room(bot_room, username=bot_nick),
##                      disconnect_callback=lambda: bot.muc_part_room(bot_room, username=bot_nick))

    bot.serve_forever(connect_callback=lambda: bot.join_room(bot_room, username=bot_nick))
