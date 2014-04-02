from libris.search_manager.helpers.base_result import BaseResult
from libris.search_manager.helpers.path_description import Path
from base_driver import BaseDriver
from libris.settings.log_config import *
logger = logging.getLogger("abebooks-driver")


class AbeBooksResult(BaseResult):
    def __init__(self):
        super(AbeBooksResult, self).__init__()
        self.__block__ = '//*[@id="main"]/div[@class="result-set"]/div[@class="result"]'
        self.title = Path('./div[@class="result-data"]/div[@class="result-detail"]/h2/a/span/text()')
        self.author = Path('./div[@class="result-data"]/div[@class="result-detail"]/div[@class="author"]/strong/span/text()')
        self.description = Path('./div[@class="result-description"]/p/span/text()')
        self.price = Path('./div[@class="result-data"]/div[@class="result-pricing"]/div[@class="item-price"]/span/text()')
        self.seller_link = Path('./div[@class="result-data"]/div[@class="result-detail"]/h2/a/@href')


class AbeBooksDriver(BaseDriver):
    def __init__(self):
        super(AbeBooksDriver, self).__init__()
        # Only include different fields, otherwise use the default
        self.field_map = {
            "author": "an",
            "title": "tn",
            "isbn": "isbn",
            "keywords": "kn",
            "publisher": "pn",
            "date_min": "yrl",
            "date_max": "yrh",
            "price_min": "prl",
            "price_max": "prh",
            "first_edition": "fe",
            "signed": "sgnd",
            "dust_jacket": "dj",
            "binding": "bi",
        }

        self.result_model = AbeBooksResult
        self.target = "http://www.abebooks.com/servlet/SearchResults"
        self.method = "get"
        self.crawl_parameter_name = "bsi"
        self.per_page = 30
        self.page_xpath = '//*[@id="main"]/div[1]/div[2]/a/text()'

    def get_page_range(self, pages):
        maximum = pages * self.per_page
        return range(self.per_page, maximum, self.per_page)


a = AbeBooksDriver()
res = a.do_search(author="Charles Dickens", title="The Pickwick Papers")

p_index = 0
for item in res[:10]:
    p_index += 1
    img = False
    if item.get("image", False):
        img = True
    print "[%d] [Price: %s] [Img: %s] [Title: %s]" % (p_index, item.get("price", "not found"), str(img), item.get("title", "NO TITLE FOUND"))