import inspect


class BaseResult(object):
    def __init__(self):
        self.title = None
        self.author = None
        self.description = None
        self.image = None
        self.price = None
        self.seller = None

    def get_field_xpaths(self):
        attributes = inspect.getmembers(self, lambda a:not(inspect.isroutine(a)))
        these_attrs = [a for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))]

        return these_attrs
