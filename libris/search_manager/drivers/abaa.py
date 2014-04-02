from libris.search_manager.helpers.base_result import BaseResult
from libris.search_manager.helpers.path_description import Path
from base_driver import BaseDriver
from libris.settings.log_config import *
logger = logging.getLogger("abaa-driver")


class AbaaResult(BaseResult):
    def __init__(self):
        super(AbaaResult, self).__init__()
        self.__block__ = '//*[@id="search-result-block"]/div/div[@class="span-15"]'
        self.title = Path('./a[@class="srtitle"]/text()')
        self.author = Path('./div[@class="srauthor"]/text()')
        self.description = Path('./div[@class="desc"]/text()[normalize-space()]')
        self.price = Path('//*[@id="search-result-block"]/div/div[@class="span-3 last"]/div[@class="order-box"]/div[@class="price"]/text()[normalize-space()]',
                          is_block=False,
                          is_list=True)
        self.seller_link = Path('./a[@class="srtitle"]/@href')
        self.image = Path('./a/img[@class="photo"]/@src')


class AbaaDriver(BaseDriver):
    def __init__(self):
        super(AbaaDriver, self).__init__()
        # Only include different fields, otherwise use the default
        self.field_map = {
            "binding": "format",
            "condition": "cond",
            "first_edition": "first",
            "signed": "signed",
            "dust_jacket": "dj",
            "price_min": "minprice",
            "price_max": "maxprice",
            "date_min": "mindate",
            "date_max": "maxdate"
        }

        self.result_model = AbaaResult
        self.target = "http://www.abaa.org/search.php"
        self.method = "get"
        self.crawl_parameter_name = "page"
        self.page_xpath = '//*[@id="search-result-block"]/div/div[1]/div[3]/div/div/span/a/text()'