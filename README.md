MediaWikiAnalysis
=================

MediaWiki Analysis Tool to gather information about pages, changes and people in MediaWiki based websites.

Usage example:

    acs@lenovix:~$ echo "CREATE DATABASE mwdb CHARACTER SET utf8 COLLATE utf8_unicode_ci" | mysql -u root
    acs@lenovix:~/devel/MediawikiAnalysis$ ./mediawiki_analysis.py --database mwdb --db-user root --url mediawiki_url
