# -*- coding: UTF-8 -*-
from datetime import datetime
import unittest

from flask import url_for
import lxml.html

from naverwebtoonfeeds import db
from naverwebtoonfeeds.models import Series, Chapter
from naverwebtoonfeeds.test.utilities import Mock
from naverwebtoonfeeds.helpers import externalize
import naverwebtoonfeeds.view_helpers as v


# pylint: disable=C0103,R0904
class RenderingTest(unittest.TestCase):

    def setUp(self):
        self.originals = {}
        for name in dir(v):
            self.originals[name] = getattr(v, name)
        self.test_request_context = v.app.test_request_context()
        self.test_request_context.__enter__()
        db.create_all()

    def tearDown(self):
        for name in self.originals:
            setattr(v, name, self.originals[name])
        db.drop_all()
        self.test_request_context.__exit__(None, None, None)

    def test_render_and_cache_feed_index_without_series(self):
        v.cache = Mock()
        response = v.render_and_cache_feed_index()
        doc = lxml.html.fromstring(response)
        v.cache.set.assert_called_with('feed_index', response, v.CACHE_PERMANENT)
        self.assertIn(u'구독할 수 있는 웹툰이 없습니다.', response)
        self.assertEqual([], doc.xpath('//article'))

    def test_render_and_cache_feed_index_with_series(self):
        v.cache = Mock()
        db.session.add(Series(id=1, title='Peanuts', author='Charles M. Schulz'))
        db.session.add(Series(id=2, title="Alice's Adventures in Wonderland", author='Lewis Carroll',
                description='A girl named Alice falls down a rabbit hole into a fantasy world.'))
        db.session.commit()
        response = v.render_and_cache_feed_index()
        doc = lxml.html.fromstring(response)

        v.cache.set.assert_called_with('feed_index', response, v.CACHE_PERMANENT)
        self.assertIn('Peanuts', response)
        self.assertIn('Charles M. Schulz', response)
        self.assertIn("Alice&#39;s Adventures in Wonderland", response)
        self.assertIn('Lewis Carroll', response)
        self.assertIn('A girl named Alice falls down a rabbit hole into a fantasy world.', response)
        self.assertNotIn(u'구독할 수 있는 웹툰이 없습니다.', response)
        self.assertEqual(doc.xpath('count(//article)'), 2)
        self.assertEqual(['series-2', 'series-1'], doc.xpath('//article/attribute::id'),
                "Series should be sorted by title.")
        self.assertIn(externalize(url_for('feed_show', series_id=1)),
                doc.xpath('//article//a/attribute::href'))

    def test_render_and_cache_feed_show_with_chapters(self):
        v.cache = Mock()
        db.session.add(Series(id=1, title='Peanuts', author='Charles M. Schulz'))
        db.session.add(Chapter(id=1, title='Strip #1', pubdate=datetime(1950, 10, 2), atom_id='', series_id=1))
        db.session.add(Chapter(id=2, title='Strip #2', pubdate=datetime(1950, 10, 3), atom_id='', series_id=1))
        db.session.commit()
        response = v.render_and_cache_feed_show(Series.query.get(1))
        doc = lxml.html.fromstring(response.data)

        self.assertIn('Peanuts', response.data)
        # TODO continue to write code tomorrow
