class Path(object):
    def __init__(self, xpath, is_block=True, is_list=False, is_unique=False):
        self.xpath = xpath
        self.is_block = is_block
        self.is_list = is_list
        self.is_unique = is_unique