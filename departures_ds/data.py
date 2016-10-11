'''
Created on 10 Oct 2016

@author: fressi
'''

import collections
import logging

import msgpack
import msgpack_numpy
import numpy
import pandas
import zlib


LOG = logging.getLogger(__name__)

Rectangle = collections.namedtuple(
    'Rectangle', ['west', 'south', 'east', 'north'])


class DataStore(object):

    def __init__(self):
        self.feeds = []
        self.stops = pandas.DataFrame()
        self.routes = pandas.DataFrame()
        self.trips = pandas.DataFrame()
        self.stop_times = pandas.DataFrame()

    def put_feed(self, name, url, stops, routes, trips, stop_times):
        stops_offset = len(self.stops.index)
        stops_indexer = Indexer(stops_offset, stops.pop('stop_id'))
        self.stops = self.stops.append(pandas.DataFrame(stops))
        del stops

        routes_offset = len(self.routes.index)
        routes_indexer = Indexer(routes_offset, routes.pop('route_id'))
        self.routes = self.routes.append(pandas.DataFrame(routes))
        del routes

        trips_offset = len(self.trips.index)
        trips_indexer = Indexer(trips_offset, trips.pop('trip_id'))
        trips['route_id'] = routes_indexer.search(trips.pop('route_id'))
        self.trips = self.trips.append(pandas.DataFrame(trips))
        del trips

        stop_times_offset = len(self.stop_times.index)
        stop_times_indexer = Indexer(stop_times_offset)
        stop_times['trip_id'] = trips_indexer.search(stop_times.pop('trip_id'))
        stop_times['stop_id'] = stops_indexer.search(stop_times.pop('stop_id'))
        self.stop_times = self.stop_times.append(pandas.DataFrame(stop_times))
        del stop_times

        feed_id = len(self.feeds)
        self.feeds.append(
            Feed(name=name, url=url, stops=stops_indexer,
                 routes=routes_indexer, trips=trips_indexer,
                 stop_times=stop_times_indexer))
        return feed_id

    def pack_tiles(self, zoom_level=16):
        for i, j, tile in self.iter_tiles(zoom_level=zoom_level):
            packet = self.pack_tile(tile=tile)
            if packet is not None:
                yield i, j, packet

    def iter_tiles(self, zoom_level):
        for i, west, east in self.iter_space(-180., 180., zoom_level):
            for j, south, north in self.iter_space(-90., 90., zoom_level):
                yield i, j, Rectangle(west=west, south=south,
                                      east=east, north=north)

    def iter_space(self, start, stop, zoom_level):
        count = 2 ** zoom_level
        space = numpy.linspace(start, stop, count + 1, endpoint=True)
        assert space.shape == (count + 1,)
        for i in range(0, count):
            yield i, space[i], space[i] + 1

    def pack_tile(self, tile):
        stops = self.stops
        lat = numpy.asarray(stops['lat'])
        lon = numpy.asarray(stops['lon'])
        stops_selection = numpy.logical_and(
            numpy.logical_and(lat > tile.south, lat < tile.north),
            numpy.logical_and(lon > tile.west, lon < tile.east))
        stops_indexes, = stops_selection.nonzero()
        if len(stops_indexes) > 0:
            return None

        stops = stops.iloc[stops_indexes]
        stops = {column: numpy.asarray(stops[column])
                 for column in stops.columns}

        stop_times = self.stop_times
        stop_time_stop_ids = numpy.asarray(stop_times['stop_id'])
        stop_times_selection = stops_selection[stop_time_stop_ids]
        stop_times_indexes, = stop_times_selection.nonzero()
        stop_times = stop_times.iloc[stop_times_indexes]
        stop_times = {column: numpy.asarray(stop_times[column])
                      for column in stop_times.columns}

        trips = self.trips
        stop_time_trip_ids = numpy.asarray(stop_times['trip_id'])
        trips_selection = numpy.zeros(dtype=bool, shape=trips.index.shape)
        trips_selection[stop_time_trip_ids] = True
        trips_selection_indexes, = trips_selection.nonzero()
        trips = trips.iloc[trips_selection_indexes]
        trips = {column: numpy.asarray(trips[column])
                 for column in trips.columns}

        routes = self.routes
        trip_route_ids = numpy.asarray(trips['route_id'])
        routes_selection = numpy.zeros(dtype=bool, shape=routes.index.shape)
        routes_selection[trip_route_ids] = True
        routes_selection_indexes, = routes_selection.nonzero()
        routes = routes.iloc[routes_selection_indexes]
        routes = {column: numpy.asarray(routes[column])
                  for column in routes.columns}

        data = {
            'bounds': {'west': tile.west, 'south': tile.south,
                       'east': tile.east, 'north': tile.north},
            'stops': stops,
            'routes': routes,
            'trips': trips,
            'stop_times': stop_times
        }

        packed = msgpack.packb(data, default=msgpack_numpy.encode)
        return zlib.compress(packed, 9)


def table_arrays(**arrs):
    names = list(arrs)
    expected_size = len(arrs[names[0]])
    for name in names[1:]:
        arr = arrs[name]
        actual_size = len(arr)
        if expected_size != actual_size:
            raise ValueError(
                "Array '{name}' should have size {expected_size} "
                "instead of {actual_size}.".format(
                    name=name, expected_size=expected_size,
                    actual_size=actual_size))
    return arrs


def stop_arrays(stop_id, name, lon, lat):
    return table_arrays(
        stop_id=numpy.asarray(stop_id, dtype=object),
        name=numpy.asarray(name, dtype=object),
        lon=numpy.asarray(lon, dtype=float),
        lat=numpy.asarray(lat, dtype=float))


def route_arrays(route_id, name):
    return table_arrays(
        route_id=numpy.asarray(route_id, dtype=object),
        name=numpy.asarray(name, dtype=object))


def trip_arrays(trip_id, route_id, name):
    return table_arrays(
        trip_id=numpy.asarray(trip_id, dtype=object),
        route_id=numpy.asarray(route_id, dtype=object),
        name=numpy.asarray(name, dtype=object))


def stop_time_arrays(trip_id, stop_id, departure_time):
    return table_arrays(
        trip_id=numpy.asarray(trip_id, dtype=object),
        stop_id=numpy.asarray(stop_id, dtype=object),
        departure_time=numpy.asarray(departure_time, dtype=object))



class Feed(object):

    def __init__(self, name, url, stops, routes, trips, stop_times):
        self.name = name
        self.url = url
        self.stops = stops
        self.routes = routes
        self.trips = trips
        self.stop_times = stop_times


class Indexer(object):

    _ids = None
    _sorter = None

    def __init__(self, offset, ids=None):
        self._offset = offset
        if ids is not None:
            self._ids = ids
            self._sorter = numpy.argsort(ids)

    def search(self, ids):
        if self._ids is None:
            raise ValueError("Ids for looking for where never given.")

        indexes = numpy.searchsorted(self._ids, ids, sorter=self._sorter)
        errors, = (indexes >= len(self._ids)).nonzero()
        if errors.size:
            raise ValueError("Invalid ids: " + ids[errors])
        return indexes + self._offset

