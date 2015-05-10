#!/bin/sh

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

set -e

_status=2
_status_msg='Internal error'
trap 'printf %s\\n "$_status_msg" >&2' EXIT

##NB: In the interests of being a minimal/zero-deps client, this doesn't source
##    iam_config.l, so set the below manually
_server=''
_port=4004
_user="`id -un`" #hardcode _user='name' for speedup (or if iam user != local user)

test -n "$_server" # sanity check

case "$(printf 'STATUS\n%s\n%s\n' "$_user" "$*" | nc "$_server" "$_port")" in
OK)
    _status=0
    _status_msg='OK'
    ;;
*)
    _status=1
    _status_msg='PROBLEM submitting status'
    ;;
esac
exit $_status
