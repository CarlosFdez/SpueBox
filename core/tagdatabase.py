import shelve

class InvalidTagException(Exception):
    pass

class TagDatabase:
    '''A class used to store and retrieve tags for individual users'''
    def _validate_tagname(self, name):
        if len(name) > 50:
            raise InvalidTagException('Tag too long')

    def set(self, user_id, name, value):
        self._validate_tagname(name)
        with shelve.open('database/tag.sdb') as s:
            userkey = 'user_{}'.format(user_id)
            data = s.get(userkey, {})
            data[name] = value
            s[userkey] = data

    def get(self, user_id, name):
        'gets the tag identified by the name for that user. Raises KeyError if does not exist'
        self._validate_tagname(name)
        with shelve.open('database/tag.sdb') as s:
            data = s.get('user_{}'.format(user_id), {})
            return data[name]

    def try_get(self, user_id, name, default=None):
        '''Gets the tag identified by name for that user, returning default if it doesn't exist.
        It can still throw data related errors'''
        try:
            return self.get(user_id, name)
        except KeyError:
            return default
        except InvalidTagException:
            return default

    def keys_for(self, user_id):
        '''Shows all tags belonging to that user'''
        with shelve.open('database/tag.sdb') as s:
            data = s.get('user_{}'.format(user_id), {})
            return data.keys()
