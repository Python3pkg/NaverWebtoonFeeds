from flask import Response, render_template, request, redirect
from sqlalchemy.orm import joinedload
import pytz

from naverwebtoonfeeds import app, cache, tz
from naverwebtoonfeeds.models import Series
from naverwebtoonfeeds.lib.updater import update_series_list, update_series


def redirect_to_canonical_url(view):
    def new_view(*args, **kwargs):
        path = request.environ['RAW_URI']
        canonical_url = app.config['URL_ROOT'] + path
        if app.config.get('FORCE_REDIRECT') and request.url != canonical_url:
            return redirect(canonical_url, 301)
        else:
            return view(*args, **kwargs)
    new_view.__name__ = view.__name__
    new_view.__doc__ = view.__doc__
    return new_view


@app.route('/')
@redirect_to_canonical_url
@cache.cached(timeout=86400)
def feed_index():
    try:
        update_series_list(append_only=True)
    except:
        app.logger.error('An error occurred while updating series list', exc_info=True)
    series_list = Series.query.filter_by(is_completed=False).order_by(Series.title).all()
    return render_template('feed_index.html', series_list=series_list)


@app.route('/feeds/<int:series_id>.xml')
@redirect_to_canonical_url
@cache.cached(timeout=3600)
def feed_show(series_id):
    series = Series.query.options(joinedload('chapters')).get_or_404(series_id)
    try:
        update_series(series)
    except:
        app.logger.error('An error occurred while updating series info', exc_info=True)
    chapters = []
    for c in series.chapters:
        # _pubdate_tz is used in templates to correct time zone
        c._pubdate_tz = pytz.utc.localize(c.pubdate).astimezone(tz)
        chapters.append(c)
    xml = render_template('feed_show.xml', series=series, chapters=chapters)
    return Response(response=xml, content_type='application/atom+xml')


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
