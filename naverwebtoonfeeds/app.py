import logging
import logging.config
import os

from flask import Flask, render_template

from .config import DefaultConfig
from .extensions import (db, cache, assets_env, gzip, redis_connection)
from .feeds import feeds
from .redismod import RedisCache, CompressedRedisCache
from .template import externalize, proxify


__logger__ = logging.getLogger(__name__)


DEFAULT_BLUEPRINTS = [feeds]


def create_app(config=None, blueprints=None):
    """
    Creates a Flask app.

    If *blueprints* is None, the default blueprints will be used.
    Currently there is only one blueprint, defined in
    :mod:`naverwebtoonfeeds.feeds`.

    """
    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS
    app = Flask(__name__)
    configure_app(app, config)
    configure_logging(app)
    configure_blueprints(app, blueprints)
    configure_extensions(app)
    configure_template_filters(app)
    configure_error_handlers(app)
    return app


def configure_app(app, config=None):
    """Configures the app.

    Configuration is applied in the following order:

    1. :class:`naverwebtoonfeeds.config.DefaultConfig`
    2. `naverwebtoonfeeds.config.NWF_ENV.Config` where
       *NWF_ENV* is the value of the environment variable,
       either ``production``, ``development`` (default), or ``test``.
    3. If *NWF_SETTINGS* environment variable is set,
       the file it is pointing to.
    4. The *config* object given as an argument, if it is not *None*.

    """
    app.config.from_object(DefaultConfig)
    env = os.environ.get('NWF_ENV', 'development')
    __logger__.info('Environment: %s', env)
    app.config.from_object('naverwebtoonfeeds.config.{0}.Config'.format(env))
    if os.environ.get('NWF_SETTINGS'):
        app.config.from_envvar('NWF_SETTINGS', silent=False)
    if config is not None:
        app.config.from_object(config)


def configure_logging(app):
    """Configures logging."""
    # Make it sure that the logger is created before configuration.
    # pylint: disable=pointless-statement
    app.logger
    # Now configure
    logging.config.dictConfig(app.config['LOGGING'])
    __logger__.info('Logging configured')


def configure_blueprints(app, blueprints):
    """Registers blueprints to the app."""
    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def configure_extensions(app):
    """Initializes extensions for the app."""
    db.init_app(app)

    cache.init_app(app)
    cache.app = app   # Perhaps Flask-Cache bug
    if app.config.get('CACHE_TYPE') == 'redis':
        if app.config.get('ENABLE_CACHE_COMPRESSION'):
            cache.cache.__class__ = CompressedRedisCache
        else:
            cache.cache.__class__ = RedisCache

    assets_env.init_app(app)

    if app.config.get('GZIP'):
        gzip.init_app(app)

    if app.config.get('USE_REDIS_QUEUE'):
        redis_connection.init(host=app.config['CACHE_REDIS_HOST'],
                port=app.config['CACHE_REDIS_PORT'],
                password=app.config['CACHE_REDIS_PASSWORD'])


def configure_template_filters(app):
    """Configures template filters and context processors."""

    app.add_template_filter(externalize)
    app.add_template_filter(proxify)


def configure_error_handlers(app):
    """Configures error handlers."""
    # pylint: disable=unused-variable

    @app.errorhandler(500)
    def internal_server_error(_):
        return render_template('500.html'), 500

    @app.errorhandler(404)
    def not_found(_):
        return render_template('404.html'), 404
