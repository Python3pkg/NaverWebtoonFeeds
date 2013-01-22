# -*- coding: UTF-8 -*-
import unittest

from naverwebtoonfeeds import db
import naverwebtoonfeeds.views as v


# pylint: disable=C0103,R0904
class ViewsTest(unittest.TestCase):

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

    @unittest.skip("pending")
    def test_feed_index(self):
        pass

    @unittest.skip("pending")
    def test_feed_show(self):
        pass
