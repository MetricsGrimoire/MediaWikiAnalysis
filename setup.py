#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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

from distutils.core import setup

setup(name = "MediaWiki Analysis",
      version = "0.1",
      author =  "Bitergia",
      author_email = "acs@bitergia.com",
      description = "Analysis tool for MediaWiki websites",
      url = "https://github.com/MetricsGrimoire/MediaWikiAnalysis",
      packages = ["wikianalysis", "wikianalysis.db"],
      data_files = [],
      scripts = ["mediawiki_analysis.py", "confluence_analysis.py"],
      install_requires=["MySQL-python"])
