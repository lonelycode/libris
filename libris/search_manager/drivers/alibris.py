from libris.search_manager.helpers.base_result import BaseResult
from libris.search_manager.helpers.path_description import Path
from base_driver import BaseDriver
from libris.settings.log_config import *
logger = logging.getLogger("alibris-driver")


class AlibrisResult(BaseResult):
    def __init__(self):
        super(AlibrisResult, self).__init__()
        self.__block__ = '//*[@id="copies"]/li'
        self.title = Path('./div[@class="content"]/div[@class="header"]/div[@class="title"]/h2/a/text()[normalize-space()]')
        self.author = Path('./div[@class="content"]/div[@class="header"]/div[@class="title"]/h3/text()[normalize-space()]')
        self.description = Path('./div[@class="more"]/p[@class="description"]/span/text()[normalize-space()]')
        self.price = Path('./div[@class="content"]/div[@class="header"]/div[@class="price"]/p/span/text()[normalize-space()]')
        self.seller_link = Path('./div[@class="content"]/div[@class="header"]/div[@class="title"]/h2/a/@href')


class AlibrisDriver(BaseDriver):
    def __init__(self):
        super(AlibrisDriver, self).__init__()
        # Only include different fields, otherwise use the default
        self.field_map = {
            "author": "wauth",
            "title": "wtit",
            "isbn": "qisbn",
            "keywords": "wquery",
            "publisher": "qpub",
            "date_min": "qyear",
            "date_max": "qyearhi",
            "price_min": "qprice",
            "price_max": "qpricehi",
            "first_edition": "first",
            "dust_jacket": "dj",
        }

        self.result_model = AlibrisResult
        self.target = "http://www.alibris.com/booksearch"
        self.method = "get"
        self.crawl_parameter_name = "page"
        self.page_xpath = '//*[@id="ajax-data-content"]/div[3]/div/a[1]/text()'
        self.do_paging = True
        self.inject_search_params = {
            'collectible': '1',
            'qsort': 'p'
        }


a = AlibrisDriver()
res = a.do_search(author="Charles Dickens", title="Sketches by Boz")

p_index = 0
for item in res[:50]:
    p_index += 1
    img = False
    if item.get("image", False):
        img = True
    print "[%d] [Price: %s] [Img: %s] [Title: %s]" % (p_index, item.get("price", "not found"), str(img), item.get("title", "NO TITLE FOUND"))