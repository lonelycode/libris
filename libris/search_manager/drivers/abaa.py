import requests
import inspect
from lxml import html


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


class AbaaResult(BaseResult):
    def __init__(self):
        super(AbaaResult, self).__init__()
        self.title = '//*[@id="search-result-block"]/div/div/a[@class="srtitle"]/text()'
        self.author = '//*[@id="search-result-block"]/div/div/div[@class="srauthor"]/text()'
        self.description = '//*[@id="search-result-block"]/div/div/div[@class="desc"]/text()'
        self.price = '//*[@id="search-result-block"]/div/div/div/div[@class="price"]/text()'
        self.seller = '//*[@id="search-result-block"]/div/div/div[@class="offered_by"]/a/text()'


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

        page_tree = self._get_tree(body)
        if self.result_model:
            new_model = self.result_model()
            fields = new_model.get_field_xpaths()
            for field in fields:
                path = field[1]
                if path:
                    field_values = page_tree.xpath(path)
                    results_object[field[0]] = field_values

        return results_object

    def package_results(self, raw_results):
        result_list = []
        index = 0

        results_dict = raw_results[0]
        base_result_obj = {key: None for key, values in results_dict.iteritems()}

        for key in results_dict.keys():
                


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
        parsed_results = self.get_results(first_page)
        result_array.append(parsed_results)

        # for i in range(2, pages+1):
        #     body = self.search(page=str(i), **kwargs)
        #     parsed_results = self.get_results(body)
        #     if parsed_results:
        #         result_array.append(parsed_results)

        return result_array

a = AbaaDriver()
res = a.do_search(author="Charles Dickens", title="The Pickwick Papers")

print "RESULTS!"
print res