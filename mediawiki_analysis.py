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
import urllib2
from xml.dom.minidom import parse, parseString




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

    # Read all WikiMedia pages and the analyze all revisions
    allpages_query = "action=query&list=allpages&aplimit=500&format=xml"
    pages = urllib2.urlopen(api_url+"?"+allpages_query)
    if (opts.debug):
        pages_list_orig = '\n<?xml version="1.0"?><api><query><allpages><p pageid="189" ns="0" title="A Case Study: Starting From Scratch With Havana" /><p pageid="40" ns="0" title="About RDO" /><p pageid="73" ns="0" title="Accessing Nagios" /><p pageid="31" ns="0" title="Adding a compute node" /><p pageid="66" ns="0" title="Adding new content" /><p pageid="107" ns="0" title="Books" /><p pageid="47" ns="0" title="Case studies" /><p pageid="175" ns="0" title="CeilometerQuickStart" /><p pageid="162" ns="0" title="Clients" /><p pageid="81" ns="0" title="Common service operations" /><p pageid="42" ns="0" title="Community guidelines" /><p pageid="170" ns="0" title="Configuring Neutron with OVS and GRE Tunnels using quickstack" /><p pageid="172" ns="0" title="Continuous Integration" /><p pageid="150" ns="0" title="DeployHeatOnHavana" /><p pageid="77" ns="0" title="Deploy Haeat and launch your first Application" /><p pageid="78" ns="0" title="Deploy Heat and launch your first Application" /><p pageid="151" ns="0" title="Deploy an application with Heat" /><p pageid="138" ns="0" title="Deploying RDO Using Foreman" /><p pageid="198" ns="0" title="Deploying RDO Using Tuskar And TripleO" /><p pageid="165" ns="0" title="Difference between Floating IP and private IP" /><p pageid="7" ns="0" title="Docs" /><p pageid="95" ns="0" title="Dumb Tricks with Neutron" /><p pageid="129" ns="0" title="Events" /><p pageid="102" ns="0" title="External Connectivity" /><p pageid="33" ns="0" title="FAQ" /><p pageid="118" ns="0" title="Fedora 19" /><p pageid="32" ns="0" title="Floating IP range" /><p pageid="128" ns="0" title="Floating IPs on the Lab Network" /><p pageid="63" ns="0" title="Floating ip range" /><p pageid="195" ns="0" title="Foreman HA Database" /><p pageid="34" ns="0" title="Frequently Asked Questions" /><p pageid="2" ns="0" title="Frequently asked questions" /><p pageid="29" ns="0" title="Get Involved" /><p pageid="50" ns="0" title="Get involved" /><p pageid="171" ns="0" title="GettingStartedHavana w GRE" /><p pageid="84" ns="0" title="Getting Started" /><p pageid="132" ns="0" title="HA OpenStack API" /><p pageid="135" ns="0" title="Heat" /><p pageid="133" ns="0" title="Highly Available MySQL server" /><p pageid="127" ns="0" title="Highly Available MySQL server for OpenStack" /><p pageid="134" ns="0" title="Highly Available MySQL server on OpenStack" /><p pageid="182" ns="0" title="Highly Available Qpid for OpenStack" /><p pageid="178" ns="0" title="HorizonSSL" /><p pageid="183" ns="0" title="HowToTest" /><p pageid="188" ns="0" title="HowToTest/Ceilometer/H/AlarmAggregation" /><p pageid="187" ns="0" title="HowToTest/Ceilometer/H/AlarmHistoryAPI" /><p pageid="185" ns="0" title="HowToTest/Ceilometer/H/AlarmPartitioning" /><p pageid="184" ns="0" title="HowToTest/Ceilometer/H/AlarmThresholdEvaluation" /><p pageid="186" ns="0" title="HowToTest/Ceilometer/H/UnitsRateOfChangeConversion" /><p pageid="88" ns="0" title="Image resources" /><p pageid="76" ns="0" title="Installation errors" /><p pageid="86" ns="0" title="KeystoneIDMIntegration" /><p pageid="85" ns="0" title="Keystone integration with IDM" /><p pageid="191" ns="0" title="Lars-Test" /><p pageid="169" ns="0" title="LaunchHeatApplication" /><p pageid="44" ns="0" title="Legal" /><p pageid="48" ns="0" title="Licensing" /><p pageid="123" ns="0" title="Load Balance OpenStack API" /><p pageid="1" ns="0" title="Main Page" /><p pageid="96" ns="0" title="Network Configuration Overview" /><p pageid="103" ns="0" title="Network Interfaces" /><p pageid="90" ns="0" title="Networking" /><p pageid="100" ns="0" title="Networking Solutions" /><p pageid="192" ns="0" title="Networking in too much detail" /><p pageid="97" ns="0" title="Neutron-Quickstart" /><p pageid="108" ns="0" title="Neutron-ovs with vlans" /><p pageid="161" ns="0" title="NeutronLibvirtMultinodeDevEnvironment" /><p pageid="105" ns="0" title="Neutron with OVS and VLANs" /><p pageid="109" ns="0" title="Neutron with OVS and vlans" /><p pageid="164" ns="0" title="Neutron with existing external network" /><p pageid="67" ns="0" title="OSAS Test Lab" /><p pageid="65" ns="0" title="OSAS test lab" /><p pageid="126" ns="0" title="OpenStackForumHongKong" /><p pageid="125" ns="0" title="OpenStack Summit Hong Kong" /><p pageid="92" ns="0" title="PackStack All-in-One DIY Configuration" /><p pageid="94" ns="0" title="Packstack with Multiple Compute nodes" /><p pageid="6" ns="0" title="People" /><p pageid="177" ns="0" title="People/" /><p pageid="89" ns="0" title="Qpid errors" /><p pageid="179" ns="0" title="QuickStart" /><p pageid="136" ns="0" title="QuickStartLatest" /><p pageid="4" ns="0" title="Quickstart" /><p pageid="174" ns="0" title="RDO HighlyAvailable and LoadBalanced Control Services" /><p pageid="199" ns="0" title="RDO MySQL Multi-Master Replication Active-Active HA" /><p pageid="168" ns="0" title="RDO Test Day October 2013" /><p pageid="131" ns="0" title="RDO Test Day September 2013" /><p pageid="197" ns="0" title="RDO Video" /><p pageid="149" ns="0" title="RDO Videos" /><p pageid="87" ns="0" title="Repositories" /><p pageid="30" ns="0" title="Running an instance" /><p pageid="98" ns="0" title="Running an instance with Neutron" /><p pageid="72" ns="0" title="SELinux issues" /><p pageid="124" ns="0" title="Scratch" /><p pageid="139" ns="0" title="Securing Services" /><p pageid="176" ns="0" title="Securing Services Foreman" /><p pageid="101" ns="0" title="Tenant Networks" /><p pageid="45" ns="0" title="Terms of use" /><p pageid="140" ns="0" title="Test Day 09 2013" /><p pageid="137" ns="0" title="TestedSetups" /><p pageid="99" ns="0" title="Tools" /><p pageid="147" ns="0" title="TripleO images" /><p pageid="41" ns="0" title="Troubleshooting" /><p pageid="75" ns="0" title="Uninstalling RDO" /><p pageid="180" ns="0" title="Upgrading RDO" /><p pageid="106" ns="0" title="Using Ceph for Block Storage with RDO" /><p pageid="122" ns="0" title="Using GRE Tenant Networks" /><p pageid="83" ns="0" title="Using RDO on TryStack" /><p pageid="194" ns="0" title="Virtualized Foreman Dev Setup" /><p pageid="148" ns="0" title="Workarounds" /></allpages></query></api>'
        pages_list = pages_list_orig.strip('\n')
    else:
        pages_list = pages.read().strip('\n')
    import pprint
    pprint.pprint(pages_list)
    pprint.pprint(parseString(pages_list))
    sys.exit(0)

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