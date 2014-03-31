import requests
from lxml import html
from base_result import BaseResult
from libris.settings.log_config import *
logger = logging.getLogger("abaa-driver")


class AbaaResult(BaseResult):
    def __init__(self):
        super(AbaaResult, self).__init__()
        self.__block__ = '//*[@id="search-result-block"]/div/div[@class="span-15"]'
        self.title = './a[@class="srtitle"]/text()'
        self.author = './div[@class="srauthor"]/text()'
        self.description = './div[@class="desc"]/text()[normalize-space()]'
        self.price = '../div[@class="span-3 last"]/div[@class="order-box"]/div[@class="price"]/text()[normalize-space()]'
        self.seller_link = './a[@class="srtitle"]/@href'
        self.image = './a/img[@class="photo"]/@src'


class AbaaDriver(object):
    def __init__(self):
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

    @staticmethod
    def _get_tree(body):
        tree = html.fromstring(body)
        return tree

    def get_pages(self, body):
        page_tree = self._get_tree(body)
        pages = page_tree.xpath(self.page_xpath)

        if pages:
            return int(pages[-1])
        else:
            return 0

    def get_results(self, body):
        results_object = {}

        page_tree = body
        if self.result_model:
            new_model = self.result_model()
            fields = new_model.get_field_xpaths()
            for field in fields:
                path = field[1]
                if path:
                    field_values = page_tree.xpath(path)
                    if field_values:
                        results_object[field[0]] = self.clean_result(field_values[0])

        return results_object

    def get_blocks(self, body):
        page_tree = self._get_tree(body)
        new_model = self.result_model()
        base_path = new_model.__block__
        blocks = page_tree.xpath(base_path)
        print len(blocks)

        return blocks

    @staticmethod
    def clean_result(result_text):
        new_text = result_text.encode("utf-8")
        new_text = new_text.replace("\n", "").strip()
        return new_text

    def search(self, **kwargs):
        payload = {}
        for key, value in kwargs.iteritems():
            this_key = self.field_map.get(key, key)
            payload[this_key] = value

        search_request = None
        if self.method.lower() == "get":
            search_request = requests.get(self.target, params=payload)

        if self.method.lower() == "post":
            search_request = requests.post(self.target, params=payload)

        if search_request:
            if search_request.status_code != 200:
                return False
            else:
                return search_request.text

    def do_search(self, **kwargs):
        result_array = []

        first_page = self.search(**kwargs)
        pages = self.get_pages(first_page)
        blocks = self.get_blocks(first_page)
        for block in blocks:
            parsed_results = self.get_results(block)
            result_array.append(parsed_results)

        for i in range(2, pages+1):
            body = self.search(page=str(i), **kwargs)
            blocks = self.get_blocks(body)
            for block in blocks:
                parsed_results = self.get_results(block)
                result_array.append(parsed_results)

        logger.info("Total results: %d" % len(result_array))
        return result_array

a = AbaaDriver()
res = a.do_search(author="Charles Dickens", title="The Pickwick Papers")

for item in res[:5]:
    print "%s [%s], Has Image: %s" % (item.get("title", "NO TITLE FOUND"), item.get("price", "not found"), item.get("image", "None"))