# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
#
# The Original Code is Reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of the
# Original Code is CondeNet, Inc.
#
# All portions of the code written by CondeNet are Copyright (c) 2006-2010
# CondeNet, Inc. All Rights Reserved.
################################################################################
from r2.models import *
from r2.lib.utils import fetch_things2
from pylons import g
from r2.lib.db import queries
from r2.models import admintools
from pylons.i18n import ungettext, _
from r2.lib.db.queries import changed
from r2.lib.utils.trial_utils import indict, end_trial, trial_info

import string

def subreddit_or_create(name, author):
    try:
        sr = Subreddit._new(name = name, title = "Arxiv category %s"%name.replace('_','-'),
                            ip = '0.0.0.0', author_id = author._id, allow_top=True)
        sr.lang = "en"
        sr._commit()
    except SubredditExists:
        sr = Subreddit._by_name(name)
    return sr

def insert(title, sr_name, url, description, date, author='ArxivBot', cross_srs=[]):
    a = Account._by_name(author)
    sr = subreddit_or_create(sr_name, a)

    try:
        l = Link._by_url(url, sr)
        print "!! Link already exists"
        return l
    except NotFound:
        print "Submitting link"

    user = a
    l = Link(_ups = 1,
            title = title,
            url = url,
            _spam = False,
            author_id = user._id,
            sr_id = sr._id,
            lang = sr.lang,
            ip = '127.0.0.1',
            selftext = description)
    l.verdict = 'admin-approved'
    l.approval_checkmark = _("auto-approved")
    l._date = datetime(date.year,date.month,date.day,tzinfo=g.tz)
    l.selftext = description
    l._commit()
    for cross_sr in cross_srs:
      LinkSR(l, subreddit_or_create(cross_sr, a))._commit()
    l.set_url_cache()
    queries.queue_vote(user, l, True, '127.0.0.1')
    queries.new_savehide(l._save(user))

    queries.new_link(l)
    changed(l)

    queries.worker.join()
    
    end_trial(l, "admin-approved")
    admintools.unspam(l, user.name)
    ModAction.create(sr, user, 'approvelink', target=l)

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader, MetadataReader
from datetime import datetime, timedelta, date
import string

URL = 'http://export.arxiv.org/oai2'

arXiv_reader = MetadataReader(
    fields={
    'title':       ('textList', 'arXiv:arXiv/arXiv:title/text()'),
    'categories':       ('textList', 'arXiv:arXiv/arXiv:categories/text()'),
    'abstract':       ('textList', 'arXiv:arXiv/arXiv:abstract/text()'),
    'id':       ('textList', 'arXiv:arXiv/arXiv:id/text()'),
    'created':       ('textList', 'arXiv:arXiv/arXiv:created/text()'),
    'keynames':      ('textList', 'arXiv:arXiv/arXiv:authors/arXiv:author/arXiv:keyname/text()'),
    #'title':       ('textList', 'oai_dc:dc/dc:title/text()'),
    #'creator':     ('textList', 'oai_dc:dc/dc:creator/text()'),
    #'subject':     ('textList', 'oai_dc:dc/dc:subject/text()'),
    #'description': ('textList', 'oai_dc:dc/dc:description/text()'),
    #'publisher':   ('textList', 'oai_dc:dc/dc:publisher/text()'),
    #'contributor': ('textList', 'oai_dc:dc/dc:contributor/text()'),
    #'date':        ('textList', 'oai_dc:dc/dc:date/text()'),
    #'type':        ('textList', 'oai_dc:dc/dc:type/text()'),
    #'format':      ('textList', 'oai_dc:dc/dc:format/text()'),
    #'identifier':  ('textList', 'oai_dc:dc/dc:identifier/text()'),
    #'source':      ('textList', 'oai_dc:dc/dc:source/text()'),
    #'language':    ('textList', 'oai_dc:dc/dc:language/text()'),
    #'relation':    ('textList', 'oai_dc:dc/dc:relation/text()'),
    #'coverage':    ('textList', 'oai_dc:dc/dc:coverage/text()'),
    #'rights':      ('textList', 'oai_dc:dc/dc:rights/text()')
    },
    namespaces={
    'arXiv': 'http://arxiv.org/OAI/arXiv/',
    'dc' : 'http://purl.org/dc/elements/1.1/'
    }
    )

def run():
    time2 = datetime.now(tz=None)
    time = time2 - timedelta(days=2)
    insertAll(time, None)

def insertAll(time, time2):
    registry = MetadataRegistry()
    registry.registerReader('arXiv', arXiv_reader)
    client = Client(URL, registry)
    client.updateGranularity()
    list = client.listRecords(metadataPrefix='arXiv', from_=time, until=time2)
    for a in list:
        a = list.next()
        title = '\n'.join(a[1]['title'])
        sr2 = ' '.join(a[1]['categories']).replace('-','_').split(' ')
        abstract = '\n'.join(a[1]['abstract'])
        url = 'http://arxiv.org/abs/' + a[1]['id'][0]
        date = datetime.strptime(a[1]['created'][0],'%Y-%m-%d')
        authors = '; '.join(a[1]['keynames'])
        print title
        print sr2
        print abstract
        print url
        print date
        print authors
        for sr in sr2:
            insert(title + ' (' + authors + ')', str(sr), url, abstract, date=date)

