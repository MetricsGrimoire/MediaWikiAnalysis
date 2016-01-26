MediaWikiAnalysis
=================

MediaWiki Analysis Tool to gather information about pages, changes and people in MediaWiki based websites.

Usage
=====

 1. Create an empty database to be used by us:

    $ echo "CREATE DATABASE mwdb CHARACTER SET utf8 COLLATE utf8_unicode_ci" | mysql -u root

 1. Install required dependencies

    $ pip install -e .

 1. Run analysis on a website:

    $ python mediawiki_analysis.py --database mwdb --db-user root --url <mediawiki_url>
