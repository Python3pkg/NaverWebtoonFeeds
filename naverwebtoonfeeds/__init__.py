import logging
import logging.config
import os

from flask import Flask
from flask.ext.cache import Cache
from flask.ext.assets import Environment, Bundle

from naverwebtoonfeeds.models import db

app = Flask(__name__)
app.config.from_object('naverwebtoonfeeds.default_settings')
if os.environ.get('NAVERWEBTOONFEEDS_SETTINGS'):
    app.config.from_envvar('NAVERWEBTOONFEEDS_SETTINGS')

app.logger   # Make sure the logger is created.
logging.config.dictConfig(app.config['LOGGING'])
try:
    from naverwebtoonfeeds.lib.naver import get_public_ip
    app.logger.warning('Current IP: %s', get_public_ip())
except:
    app.logger.warning('Failed to get the public IP')

db.init_app(app)

cache = Cache(app)

if app.config.get('GZIP'):
    from flask.ext.gzip import Gzip
    gzip = Gzip(app)

if app.config.get('USE_REDIS_QUEUE'):
    from redis import Redis
    from rq import Queue
    redis_connection = Redis(host=app.config['CACHE_REDIS_HOST'],
            port=app.config['CACHE_REDIS_PORT'],
            password=app.config['CACHE_REDIS_PASSWORD'])
    redis_queue = Queue(connection=redis_connection)

assets = Environment(app)
assets.register('js_all',
    'jquery.min.js',
    'bootstrap/js/bootstrap.min.js',
    'jquery.lazyload.min.js',
    Bundle('jquery.delayedlast.js.coffee',
        'application.js.coffee',
        filters='coffeescript,yui_js'),
    output='gen/packed.%(version)s.js'
)
assets.register('css_all',
    Bundle('bootstrap/css/bootstrap.min.css',
        'bootstrap/css/bootstrap-responsive.min.css',
        filters='cssrewrite'),
    Bundle('application.css.scss', filters='scss,yui_css'),
    output='gen/packed.%(version)s.css'
)

import naverwebtoonfeeds.views
import naverwebtoonfeeds.helpers
