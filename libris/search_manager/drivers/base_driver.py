import requests
from lxml import html
from libris.settings.log_config import *
logger = logging.getLogger("base-driver")


class BaseDriver(object):
    def __init__(self):
        # Only include different fields, otherwise use the default
        self.field_map = {}

        self.result_model = None
        self.target = None
        self.method = "get"
        self.crawl_parameter_name = "page"
        self.page_xpath = ''

    @staticmethod
    def _get_tree(body):
        tree = html.fromstring(body)
        return tree

    def pre_process_pages(self, pages):
        return pages

    def get_pages(self, body):
        page_tree = self._get_tree(body)
        pages = page_tree.xpath(self.page_xpath)

        if pages:
            return self.pre_process_pages(int(pages[-1]))
        else:
            return 0

    def _get_model_fields(self):
        if self.result_model:
            new_model = self.result_model()
            fields = new_model.get_field_xpaths()
            return fields
        else:
            return []

    def find_list_results(self, html):
        logger.info("Processing list results")
        fields = self._get_model_fields()
        list_results = {}
        for field in fields:
            if field[1]:
                if field[1].is_list:
                    logger.info("Processing: %s" % field[0])

                    field_values = self._get_tree(html).xpath(field[1].xpath)
                    cleaned_results = []
                    if field_values:
                        for value in field_values:
                            result = self.clean_result(value)
                            cleaned_results.append(result)

                    list_results[field[0]] = cleaned_results

        return list_results

    def find_block_results(self, html):
        logger.info("Processing block results")
        fields = self._get_model_fields()
        blocks = self.get_blocks(html)
        cleaned_results = []

        for block in blocks:
            this_result = {}

            for field in fields:
                if field[1]:
                    if field[1].is_block:
                        field_values = block.xpath(field[1].xpath)
                        if field_values:
                            for value in field_values:
                                result = self.clean_result(value)
                                this_result[field[0]] = result
                        else:
                            logger.info("No results found for %s: " % field[1].xpath)

            cleaned_results.append(this_result)

        return cleaned_results

    def zip_list_and_blocks(self, block_results, list_results):
        # Assume that blocks and list result units are the same length
        # Assume that block results should include list results as fields

        for field_name, list_item_results in list_results.iteritems():
            if len(block_results) != len(list_item_results):
                logging.error("Could not zip results for %s - lists not same length!" % field_name)
            else:
                block_index = 0
                for block_result in block_results:
                    block_results[block_index][field_name] = list_item_results[block_index]
                    block_index += 1

        return block_results

    def get_blocks(self, body):
        page_tree = self._get_tree(body)
        new_model = self.result_model()
        base_path = new_model.__block__
        blocks = page_tree.xpath(base_path)

        logger.info("Found %d blocks" % len(blocks))

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
            logger.info("Requested: %s" % search_request.url)

        if self.method.lower() == "post":
            search_request = requests.post(self.target, params=payload)

        if search_request:
            if search_request.status_code != 200:
                return False
            else:
                return search_request.text

    def _process_page(self, page):
        block_results = self.find_block_results(page)
        logger.info("Block results length: %d" % len(block_results))

        list_results = self.find_list_results(page)
        logger.info("List results length: %d" % len(list_results))

        zipped_results = self.zip_list_and_blocks(block_results, list_results)
        logger.info("Zipped results length: %d" % len(zipped_results))

        return zipped_results

    def get_page_range(self, pages):
        return range(2, pages+1, 1)

    def do_search(self, **kwargs):

        first_page = self.search(**kwargs)
        pages = self.get_pages(first_page)

        zipped_results = self._process_page(first_page)

        for i in self.get_page_range(pages):
            logger.info("Processing page: %d" % i)
            kwargs[self.crawl_parameter_name] = str(i)
            body = self.search(**kwargs)
            next_page_results = self._process_page(body)
            zipped_results.extend(next_page_results)

        logger.info("Total results: %d" % len(zipped_results))
        return zipped_results