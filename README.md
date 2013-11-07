MediaWikiAnalysis
=================

MediaWiki Analysis Tool to gather information about pages, changes and people in MediaWiki based websites.

Usage example:

    acs@lenovix:~/devel/IRCAnalysis$ mysqladmin -u root create mediawikidb
    acs@lenovix:~/devel/IRCAnalysis$ ./mediawiki_analysis.py -d mediawikidb --url mediawiki_url
