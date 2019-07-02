from functools import update_wrapper
class cached_property(object):
    """
     A property that is only computed once per instance and then replaces itself
     with an ordinary attribute. Deleting the attribute resets the property.
     Source: https://github.com/bottlepy/bottle/blob/c8179b28d93b2875a31866c6b84a9b5b59c0c8b4/bottle.py#L233
     """

    def __init__(self, func):
        update_wrapper(self,func)
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value