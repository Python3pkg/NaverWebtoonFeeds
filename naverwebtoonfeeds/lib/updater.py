from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from naverwebtoonfeeds import app, cache, db, CACHE_PERMANENT
from naverwebtoonfeeds.models import Series, Chapter
from naverwebtoonfeeds.lib.naver import as_naver_time_zone, NaverBrowser


__browser__ = NaverBrowser(app)


def update_series_list(update_all=False):
    fetched = cache.get('series_list_fetched')
    if (update_all or fetched is None or
            fetched + _series_stats_update_interval() < datetime.utcnow()):
        _fetch_series_list(update_all)
        cache.set('series_list_fetched', datetime.utcnow(), CACHE_PERMANENT)


def _series_stats_update_interval():
    # The longer this interval, the fewer HTTP requests will be made to Naver.
    # 30 min to 1 hour would be a good choice.
    # Should be shorter than 1 day.
    hour = as_naver_time_zone(datetime.utcnow()).hour
    if 23 <= hour or hour < 1:
        return timedelta(minutes=15)
    elif 1 <= hour < 3:
        return timedelta(minutes=30)
    else:
        return timedelta(hours=1)


def _fetch_series_list(update_all):
    updated = False
    fetched_data = {}
    try:
        issues = __browser__.get_issues()
    except:
        app.logger.error("An error occurred while getting series list",
                exc_info=True)
        return
    for data in issues:
        info = fetched_data.setdefault(data['id'], {})
        info.setdefault('update_days', []).append(data['day'])
        days_updated = info.setdefault('days_updated', [])
        if data['days_updated']:
            days_updated.append(data['days_updated'])
    series_list = Series.query.all()
    series_ids = set()
    for series in series_list:
        series_ids.add(series.id)
        if update_all:
            updated |= update_series(series, add_new_chapters=update_all,
                    do_commit=False)
        info = fetched_data.get(series.id)
        if info is None:
            # The series is completed or somehow not showing up in the index
            continue
        series.update_days = ','.join(info['update_days'])
        if any(day not in series.last_update_status for day in info['days_updated']):
            series.new_chapters_available = True
        series.last_update_status = ','.join(info['days_updated'])
    for series_id in fetched_data.viewkeys() - series_ids:
        series = Series(id=series_id)
        updated |= update_series(series, add_new_chapters=update_all,
                do_commit=False)
    _commit()
    return updated


def update_series(series, add_new_chapters=True, do_commit=True):
    updated = _fetch_series_data(series)
    db.session.add(series)
    if add_new_chapters and series.new_chapters_available:
        updated |= _add_new_chapters(series)
        series.new_chapters_available = False
        # updated indicates the view cache should be purged.
        # new_chapters_available doesn't affect the view, so it doesn't set
        # updated to True.
    if do_commit:
        _commit()
    return updated


def _commit():
    try:
        db.session.commit()
    except IntegrityError:
        app.logger.error('IntegrityError', exc_info=True)
        db.session.rollback()


def _fetch_series_data(series):
    try:
        data = __browser__.get_series_data(series.id)
    except:
        app.logger.error("An error occurred while getting data for series #%d",
                series.id, exc_info=True)
        return
    if data.get('removed'):
        if not series.is_completed:
            app.logger.warning('Series #%d seems removed', series.id)
            series.is_completed = True
            return True
    else:
        attributes = ['title', 'author', 'description', 'last_chapter',
                'is_completed', 'thumbnail_url']
        return _update_attributes(series, data, attributes)


def _fetch_chapter_data(chapter):
    try:
        data = __browser__.get_chapter_data(chapter.series.id, chapter.id)
    except:
        app.logger.error("An error occurred while getting data for chapter #%d of series #%d",
                chapter.id, chapter.series.id, exc_info=True)
        return False
    if data.get('not_found'):
        raise Chapter.DoesNotExist
    attributes = ['title', 'pubdate', 'thumbnail_url']
    return _update_attributes(chapter, data, attributes)


def _update_attributes(object, data, attribute_names):
    updated = False
    for attribute_name in attribute_names:
        if getattr(object, attribute_name) != data[attribute_name]:
            updated = True
            setattr(object, attribute_name, data[attribute_name])
    return updated


def _add_new_chapters(series):
    current_last_chapter = series.chapters[0].id if len(series.chapters) else 0
    start = current_last_chapter + 1
    chapter_ids = range(start, series.last_chapter + 1)
    for chapter_id in chapter_ids:
        chapter = Chapter(series=series, id=chapter_id)
        try:
            success = _fetch_chapter_data(chapter)
        except Chapter.DoesNotExist:
            continue
        if success:
            db.session.add(chapter)
