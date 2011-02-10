"""
Redis session store by Adam Gomaa

http://hg.gomaa.us/agdj/file/tip/agdj/lib/redis_session_backend.py
"""
from cPickle import loads, dumps

from django.contrib.sessions.backends.base import SessionBase, CreateError
from django.conf import settings

from forum.redis_connection import r

class SessionStore(SessionBase):
    """
    A redis-based session store.
    """
    def __init__(self, session_key=None):
        super(SessionStore, self).__init__(session_key)

    def load(self):
        session_data = r.get(self.session_key)
        if session_data is not None:
            return loads(session_data)
        self.create()
        return {}

    def create(self):
        while True:
            self.session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                # Would be raised if the key wasn't unique
                continue
            self.modified = True
            return

    def save(self, must_create=False):
        if must_create:
            # preserve=True -> SETNX
            result = r.set(
                self.session_key, dumps(self._get_session(no_load=must_create)), preserve=True)
            if result == 0: # 0 == not created, 1 == created.
                raise CreateError
        else:
            r.set(self.session_key, dumps(self._get_session(no_load=must_create)),)

    def exists(self, session_key):
        if r.exists(session_key):
            return True
        return False

    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self._session_key
        r.delete(session_key)

