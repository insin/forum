from django.contrib.sessions.backends.base import SessionBase, CreateError

from forum.redis_connection import r

class SessionStore(SessionBase):
    """
    Implements a Redis session store.
    """
    def load(self):
        session_data = r.get('session:%s' % self.session_key)
        if session_data is not None:
            return self.decode(session_data)
        self.create()
        return {}

    def exists(self, session_key):
        if r.exists('session:%s' % session_key):
            return True
        return False

    def create(self):
        while True:
            self.session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            return

    def save(self, must_create=False):
        key = 'session:%s' % self.session_key
        if must_create and r.exists(key):
            raise CreateError
        r.set(key, self.encode(self._get_session(no_load=must_create)))
        r.expire(key, self.get_expiry_age())

    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self._session_key
        r.delete('session:%s' % session_key)
