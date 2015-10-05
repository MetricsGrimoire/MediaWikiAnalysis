#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

from argparse import ArgumentParser

from wikianalysis.db.database import Database, DatabaseError
from wikianalysis.confluence import Confluence, ConfluenceAPIClient


def main():
    args = parse_args()

    try:
        db = Database(args.db_user, args.db_password, args.db_name,
                      args.db_hostname, args.db_port)
    except DatabaseError, e:
        raise RuntimeError(str(e))

    session = db.connect()
    try:
        backend = Confluence(args.url, session)

        last_activity = db.last_activity(session)

        for content in backend.fetch(args.space, last_activity):
            store(db, session, content)
    except ConfluenceAPIClient, e:
        raise e
        #s = "Error: %s\n" % str(e)
        #sys.stderr.write(s)
        #sys.exit(1)


def store(db, session, content):
    try:
        db.store(session, content)
    except Exception, e:
        raise RuntimeError(str(e))


def parse_args():
    parser = ArgumentParser(usage="Usage: '%(prog)s [options] <group>")

    # Database options
    group = parser.add_argument_group('Database options')
    group.add_argument('-u', '--user', dest='db_user',
                       help='Database user name',
                       default='root')
    group.add_argument('-p', '--password', dest='db_password',
                       help='Database user password',
                       default='')
    group.add_argument('-d', dest='db_name', required=True,
                       help='Name of the database where data will be stored')
    group.add_argument('--host', dest='db_hostname',
                       help='Name of the host where the database server is running',
                       default='localhost')
    group.add_argument('--port', dest='db_port',
                       help='Port of the host where the database server is running',
                       default='3306')

    # Positional arguments
    parser.add_argument('url', help='URL of the Confluence server')
    parser.add_argument('space', nargs='?', help='Confluence space',
                        default=None)

    # Parse arguments
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    import sys

    try:
        main()
    except RuntimeError, e:
        s = "Error: %s\n" % str(e)
        sys.stderr.write(s)
        sys.exit(1)
