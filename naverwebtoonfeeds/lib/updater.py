from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from naverwebtoonfeeds import app, cache, db, tz
from naverwebtoonfeeds.models import Series, Chapter
from naverwebtoonfeeds.lib.naver import NaverBrowser


# The longer this interval, the fewer HTTP requests will be made to Naver.
# 30 min to 1 hour would be a good choice.
# Should be shorter than 1 day.
SERIES_STATS_UPDATE_INTERVAL = timedelta(hours=1)

# Used to set a permanent cache.
CACHE_PERMANENT = 86400 * 365 * 10


browser = NaverBrowser(app)


def update_series_list(update_all=False):
    fetched = cache.get('series_list_fetched')
    if (update_all or fetched is None or
            fetched + SERIES_STATS_UPDATE_INTERVAL < datetime.now()):
        _fetch_series_list(update_all)
        cache.set('series_list_fetched', datetime.now(), CACHE_PERMANENT)


def _fetch_series_list(update_all):
    fetched_data = {}
    for data in browser.get_series_list():
        info = fetched_data.setdefault(data['id'], {})
        info.setdefault('update_days', []).append(data['day'])
        if info.get('updated') is None or data['updated']:
            info['updated'] = data['updated']
    series_list = Series.query.all()
    series_ids = set()
    for series in series_list:
        series_ids.add(series.id)
        if update_all:
            update_series(series, add_new_chapters=update_all, do_commit=False)
        info = fetched_data.get(series.id)
        if info is None:
            # The series is completed or somehow not showing up in the index
            continue
        series.update_days = ','.join(info['update_days'])
        if not series.last_update_status and info['updated']:
            series.new_chapters_available = True
        series.last_update_status = info['updated']
    for series_id in fetched_data.viewkeys() - series_ids:
        series = Series(id=series_id)
        update_series(series, add_new_chapters=update_all, do_commit=False)
    _commit()


def update_series(series, add_new_chapters=True, do_commit=True):
    _fetch_series_data(series)
    db.session.add(series)
    if add_new_chapters and series.new_chapters_available:
        _add_new_chapters(series)
        series.new_chapters_available = False
    if do_commit:
        _commit()


def _commit():
    try:
        db.session.commit()
    except IntegrityError:
        app.logger.error('IntegrityError', exc_info=True)
        db.session.rollback()


def _fetch_series_data(series):
    data = browser.get_series_data(series.id)
    if data.get('removed'):
        if not series.is_completed:
            app.logger.warning('Series #%d seems removed', series.id)
            series.is_completed = True
    else:
        series.title = data['title']
        series.author = data['author']
        series.description = data['description']
        series.last_chapter = data['last_chapter']
        series.is_completed = data['is_completed']
        series.thumbnail_url = data['thumbnail_url']


def _fetch_chapter_data(chapter):
    data = browser.get_chapter_data(chapter.series.id, chapter.id, tz)
    if data.get('not_found'):
        raise Chapter.DoesNotExist
    chapter.title = data['title']
    chapter.pubdate = data['pubdate']
    chapter.thumbnail_url = data['thumbnail_url']


def _add_new_chapters(series):
    current_last_chapter = series.chapters[0].id if len(series.chapters) else 0
    start = current_last_chapter + 1
    chapter_ids = range(start, series.last_chapter + 1)
    for chapter_id in chapter_ids:
        chapter = Chapter(series=series, id=chapter_id)
        try:
            _fetch_chapter_data(chapter)
        except Chapter.DoesNotExist:
            continue
        db.session.add(chapter)
