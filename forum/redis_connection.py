import datetime
import time

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

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

def increment_viewcount(topic):
    r.incr('views%s' % topic.pk, 1)

def get_viewcounts(topics):
    for view_count in r.mget(['views%s' % t.pk for t in topics]):
        if view_count:
            yield int(view_count)
        else:
            yield 0

def set_tracker(user, topic):
    key = 'u%st%s' % (user.pk, topic.pk)
    timestamp = datetime.datetime.now()
    expire_at = timestamp + datetime.timedelta(days=14)
    r.set(key, timestamp.strftime(TIMESTAMP_FORMAT))
    r.expireat(key, int(time.mktime(expire_at.timetuple())))

def get_tracker(user, topic_id):
    last_read = r.get('u%st%s' % (user.pk, topic_id))
    if last_read:
        print(last_read)
        return datetime.datetime.strptime(last_read, TIMESTAMP_FORMAT)
    return None

def get_trackers(user, topics):
    for last_read in r.mget(['u%st%s' % (user.pk, t.pk) for t in topics]):
        if last_read:
            yield datetime.datetime.strptime(last_read, TIMESTAMP_FORMAT)
        else:
            yield None
