import sys
import os
from raven import Client
from loadzen.settings.global_api_config import sentry_api_key


if 'LZ_TEST_ENV' not in os.environ.keys():
    client = Client(sentry_api_key)

    old_except_hook = sys.excepthook

    def generic_exception_wrapper(type, value, traceback):
        print 'THIS IS CUSTOM: %s %s %s' % (str(type), str(value), str(traceback))
        old_except_hook(type, value, traceback)
        client.captureException(exc_info=(type, value, traceback))

    sys.excepthook = generic_exception_wrapper