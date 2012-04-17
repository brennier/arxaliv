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
    srs = [subreddit_or_create(sr_name, a) for sr_name in cross_srs]
    ups = 1
    downs = 0
    try:
        ls = Link._by_url(url, None)
        print 'Found %d links' % len(ls)
        for l in ls:
            if l.author_id == a._id and l.sr_id != sr._id:
                ups = ups + l._ups - 1
                downs = downs + l._downs
		l._deleted=True
		l._commit()
                changed(l)
                x = l.subreddit_slow
                queries.delete_links(l)
                print 'Deleting ' + str(l)
            else:
                print 'Not deleting ' + str(l)
        print 'Seed votes %s %s' % (ups, downs)
    except NotFound:
        pass


    try:
        l = Link._by_url(url, sr)
        print "!! Link already exists"
        return l
    except NotFound:
        print "Submitting link"



    user = a
    l = Link(_ups = ups,
            _downs = downs,
            title = title,
            url = url,
            _spam = False,
            author_id = user._id,
            sr_id = sr._id,
            lang = sr.lang,
            ip = '127.0.0.1',
            multi_sr_id = [sr._id]+[sr._id for sr in srs],
            selftext = description)
    l.verdict = 'admin-approved'
    l.approval_checkmark = _("auto-approved")
    l._date = datetime(date.year,date.month,date.day,tzinfo=g.tz)
    l.selftext = description
    l._commit()
    #for cross_sr in cross_srs:
    #  LinkSR(l, subreddit_or_create(cross_sr, a), 'crosspost')._commit()
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

arXivRaw_reader = MetadataReader(
    fields={
    'title':       ('textList', 'arXivRaw:arXivRaw/arXivRaw:title/text()'),
    'categories':       ('textList', 'arXivRaw:arXivRaw/arXivRaw:categories/text()'),
    'abstract':       ('textList', 'arXivRaw:arXivRaw/arXivRaw:abstract/text()'),
    'id':       ('textList', 'arXivRaw:arXivRaw/arXivRaw:id/text()'),
    'authors':  ('textList', 'arXivRaw:arXivRaw/arXivRaw:authors/text()'),
    'created':  ('textList', 'arXivRaw:arXivRaw/arXivRaw:version/arXivRaw:date/text()'),
    #'created':       ('textList', 'arXivRaw:arXivRaw/arXivRaw:created/text()'),
    #'keynames':      ('textList', 'arXivRaw:arXivRaw/arXivRaw:authors/arXivRaw:author/arXivRaw:keyname/text()'),
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
    'arXivRaw': 'http://arxiv.org/OAI/arXivRaw/',
    'dc' : 'http://purl.org/dc/elements/1.1/'
    }
    )

def run():
    time2 = datetime.now(tz=None)
    time = time2 - timedelta(days=7)
    insertAll(time, None)

def insertAll(time, time2):
    registry = MetadataRegistry()
    registry.registerReader('arXivRaw', arXivRaw_reader)
    client = Client(URL, registry)
    client.updateGranularity()
    list = client.listRecords(metadataPrefix='arXivRaw', from_=time, until=time2)
    errors = 0
    for a in list:
        #a = list.next()
        try:
            title = '\n'.join(a[1]['title'])
            sr2 = str(' '.join(a[1]['categories']).replace('-','_')).split(' ')
            abstract = '\n'.join(a[1]['abstract'])
            url = 'http://arxiv.org/abs/' + a[1]['id'][0]
            date = datetime.strptime(a[1]['created'][0], '%a, %d %b %Y %H:%M:%S %Z')
            authors = a[1]['authors'][0]# '; '.join(a[1]['keynames'])
            abstract = abstract + '\nBy: ' + authors + '\nIn: ' + ', '.join(sr2)
            print title
            print sr2
            print abstract
            print url
            print date
            print authors
            insert(title + ' (' + authors + ')', str("fullarxiv"), url, abstract, date=date, cross_srs=sr2)
        except:
            print 'ERROR'
            print a
            errors = errors+1
    print 'Completed with %s errors' % errors
