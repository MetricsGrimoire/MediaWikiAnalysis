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
# To run: PYTHONPATH=. test/test_mediawiki.py 
#

import MySQLdb, os, random, string, sys, unittest
import mediawiki_analysis
from xml.dom.minidom import parseString


class Config:
    pass

class MediaWikiTest(unittest.TestCase):
    
    def testZAll(self):
        # look test/data/README
        total_pages = 17
        total_reviews = 23
        total_changes = 47
        cursor = MediaWikiTest.db.cursor()
        pages = open(os.path.join(MediaWikiTest.tests_data_dir, "pages.xml"))
        reviews = open(os.path.join(MediaWikiTest.tests_data_dir, "revisions.xml"))
        changes = open (os.path.join(MediaWikiTest.tests_data_dir, "changes.xml"))
        mediawiki_analysis.process_pages(cursor, parseString(pages.read()), None, False)
        # print (reviews.read())
        # print (changes.read())
        MediaWikiTest.db.commit()
        sql = "SELECT COUNT(*) FROM wiki_pages"
        cursor.execute(sql)
        self.assertEqual(cursor.fetchall()[0][0], total_pages)
        sys.exit(0)
        sql = "SELECT COUNT(*) FROM wiki_pages_revs"
        cursor.execute(sql)
        self.assertEqual(cursor.fetchall()[0][0], total_reviews)

    def setUp(self):
        pass

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
        cursor = MediaWikiTest.db.cursor()
        mediawiki_analysis.create_tables(cursor)


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
