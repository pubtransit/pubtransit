import logging


LOG = logging.getLogger()

REST_API = []


def rest_function(func):
    REST_API.append(func)


@rest_function
def get_stops(lat, lon):  # pylint: disable=unused-argument
    return []
