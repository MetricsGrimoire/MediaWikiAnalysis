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
import sys
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

def insert_page(cursor, pageid, title):
    title = escape_string (title)
    q = "INSERT INTO wiki_pages (page_id,title) ";
    q += "VALUES ('" + pageid + "','" + title + "')"
    cursor.execute(q)

def insert_revision(cursor, pageid, revid, user, date, comment):
    comment = escape_string (comment)
    user = escape_string (user)
    q = "INSERT INTO wiki_pages_revs (page_id,rev_id,date,user,comment) ";
    q += "VALUES (";
    q += "'" + pageid + "','" + revid + "','" + date + "','";
    q +=  user + "','"+ comment +"')"
    if (opts.debug): print(q)
    cursor.execute(q)

def create_tables(cursor, con):
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

if __name__ == '__main__':
    opts = None
    opts = read_options()

    # Persistance Layer
    con = open_database(opts.dbuser, opts.dbpassword, opts.dbname)
    cursor = con.cursor()
    create_tables(cursor, con)
    # Incremental support
    # last_date = get_last_date(opts.channel, cursor)

    count_revs = count_pages = 0

    # http://openstack.redhat.com/api.php?action=query&list=allpages&aplimit=500
    api_url = opts.url + "/" + "api.php"
    if (opts.debug): print("API URL: " + api_url)

    # Read all WikiMedia pages and the analyze all revisions
    allpages_query = "action=query&list=allpages&aplimit=500&format=xml"
    pages = urllib2.urlopen(api_url+"?"+allpages_query)
    pages_list = pages.read().strip('\n')
    xmlpages = parseString(pages_list)
    for page in xmlpages.getElementsByTagName('p'):
        count_pages += 1
        # TODO: we can join several title pages here
        title = page.attributes['title'].value
        urltitle = urllib.urlencode({'titles':title})
        page_allrevs_query = "action=query&prop=revisions&"+urltitle+"&rvlimit=500&format=xml"
        pageid = page.attributes['pageid'].value
        insert_page (cursor, pageid, title)
        if (opts.debug): print(api_url+"?"+page_allrevs_query)
        page_revs = urllib2.urlopen(api_url+"?"+page_allrevs_query)
        page_revs_list = page_revs.read().strip('\n')
        xmlrevs = parseString(page_revs_list)
        for rev in xmlrevs.getElementsByTagName('rev'):
            count_revs += 1
            revid = rev.attributes['revid'].value
            user = rev.attributes['user'].value
            timestamp = rev.attributes['timestamp'].value
            comment = rev.attributes['comment'].value
            if (opts.debug): print (pageid +" " + revid+" "+user+" "+timestamp+" "+comment)
            insert_revision (cursor, pageid, revid, user, timestamp, comment)
            if (count_revs % 1000 == 0): print (count_revs)
        con.commit()
    close_database(con)
    print("Total revisions: %s" % (count_revs))
    print("Total pagess: %s" % (count_pages))
    sys.exit(0)