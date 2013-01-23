import unittest

from naverwebtoonfeeds.test.utilities import mock_obj, Mock
import naverwebtoonfeeds.misc as m


# pylint: disable=C0103,R0904
class MiscTest(unittest.TestCase):

    def setUp(self):
        self.originals = {}
        for name in dir(m):
            self.originals[name] = getattr(m, name)

    def tearDown(self):
        for name in self.originals:
            setattr(m, name, self.originals[name])

    def test_urlpath_minimum(self):
        self.assertEqual(m.urlpath('http://a.co'), '')

    def test_urlpath_root(self):
        self.assertEqual(m.urlpath('http://foo.bar.com/'), '/')

    def test_urlpath_path(self):
        self.assertEqual(m.urlpath('http://bit.ly/bEf232'), '/bEf232')

    def test_urlpath_full(self):
        self.assertEqual(m.urlpath('http://a.co/p;p1;p2;p3?a=1&b=2#frag'),
                '/p;p1;p2;p3?a=1&b=2#frag')

    def test_heroku_scale(self):
        m.app = mock_obj(config=dict(HEROKU_API_KEY='foobar123', HEROKU_APP_NAME='testapp'))
        m.heroku = Mock()
        m.heroku_scale('beaver', 5)
        m.heroku.from_key.assert_called_with('foobar123')
        m.heroku.from_key('foobar123')._http_resource.assert_called_with(
                method='POST',
                resource=('apps', 'testapp', 'ps', 'scale'),
                data=dict(type='beaver', qty=5)
        )

    def test_redirect_to_canonical_url_without_raw_uri_without_force_redirect(self):
        m.app = mock_obj(config=dict(URL_ROOT='http://bit.ly', FORCE_REDIRECT=False))
        m.request = mock_obj(environ=dict(), url='http://foo.com/baa/aar')
        view = mock_obj(__name__='view', __doc__=None)
        decorated_view = m.redirect_to_canonical_url(view)
        decorated_view(1, 'x', y=3)
        view.assert_called_with(1, 'x', y=3)

    def test_redirect_to_canonical_url_without_raw_uri_with_force_redirect(self):
        m.app = mock_obj(config=dict(URL_ROOT='http://bit.ly', FORCE_REDIRECT=True))
        m.request = mock_obj(environ=dict(), url='http://foo.com/baa/aar')
        m.redirect = Mock()
        view = mock_obj(__name__='view', __doc__=None)
        decorated_view = m.redirect_to_canonical_url(view)
        decorated_view(1, 'x', y=3)
        m.redirect.assert_called_with('http://bit.ly/baa/aar', 301)

    def test_redirect_to_canonical_url_with_raw_uri_with_force_redirect(self):
        m.app = mock_obj(config=dict(URL_ROOT='http://bit.ly', FORCE_REDIRECT=True))
        m.request = mock_obj(environ=dict(RAW_URI='/baa/aar'), url='http://foo.com/baa/aar')
        m.redirect = Mock()
        view = mock_obj(__name__='view', __doc__=None)
        decorated_view = m.redirect_to_canonical_url(view)
        decorated_view(1, 'x', y=3)
        m.redirect.assert_called_with('http://bit.ly/baa/aar', 301)
