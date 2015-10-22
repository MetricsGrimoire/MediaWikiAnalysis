# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Bitergia
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

import sys
import time

import requests
import dateutil.parser

from wikianalysis.db.model import WikiPage, WikiPageRevision, Member


def str_to_datetime(ts):
    return dateutil.parser.parse(ts).replace(tzinfo=None)

def printout(str='\n'):
    if str != '\n':
        str += '\n'
    sys.stdout.write(str)
    sys.stdout.flush()

def printdbg(str='\n'):
    t = time.strftime("%d/%b/%Y-%X")
    printout("DBG: [" + t + "] " + str)


class ConfluenceAPIError(Exception):
    """Raised when an error occurs with Confluence API Client"""

    def __init__(self, code, error):
        self.code = code
        self.error = error

    def __str__(self):
        return "%s - %s" % (self.code, self.error)


class ConfluenceAPIClient(object):
    """Confluence API client"""

    URL = "%(base)s/rest/api/%(method)s"
    HEADERS = {'User-Agent': 'wikianalysis'}

    def __init__(self, url):
        self.url = url

    def contents(self, offset=None, limit=None, space=None, last_date=None):
        method = 'content/search'
        params = {'expand' : 'history,space'}

        if offset:
            params['start'] = offset
        if limit:
            params['limit'] = limit

        # Set confluence query parameter (cql)
        cql_params = []

        if space:
            cql_params.append('space = ' + space)
        if last_date:
            cql_params.append('lastmodified >= "' + last_date.strftime('%Y-%m-%d %H:%M') + '"')

        cql = ' and '.join(cql_params)
        cql += ' order by lastModified'

        params['cql'] = cql

        # Call REST API method
        result = self.call(method, params)

        return result

    def content_version(self, content_id, version):
        method = 'content/%s' % content_id
        params = {
                  'status' : 'historical',
                  'version' : version
                  }

        result = self.call(method, params)

        return result

    def call(self, method, params):
        url = self.URL % {'base' : self.url, 'method' : method}

        req = requests.get(url, params=params,
                           headers=self.HEADERS)

        printdbg("Confluence %s method called: %s" % (method, req.url))

        # Raise HTTP errors, if any
        req.raise_for_status()

        result = req.json()

        # Check for possible Confluent API errors
        if 'statusCode' in result:
            raise ConfluenceAPIError(result['statuscode'],
                                     result['message'])

        return result


class Confluence(object):

    def __init__(self, url, session):
        self.client = ConfluenceAPIClient(url)
        self.session = session
        self.members = {}

    def fetch(self, space=None, last_date=None):
        offset = 0
        limit = 25

        printout("Fetching contents from %s to %s" % (offset, offset + limit - 1))

        results = self.client.contents(offset=offset, limit=limit, space=space,
                                       last_date=last_date)
        results = results['results']

        while results:
            for r in results:
                if r['type'] not in ('page', 'blogpost'):
                    continue

                content = self.__parse_page(r)

                from_version = len(content.revisions) + 1

                versions = self.__fetch_versions(content.wikipage_id, from_version)

                for v in versions:
                    content.revisions.append(v)

                # Update 'updated_at' field
                if len(content.revisions) > 0:
                    content.updated_at = content.revisions[-1].date

                yield content

            offset += limit

            printout("Fetching contents from %s to %s" % (offset, offset + limit - 1))

            results = self.client.contents(offset=offset, limit=limit,
                                           space=space, last_date=last_date)
            results = results['results']

    def __fetch_versions(self, content_id, from_version):
        versions = []

        printout("Fetching versions of %s" % content_id)
        version_id = from_version

        fetching = True

        while fetching:
            printdbg("Fetching version : %s:%s" % (content_id, version_id))

            try:
                result = self.client.content_version(content_id, version_id)
            except requests.exceptions.HTTPError, e:
                if e.response.status_code != 404:
                    raise e
                fetching = False

            if not fetching:
                break

            version = self.__parse_content_version(result)
            versions.append(version)

            version_id += 1

        return versions

    def __parse_page(self, raw_page):
        wikipage_id = raw_page['id']

        page = WikiPage.as_unique(self.session,
                                  wikipage_id=wikipage_id)

        if not page.page_id:
            member = self.__parse_member(raw_page['history']['createdBy'])
            page.author = member
            page.type = raw_page['type']
            page.created_on = str_to_datetime(raw_page['history']['createdDate'])
            page.namespace = raw_page['space']['key']

        page.title = raw_page['title']

        return page

    def __parse_content_version(self, raw_version):
        wikipage_id = raw_version['id']
        message = raw_version['version']['message']
        number = raw_version['version']['number']
        when = str_to_datetime(raw_version['version']['when'])

        author = self.__parse_member(raw_version['version']['by'])

        version = WikiPageRevision.as_unique(self.session,
                                             wikipage_id=wikipage_id,
                                             rev_id=number)
        version.comment = message if message else None
        version.date = when
        version.author = author

        return version

    def __parse_member(self, raw_member):
        username = raw_member['username']

        member = self.members.get(username, None)

        if not member:
            member = Member.as_unique(self.session,
                                      username=username)
            member.name = raw_member['displayName']
            self.members[username] = member

        return member
