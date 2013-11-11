#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This script parse IRC logs from Wikimedia 
# and store them in database
# 
# Copyright (C) 2012-2013 Bitergia
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
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#

from optparse import OptionParser
import sys, traceback
import MySQLdb
import urllib2, urllib
from xml.dom.minidom import parseString

def open_database(myuser, mypassword, mydb):
    con = MySQLdb.Connect(host="127.0.0.1",
                          port=3306,
                          user=myuser,
                          passwd=mypassword,
                          db=mydb,
                          charset='utf8')
    # cursor = con.cursor()
    # return cursor
    return con

def close_database(con):
    con.close()

def read_options():
    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 0.1")
    parser.add_option("--url",
                      action="store",
                      dest="url",
                      help="MediaWiki URL")
    parser.add_option("-d", "--database",
                      action="store",
                      dest="dbname",
                      help="Database where information is stored")
    parser.add_option("--db-user",
                      action="store",
                      dest="dbuser",
                      default="root",
                      help="Database user")
    parser.add_option("--db-password",
                      action="store",
                      dest="dbpassword",
                      default="",
                      help="Database password")
    parser.add_option("-g", "--debug",
                      action="store_true",
                      dest="debug",
                      default=False,
                      help="Debug mode")
    (opts, args) = parser.parse_args()
    # print(opts)
    if len(args) != 0:
        parser.error("Wrong number of arguments")

    if not(opts.dbname and opts.dbuser and opts.url):
        parser.error("--database --db-user and --url are needed")
    return opts

def escape_string (message):
    if "\\" in message:
        message = message.replace("\\", "\\\\")
    if "'" in message:    
        message = message.replace("'", "\\'")
    return message
 
def get_last_date(cursor):
    query =  "SELECT MAX(date) FROM wiki_pages_revs"
    cursor.execute(query)
    return cursor.fetchone()[0]

def create_tables(cursor, con = None):
    query = "CREATE TABLE IF NOT EXISTS wiki_pages_revs (" + \
           "id int(11) NOT NULL AUTO_INCREMENT," + \
           "rev_id int," + \
           "page_id int," + \
           "user VARCHAR(255) NOT NULL," + \
           "date DATETIME NOT NULL," + \
           "comment TEXT," + \
           "PRIMARY KEY (id)" + \
           ") ENGINE=MyISAM DEFAULT CHARSET=utf8"
    cursor.execute(query)

    query = "CREATE TABLE IF NOT EXISTS wiki_pages (" + \
           "page_id int(11)," + \
           "title VARCHAR(255) NOT NULL," + \
           "PRIMARY KEY (page_id)" + \
           ") ENGINE=MyISAM DEFAULT CHARSET=utf8"
    cursor.execute(query)

    query = "CREATE TABLE IF NOT EXISTS people (" + \
           "id int(11) NOT NULL AUTO_INCREMENT," + \
           "name VARCHAR(255) NOT NULL," + \
           "PRIMARY KEY (id)" + \
           ") ENGINE=MyISAM DEFAULT CHARSET=utf8"
    cursor.execute(query)
    return


def insert_page(cursor, pageid, title):
    q = "INSERT INTO wiki_pages (page_id,title) ";
    q += "VALUES (%s, %s)"
    try:
        cursor.execute(q, (pageid, title))
    except:
        print (pageid+" "+title+" was already in the db")

def insert_revision(cursor, pageid, revid, user, date, comment):
    q = "INSERT INTO wiki_pages_revs (page_id,rev_id,date,user,comment) ";
    q += "VALUES (%s, %s, %s, %s, %s)"
    try:
        cursor.execute(q, (pageid,revid,date,user,comment))
    except:
        print (pageid+" "+revid+" "+ user +" was already in the db")

def process_revision_by_id(cursor, revid):
    # Get revision info
    # http://mediawiki.org/w/api.php?action=query&prop=revisions&revids=1
    api_url = opts.url + "/" + "api.php"
    allchanges_query = "action=query&prop=revisions&revids="+revid+"&format=xml"
    rev_query = api_url + "?" + allchanges_query
    # if (opts.debug): print("Rev query: " + rev_query)
    revision = urllib2.urlopen(rev_query)
    revision_data = revision.read().strip('\n')
    xmlrevision = parseString(revision_data)
    revision_node = xmlrevision.getElementsByTagName('rev')[0]
    pageid = xmlrevision.getElementsByTagName('page')[0].attributes['pageid'].value
    user = revision_node.attributes['user'].value
    comment = revision_node.attributes['comment'].value
    date = revision_node.attributes['timestamp'].value
    insert_revision(cursor, pageid, revid, user, date, comment)

def process_revisions(cursor, pageid, xmlrevs):
    for rev in xmlrevs.getElementsByTagName('rev'):
        # count_revs += 1
        try:
            revid = rev.attributes['revid'].value
            timestamp = rev.attributes['timestamp'].value
            comment = rev.attributes['comment'].value
            if rev.hasAttribute('user'):
                user = rev.attributes['user'].value
            else: user = rev.attributes['userhidden'].value
            # if (opts.debug): print (pageid +" " + revid+" "+user+" "+timestamp+" "+comment)
            insert_revision (cursor, pageid, revid, user, timestamp, comment)
        except:
            print rev.attributes.items()
            print ("ERROR. Revision data wrong " +revid)
            traceback.print_exc(file=sys.stdout)
        # if (count_revs % 1000 == 0): print (count_revs)

def process_page_revisions(cursor, pageid, urltitle, last_date):
    api_url = opts.url + "/" + "api.php"

    page_allrevs_query = "action=query&prop=revisions&"+urltitle
    # TODO: max limit is 500. We should iterate here
    page_allrevs_query += "&rvlimit=max&format=xml"
    if (last_date):
        page_allrevs_query += "&rvstart="+last_date+"&rvdir=newer"
    if (opts.debug): print(api_url+"?"+page_allrevs_query)
    page_revs = urllib2.urlopen(api_url+"?"+page_allrevs_query)
    page_revs_list = page_revs.read().strip('\n')
    xmlrevs = parseString(page_revs_list)
    process_revisions(cursor, pageid, xmlrevs)

def process_pages(cursor, xmlpages, last_date, revisions = True):
    apcontinue = None
    for entry in xmlpages.getElementsByTagName('allpages'):
        if entry.hasAttribute('apcontinue'):
            apcontinue = entry.attributes['apcontinue'].value.encode('utf-8')
            # if (opts.debug): print("Continue from:"+apcontinue)
            break
    for page in xmlpages.getElementsByTagName('p'):
        title = page.attributes['title'].value.encode('utf-8')
        urltitle = urllib.urlencode({'titles':title})
        pageid = page.attributes['pageid'].value        
        insert_page (cursor, pageid, title)
        if (revisions):
            process_page_revisions(cursor, pageid, urltitle, last_date)
    return apcontinue

def process_changes(cursor, xmlchanges):
    rccontinue = None
    for entry in xmlchanges.getElementsByTagName('recentchanges'):
        if entry.hasAttribute('rccontinue'):
            rccontinue = entry.attributes['rccontinue'].value.encode('utf-8')
            #  if (opts.debug): print("Continue changes from:"+rccontinue)
            break
    for change in xmlchanges.getElementsByTagName('rc'):
        revtype = change.attributes['type'].value.encode('utf-8')
        # only analyzing editions
        if (revtype != "edit"): continue
        # page info
        title = change.attributes['title'].value.encode('utf-8')
        pageid = change.attributes['pageid'].value.encode('utf-8')
        insert_page(cursor, pageid, title)
        revid = change.attributes['revid'].value.encode('utf-8')
        # TODO: we can get several revisions at the same time
        process_revision_by_id(cursor, revid)
        # insert_change (cursor, changeid, title)
    return rccontinue

def process_changes_all(cursor, last_date):
    # http://www.mediawiki.org/w/api.php?action=query&list=recentchanges&rclimit=max&rcend=2013-11-09T05:51:59Z
    api_url = opts.url + "/" + "api.php"
    limit = "max"
    allchanges_query = "action=query&list=recentchanges&rclimit="+limit+"&rcend="+last_date+"&format=xml"
    url_query = api_url + "?" + allchanges_query
    rccontinue = ''
    while (rccontinue is not None):
        url_changes = url_query
        if (rccontinue != ''): url_changes += "&rccontinue="+rccontinue
        if (opts.debug): print("Changes query: " + url_changes)
        changes = urllib2.urlopen(url_changes)
        changes_list = changes.read().strip('\n')
        print(changes_list)
        xmlchanges = parseString(changes_list)
        rccontinue = process_changes(cursor, xmlchanges)

def process_all(cursor):
    count_pages = 0

    # http://openstack.redhat.com/api.php?action=query&list=allpages&aplimit=500
    api_url = opts.url + "/" + "api.php"
    if (opts.debug): print("API URL: " + api_url)

    # Read all WikiMedia pages and the analyze all revisions
    # limit = "500"
    limit = "max"
    allpages_query = "action=query&list=allpages&aplimit="+limit+"&format=xml"
    if (opts.debug): print("Pages query: " + allpages_query)
    apcontinue=''
    while (apcontinue is not None):
        pages = urllib2.urlopen(api_url+"?"+allpages_query+"&apcontinue="+apcontinue)
        pages_list = pages.read().strip('\n')
        xmlpages = parseString(pages_list)
        apcontinue = process_pages(cursor, xmlpages, last_date)
        count_pages += len(xmlpages.getElementsByTagName('p'))
    con.commit()

    # print("Total revisions: %s" % (count_revs))
    print("Total pages: %s" % (count_pages))


if __name__ == '__main__':
    opts = None
    opts = read_options()

    con = open_database(opts.dbuser, opts.dbpassword, opts.dbname)
    cursor = con.cursor()
    create_tables(cursor)
    # Incremental support
    last_date = get_last_date(cursor)
    if (last_date):
        last_date = last_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        if (opts.debug): print ("Starting from: " + last_date)
        # We use a different API for getting changes: incremental mode
        process_changes_all(cursor, last_date)
    else: process_all(cursor)

    close_database(con)
    sys.exit(0)