import logging


class SimpleHandler(logging.Handler):
    logged = []

    def emit(self, record):
        SimpleHandler.logged.append(record)
