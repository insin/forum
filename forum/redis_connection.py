"""
Connection and forum API for real-time tracking using Redis.
"""
import datetime
import time

from django.utils.html import escape

def get_instance():
    import redis
    from forum import app_settings
    from django.core import signals
    r = redis.Redis(app_settings.REDIS_HOST,
                    app_settings.REDIS_PORT,
                    app_settings.REDIS_DB)
    # Ensure we disconnect at the end of the request cycle
    signals.request_finished.connect(
        lambda **kwargs: r.connection.disconnect()
    )
    return r

r = get_instance()

def increment_view_count(topic):
    """Increments the view count for a Topic."""
    r.incr('topic:%s:views' % topic.pk)

def get_view_counts(topics):
    """Yields viewcounts for the given Topics."""
    for view_count in r.mget(['topic:%s:views' % t.pk for t in topics]):
        if view_count:
            yield int(view_count)
        else:
            yield 0

def update_last_read_time(user, topic):
    """
    Sets the last read time for a User in the given Topic, expiring in a
    fortnight.
    """
    key = 'user:%s:topictracker:%s' % (user.pk, topic.pk)
    last_read = datetime.datetime.now()
    expire_at = last_read + datetime.timedelta(days=14)
    r.set(key, int(time.mktime(last_read.timetuple())))
    r.expireat(key, int(time.mktime(expire_at.timetuple())))

def get_last_read_time(user, topic_id):
    """Gets the last read time for a User in the given Topic."""
    last_read = r.get('user:%s:topictracker:%s' % (user.pk, topic_id))
    if last_read:
        return datetime.datetime.fromtimestamp(int(last_read))
    return None

def get_last_read_times(user, topics):
    """Gets last read times for a User in the given Topics."""
    for last_read in r.mget(['user:%s:topictracker:%s' % (user.pk, t.pk)
                             for t in topics]):
        if last_read:
            yield datetime.datetime.fromtimestamp(int(last_read))
        else:
            yield None

def seen_user(user, doing, item=None):
    """
    Stores what a User was doing when they were last seen and updates
    their last seen time in the active users sorted set.
    """
    last_seen = int(time.mktime(datetime.datetime.now().timetuple()))
    r.zadd('activeusers', user.pk, last_seen)
    r.set('user:%s:lastseen' % user.pk, last_seen)
    if item:
        doing = '%s <a href="%s">%s</a>' % (
            doing, item.get_absolute_url(), escape(str(item)))
    r.set('user:%s:lastseendoing' % user.pk, doing)

def get_active_users(minutes_ago=30):
    """
    Yields active Users in the last ``minutes_ago`` minutes, returning
    2-tuples of (user_id, last_seen_time) in low-to-high order by time.
    """
    since = datetime.datetime.now() - datetime.timedelta(minutes=minutes_ago)
    since_time = int(time.mktime(since.timetuple()))
    for user_id, last_seen in r.zrangebyscore('activeusers', since_time,
                                              'max', withscores=True):
        yield user_id, datetime.datetime.fromtimestamp(int(last_read))

def get_last_seen(user):
    """
    Returns a 2-tuple of (last_seen, doing), where doing may contain HTML
    linking to the relevant place.
    """
    last_seen = r.get('user:%s:lastseen' % user.pk)
    if last_seen:
        last_seen = datetime.datetime.fromtimestamp(int(last_seen))
    else:
        last_seen = user.date_joined
    doing = r.get('user:%s:lastseendoing' % user.pk)
    return last_seen, doing