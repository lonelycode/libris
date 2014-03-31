import logging

logging.basicConfig(
    format='[%(asctime)s][%(levelname)s][%(name)s]: %(message)s',
    datefmt='%d/%m/%y %H:%M:%S',
    level=logging.INFO
)

logging.info("Setting up Logging Format")