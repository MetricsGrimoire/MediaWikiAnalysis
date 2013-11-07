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
import os, sys
import MySQLdb
from datetime import datetime


def read_file(filename):
    fd = open(filename, "r")
    lines = fd.readlines()
    fd.close()
    return lines


def parse_file(filename):
    date_nick_message = []
    lines = read_file(filename)
    for l in lines:
        # [12:39:15] <wm-bot>  Infobot disabled
        aux = l.split(" ")
        time = aux[0]
        time = time[1:len(time) - 1]
        nick = (aux[1].split("\t"))[0]
        nick = nick[1:len(nick) - 1]
        msg = ' '.join(aux[2:len(aux)])
        date_nick_message.append([time, nick, msg])
    return date_nick_message


def open_database(myuser, mypassword, mydb):
    con = MySQLdb.Connect(host="127.0.0.1",
                          port=3306,
                          user=myuser,
                          passwd=mypassword,
                          db=mydb)
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
 
def get_last_date(channel, cursor):
    query =  "SELECT MAX(date) FROM irclog, channels "
    query += "WHERE irclog.channel_id=channels.id "
    query += " AND channels.name='"+channel+"'"
    cursor.execute(query)
    return cursor.fetchone()[0]

def insert_message(cursor, date, nick, message, channel_id):
    message = escape_string (message)
    nick = escape_string (nick)
    q = "insert into irclog (date,nick,message,channel_id) values (";
    q += "'" + date + "','" + nick + "','" + message + "','"+channel_id+"')"
    cursor.execute(q)
    
def create_tables(cursor, con):
#    query = "DROP TABLE IF EXISTS irclog"
#    cursor.execute(query)
#    query = "DROP TABLE IF EXISTS channels"
#    cursor.execute(query)

    query = "CREATE TABLE IF NOT EXISTS irclog (" + \
           "id int(11) NOT NULL AUTO_INCREMENT," + \
           "nick VARCHAR(255) NOT NULL," + \
           "date DATETIME NOT NULL," + \
           "message TEXT," + \
           "channel_id int," + \
           "PRIMARY KEY (id)" + \
           ") ENGINE=MyISAM DEFAULT CHARSET=utf8"
    cursor.execute(query)
    
    query = "CREATE TABLE IF NOT EXISTS channels (" + \
           "id int(11) NOT NULL AUTO_INCREMENT," + \
           "name VARCHAR(255) NOT NULL," + \
           "PRIMARY KEY (id)" + \
           ") ENGINE=MyISAM DEFAULT CHARSET=utf8"
    cursor.execute(query)
    
    try:
        query = "DROP INDEX ircnick ON irclog;"
        cursor.execute(query)
        query = "CREATE INDEX ircnick ON irclog (nick);"
        cursor.execute(query)
        con.commit()
    except MySQLdb.Error:
        print "Problems creating nick index"

    return

def get_url_id(name, cursor):
    cursor.execute("SELECT * from channels where name='"+name+"'")
    results =  cursor.fetchall()
    if len(results) == 0:
        query = "INSERT INTO channels (name) VALUES ('"+name+"')"
        cursor.execute(query)
        cursor.execute("SELECT * from channels where name='"+name+"'")
        results =  cursor.fetchall()
    url_id = str(results[0][0])
    return url_id

if __name__ == '__main__':
    opts = None
    opts = read_options()

    # Persistance Layer
    if False:
        con = open_database(opts.dbuser, opts.dbpassword, opts.dbname)
        cursor = con.cursor()
        create_tables(cursor, con)
        url_id = get_url_id(opts.url, cursor)
        last_date = get_last_date(opts.channel, cursor)

    count_msg = count_msg_new = count_msg_drop = count_files_drop = 0

    # http://openstack.redhat.com/api.php?action=query&list=allpages&aplimit=500
    api_url = opts.url + "/" + "api.php"
    print("API URL: " + api_url)
    sys.exit(0)
    
    # Read all WikiMedia pages and the analyze all revisions
    allpages_query = "http://openstack.redhat.com/api.php?action=query&list=allpages&aplimit=500"
    
    files = os.listdir(opts.data_dir)
    for logfile in files:
        year = logfile[0:4]
        month = logfile[4:6]
        day = logfile[6:8]    
        date = year + "-" + month + "-" + day
        try:
            date_test = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            count_files_drop += 1
            print "Bad filename format in  " + logfile
            continue

        date_nick_msg = parse_file(opts.data_dir + "/" + logfile)

        for i in date_nick_msg:
            count_msg += 1
            # date: 2013-07-11 15:39:16
            date_time = date + " " + i[0]
            try:
                msg_date = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                count_msg_drop += 1
                print "Bad format in " + date_time + " (" + logfile + ")"
                continue
            if (last_date and msg_date <= last_date): continue
            insert_message (cursor, date_time, i[1], i[2], url_id)
            count_msg_new += 1
            if (count_msg % 1000 == 0): print (count_msg)
        con.commit()

    close_database(con)
    print("Total messages: %s" % (count_msg))
    print("Total new messages: %s" % (count_msg_new))
    print("Total drop messages: %s" % (count_msg_drop))
    print("Total log files drop: %s" % (count_files_drop))
    sys.exit(0)