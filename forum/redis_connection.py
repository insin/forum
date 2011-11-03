"""
Connection and forum API for real-time tracking using Redis.
"""
import datetime
import time

from django.core import signals
from django.utils.html import escape

import redis
from forum import app_settings

r = redis.StrictRedis(app_settings.REDIS_HOST,
                      app_settings.REDIS_PORT,
                      app_settings.REDIS_DB)

TOPIC_ViEWS = 't:%s:v'
TOPIC_TRACKER = 'u:%s:t:%s'
ACTIVE_USERS = 'au'
USER_USERNAME = 'u:%s:un'
USER_LAST_SEEN = 'u:%s:s'
USER_DOING = 'u:%s:d'

def increment_view_count(topic):
    """Increments the view count for a Topic."""
    r.incr(TOPIC_ViEWS % topic.pk)

def get_view_counts(topic_ids):
    """Yields viewcounts for the given Topics."""
    for view_count in r.mget([TOPIC_ViEWS % id for id in topic_ids]):
        if view_count:
            yield int(view_count)
        else:
            yield 0

def update_last_read_time(user, topic):
    """
    Sets the last read time for a User in the given Topic, expiring in a
    fortnight.
    """
    key = TOPIC_TRACKER % (user.pk, topic.pk)
    last_read = datetime.datetime.now()
    expire_at = last_read + datetime.timedelta(days=14)
    r.set(key, int(time.mktime(last_read.timetuple())))
    r.expireat(key, int(time.mktime(expire_at.timetuple())))

def get_last_read_time(user, topic_id):
    """Gets the last read time for a User in the given Topic."""
    last_read = r.get(TOPIC_TRACKER % (user.pk, topic_id))
    if last_read:
        return datetime.datetime.fromtimestamp(int(last_read))
    return None

def get_last_read_times(user, topics):
    """Gets last read times for a User in the given Topics."""
    for last_read in r.mget([TOPIC_TRACKER % (user.pk, t.pk)
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
    r.zadd(ACTIVE_USERS, last_seen, user.pk)
    r.setnx(USER_USERNAME % user.pk, user.username)
    r.set(USER_LAST_SEEN % user.pk, last_seen)
    if item:
        doing = '%s <a href="%s">%s</a>' % (
            doing, item.get_absolute_url(), escape(str(item)))
    r.set(USER_DOING % user.pk, doing)

def get_active_users(minutes_ago=30):
    """
    Yields active Users in the last ``minutes_ago`` minutes, returning
    2-tuples of (user_detail_dict, last_seen_time) in most-to-least recent
    order by time.
    """
    since = datetime.datetime.now() - datetime.timedelta(minutes=minutes_ago)
    since_time = int(time.mktime(since.timetuple()))
    for user_id, last_seen in reversed(r.zrangebyscore(ACTIVE_USERS, since_time,
                                                       'inf', withscores=True)):
        yield (
            {'id': int(user_id), 'username': r.get(USER_USERNAME % user_id)},
            datetime.datetime.fromtimestamp(int(last_seen)),
        )

def get_last_seen(user):
    """
    Returns a 2-tuple of (last_seen, doing), where doing may contain HTML
    linking to the relevant place.
    """
    last_seen = r.get(USER_LAST_SEEN % user.pk)
    if last_seen:
        last_seen = datetime.datetime.fromtimestamp(int(last_seen))
    else:
        last_seen = user.date_joined
    doing = r.get(USER_DOING % user.pk)
    return last_seen, doing
