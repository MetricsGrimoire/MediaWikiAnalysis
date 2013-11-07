#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Bitergia
#
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
#
# Authors:
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#
import MySQLdb, os, random, string, sys, unittest
import mediawiki_analysis

class Config:
    pass

class MediaWikiTest(unittest.TestCase):

    def testZAll(self):
        channel_id = "1"
        total_messages = 5552
        cursor = MediaWikiTest.db.cursor()
        files = os.listdir(MediaWikiTest.tests_data_dir)
        for logfile in files:
            year = logfile[0:4]
            month = logfile[4:6]
            day = logfile[6:8]    
            date = year + "-" + month + "-" + day
            date_nick_msg = mediawiki_analysis.parse_file(os.path.join(MediaWikiTest.tests_data_dir, logfile))
    
            for i in date_nick_msg:
                mediawiki_analysis.insert_message (cursor, date + " " + i[0], i[1], i[2], channel_id)                
            MediaWikiTest.db.commit()
        sql = "SELECT COUNT(*) FROM mediawikilog"
        cursor.execute(sql)
        self.assertEqual(cursor.fetchall()[0][0], total_messages)
        
    def testReadFile(self):
        filename = "20130715.txt"
        date_nick_msg = mediawiki_analysis.parse_file(os.path.join(MediaWikiTest.tests_data_dir, filename))
        self.assertEqual(len(date_nick_msg), 224)
        
    def testWriteDb(self):
        channel_id = "1"
        filename = "20130715.txt"
        date = "2013-07-15"
        date_nick_msg = mediawiki_analysis.parse_file(os.path.join(MediaWikiTest.tests_data_dir, filename))
        cursor = MediaWikiTest.db.cursor()

        for i in date_nick_msg:
            mediawiki_analysis.insert_message (cursor, date + " " + i[0], i[1], i[2], channel_id) 
        MediaWikiTest.db.commit()
        
        sql = "SELECT COUNT(*) FROM mediawikilog"
        cursor.execute(sql)
        self.assertEqual(cursor.fetchall()[0][0], 224)
        
    def setUp(self):
        cursor = MediaWikiTest.db.cursor()
        cursor.execute("DELETE from mediawikilog")

    @staticmethod
    def setUpDB():
        Config.db_driver_out = "mysql"
        Config.db_user_out = "root"
        Config.db_password_out = ""
        Config.db_hostname_out = ""
        Config.db_port_out = ""
        random_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(5))
        Config.db_database_out = "mediawikilogdb"+random_str
        
        MediaWikiTest.db = MySQLdb.connect(user=Config.db_user_out, passwd=Config.db_password_out)
        c = MediaWikiTest.db.cursor()
        sql = "CREATE DATABASE "+ Config.db_database_out +" CHARACTER SET utf8 COLLATE utf8_unicode_ci"
        c.execute(sql)
        MediaWikiTest.db.close()
        MediaWikiTest.db = MySQLdb.connect(user=Config.db_user_out, passwd=Config.db_password_out, db=Config.db_database_out)

    @staticmethod                
    def setUpBackend():
        MediaWikiTest.tests_data_dir = os.path.join('test','data')        
        
        if not os.path.isdir (MediaWikiTest.tests_data_dir):
            print('Can not find test data in ' + MediaWikiTest.tests_data_dir)
            sys.exit(1)
            
        MediaWikiTest.setUpDB()
        
        cursor = MediaWikiTest.db.cursor()
        mediawiki_analysis.create_tables(cursor, MediaWikiTest.db)

    @staticmethod
    def closeBackend():
        c = MediaWikiTest.db.cursor()
        sql = "DROP DATABASE " + Config.db_database_out
        c.execute(sql)
        MediaWikiTest.db.close()
        
if __name__ == '__main__':
    MediaWikiTest.setUpBackend()
    suite = unittest.TestLoader().loadTestsFromTestCase(MediaWikiTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
    # unittest.main()
    MediaWikiTest.closeBackend()
