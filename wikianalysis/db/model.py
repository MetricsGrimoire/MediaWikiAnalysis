# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
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
#     Santiago Dueñas <sduenas@bitergia.com>
#

from sqlalchemy import Table, Column, Float, DateTime, Integer,\
    String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class UniqueObject(object):

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        return _unique(
                    session,
                    cls,
                    cls.unique_filter,
                    cls,
                    arg, kw
               )

def _unique(session, cls, queryfunc, constructor, arg, kw):
    with session.no_autoflush:
        q = session.query(cls)
        q = queryfunc(q, *arg, **kw)

        obj = q.first()

        if not obj:
            obj = constructor(*arg, **kw)

        session.add(obj)
    return obj


class WikiPage(UniqueObject, Base):
    __tablename__ = 'wiki_pages'

    page_id = Column(Integer, primary_key=True)
    wikipage_id = Column(String(64))
    type = Column(String(64))
    title = Column(String(256))
    namespace = Column(String(64))

    created_by = Column(String(64),
                        ForeignKey('people.username', ondelete='CASCADE'),)
    created_on = Column(DateTime(timezone=False))
    updated_at  = Column(DateTime(timezone=False))

    author = relationship('Member', foreign_keys=[created_by])

    revisions = relationship('WikiPageRevision',
                             cascade="save-update, merge, delete")

    __table_args__ = {'mysql_charset': 'utf8'}

    @classmethod
    def unique_filter(cls, query, wikipage_id):
        return query.filter(WikiPage.wikipage_id == wikipage_id)


class WikiPageRevision(UniqueObject, Base):
    __tablename__ = 'wiki_pages_revs'

    id = Column(Integer, primary_key=True)
    wikipage_id = Column(String(64))
    rev_id = Column(Integer)
    comment = Column(Text())
    date = Column(DateTime(timezone=False))

    user = Column(String(64),
                  ForeignKey('people.username', ondelete='CASCADE'),)
    page_id = Column(Integer,
                     ForeignKey('wiki_pages.page_id', ondelete='CASCADE'),)

    author = relationship('Member', foreign_keys=[user])
    wikipage = relationship('WikiPage', foreign_keys=[page_id])

    __table_args__ = {'mysql_charset': 'utf8'}

    @classmethod
    def unique_filter(cls, query, wikipage_id, rev_id):
        return query.filter(WikiPageRevision.wikipage_id == wikipage_id,
                            WikiPageRevision.rev_id == rev_id)


class Member(UniqueObject, Base):
    __tablename__ = 'people'

    username = Column(String(64), primary_key=True)
    name = Column(String(256))

    __table_args__ = {'mysql_charset': 'utf8'}

    @classmethod
    def unique_filter(cls, query, username):
        return query.filter(Member.username == username)
