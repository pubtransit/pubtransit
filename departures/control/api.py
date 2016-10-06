import logging
import random

LOG = logging.getLogger()

REST_API = []


def rest_function(func):
    REST_API.append(func)


@rest_function
def get_stops(lat, lng):  # pylint: disable=unused-argument
    return [
        {"lat": lat + random.uniform(-0.001, 0.001),
         "lng": lng + random.uniform(-0.001, 0.001)}
        for _ in range(random.randrange(3, 7))]

@rest_function
def get_buses(lat, lng):  # pylint: disable=unused-argument
    return [
        {"line": random.randrange(1, 343),
         "time": lng + random.uniform(0., 60.)}
        for _ in range(random.randrange(3, 7))]
