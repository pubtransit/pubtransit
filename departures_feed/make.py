'''
Created on 11 Oct 2016

@author: fressi
'''

import argparse
import collections
import csv
import logging
import os
import sys
import zipfile
import zlib

import jinja2
import msgpack
import numpy
import pandas
import yaml

import departures_feed


LOG = logging.getLogger(__name__)

OUT_STREAM = sys.stdout

TEMPLATE_MANAGER = jinja2.Environment(
    loader=jinja2.PackageLoader(departures_feed.__name__, ''))

TARGET_METHODS = {}

DEFAULT_STOPS_PER_TILE = 128


def main():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)-15s | %(message)s")

    parser = argparse.ArgumentParser(
        description='Departures transit feed compiler.')

    parser.add_argument(
        '--target', type=str, nargs=1, choices=TARGET_METHODS,
        default='all',
        help='One between: {}'.format(', '.join(TARGET_METHODS)))

    parser.add_argument(
        '--build-dir', type=str, default='build',
        help='Folder where to put produced data.')

    parser.add_argument(
        '--quiet', dest='logging_level', action='store_const',
        const=logging.ERROR, default=None, help='Show only error messages.')

    parser.add_argument(
        '--logging-level', dest='logging_level', default=logging.WARNING,
        type=int,
        help='Set logging level (from {min} to {max}.'.format(
            min=logging.DEBUG, max=logging.FATAL))

    parser.add_argument(
        '--max-stops', dest='max_stops', default=DEFAULT_STOPS_PER_TILE,
        type=int, help='Set maximum number of stops-per-tile.')

    parser.add_argument(
        '--verbose', dest='logging_level', action='store_const',
        const=logging.INFO, default=None, help='Show verbose messages.')

    parser.add_argument(
        '--debug', dest='logging_level', action='store_const',
        const=logging.DEBUG, default=None, help='Show debug messages.')

    parser.add_argument(
        'feed', type=str, default=['feeds.yaml'], nargs='*',
        help='Feed file to extract feed rules from.')

    parser.add_argument(
        '--dest', type=str, help='Destination feed file.')

    args = parser.parse_args()

    if args.logging_level:
        # Raise logging level
        logging.getLogger().setLevel(args.logging_level)

    method = TARGET_METHODS[args.target[0]]

    try:
        for feed in args.feed or [None]:
            method(args, feed)

    except Exception as e:  # pylint: disable=broad-except
        if args.logging_level is logging.DEBUG:
            LOG.fatal("Unhandled exception.", exc_info=1)
        else:
            LOG.fatal(str(e) or str(type(e)))
        exit(1)

    except BaseException:
        logging.warning('interrupted', exc_info=1)
        raise

    else:
        logging.debug('SUCCESS')


def target_method(name):

    def decorator(func):
        TARGET_METHODS[name] = func
        return func

    return decorator


MethodParameters = collections.namedtuple(
    'MethodParameters', ['site', 'feed', 'target_path'])


@target_method("all")
def make_all(args):
    # pylint: disable=unused-argument 
    raise NotImplementedError


@target_method("makefile")
def make_makefiles(args, feed_file=None):
    feeds_conf = read_yaml_file(feed_file or 'feeds.yaml')
    for site in feeds_conf['sites']:
        for feed in site["feeds"]:
            target_path = os.path.join(
                args.build_dir, site["name"], feed["name"])

            if not os.path.isdir(target_path):
                os.makedirs(target_path)

            # pylint: disable=unused-argument,no-member
            OUT_STREAM.write(target_path + ".mk ")
            target_template = TEMPLATE_MANAGER.get_template("feed.mk")
            target_make = target_template.render(
                target=target_path,
                url=site["url"] + '/' + feed["path"],
                make_flags="--logging-level " + str(args.logging_level),
                make_me=' '.join(repr(arg) for arg in sys.argv))
            with open(target_path + ".mk", 'wt') as target_stream:
                target_stream.write(target_make)


@target_method("datastore")
def generate_datastores(args, feed_file):
    dest_dir = os.path.splitext(args.dest or args.source)[0]
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)

    with zipfile.ZipFile(feed_file) as zip_file:
        routes = read_routes(zip_file)
        generate_routes(dest_dir=dest_dir, routes=routes)

        trips = read_trips(zip_file)
        generate_trips(dest_dir=dest_dir, trips=trips, route_id=routes.id)

        stops = read_stops(zip_file)
        tiles = generate_tiled_stops(
            dest_dir=dest_dir, stops=stops, max_stops=args.max_stops)

        stop_times = read_stop_times(zip_file)
        generate_tiled_stop_times(
            dest_dir=dest_dir, stop_times=stop_times, trip_id=trips.id,
            stops_id=stops.id, tiles=tiles)


def generate_routes(dest_dir, routes):
    store_column(routes.name, dest_dir, 'routes', 'name')


def generate_trips(dest_dir, trips, route_id):
    trip_route_id = numpy.searchsorted(route_id, trips.route_id)
    store_column(trip_route_id, dest_dir, 'trips', 'route_id', int)
    store_column(trips.name, dest_dir, 'trips', 'name')


def generate_tiled_stops(dest_dir, stops, max_stops=None):
    return tuple(_generate_tiled_stops(dest_dir, stops, max_stops))

def _generate_tiled_stops(dest_dir, stops, max_stops):

    if not max_stops:
        max_stops = len(stops.id)
    max_stops = max(max_stops, 4)

    tree = kdtree_from_table(
        stops, pivot_keys=['lon', 'lat'], max_rows=max_stops)
    for i, tile in enumerate(iter_kdtree(tree)):
        store_column(
            tile.name, dest_dir, 'stops', 'name' + str(i))
        store_column(
            tile.lon, dest_dir, 'stops', 'lon' + str(i), float)
        store_column(
            tile.lat, dest_dir, 'stops', 'lat' + str(i), float)
        yield tile

    # TODO: KDTree here !!!


def generate_tiled_stop_times(
        dest_dir, stop_times, trip_id, stops_id, tiles):

    stop_times_stop_id = numpy.searchsorted(stops_id, stop_times.stop_id)
    stop_tile_id = numpy.ones(dtype=int, shape=stop_times_stop_id.shape)
    for i, tile in enumerate(tiles):
        stop_tile_id[tile.indexes] = i

    stop_times_tile_id = stop_tile_id[stop_times_stop_id]
    stop_times = stop_times.sort_by_array(
        stop_times_tile_id, sort_index_array=True)

    tile_id = numpy.arange(len(tiles))
    stop_times_tile_start = numpy.searchsorted(
        stop_times_tile_id, tile_id, side='left')
    stop_times_tile_stop = numpy.searchsorted(
        stop_times_tile_id, tile_id, side='right')

    stop_times_trip_id = numpy.searchsorted(trip_id, stop_times.trip_id)
    for i in tile_id:
        tile_slice = slice(stop_times_tile_start[i], stop_times_tile_stop[i])
        store_column(
            stop_times_stop_id[tile_slice], dest_dir, 'stop_times',
            'stop_id' + str(i))
        store_column(
            stop_times_trip_id[tile_slice], dest_dir, 'stop_times',
            'trip_id' + str(i))
        store_column(
            stop_times.departure_minutes[tile_slice], dest_dir, 'stop_times',
            'departure_minutes' + str(i))


def timestamp_to_minutes(timestamp):
    timestamp = numpy.asarray(timestamp, dtype='S8')
    timestamp = numpy.core.defchararray.rjust(timestamp, 8, '0')

    hours = ArrayView(
        data=timestamp.__array_interface__['data'],
        shape=timestamp.shape, typestr='S2', strides=(8,))
    hours = numpy.array(hours).astype(int) % 24

    minutes = ArrayView(
        data=timestamp.__array_interface__['data'],
        shape=timestamp.shape, typestr='S2', strides=(8,), offset=3)
    minutes = numpy.array(minutes).astype(int) % 60

    timestamp = (hours * 60) + minutes
    assert timestamp.max() <  24 * 60
    return timestamp


class ArrayView(object):

    def __init__(self, data, shape, typestr, strides, offset=0):
        if offset:
            data = data[0] + offset, data[1]
        self.__array_interface__ = {
            'shape': shape, 'typestr': typestr, 'data': data,
            'strides': strides, 'version': 3, 'offset': offset}


def named_tuple(*fields):

    def decorator(cls):
        _named_tuple_type = collections.namedtuple(cls.__name__, fields)
        return type(cls.__name__, (cls, _named_tuple_type), {})

    return decorator


class BaseTable(tuple):

    def sort_by(self, index_name):
        # sort all columns by given index
        return self.sort_by_array(getattr(self, index_name))

    def sort_by_array(self, index_array, sort_index_array=False, sorter=None):
        # sort all columns by given index
        if sorter is None:
            sorter = numpy.argsort(index_array)
        sorted_columns = [
            column[sorter] for column in self if column is not None]
        if sort_index_array:
            index_array[:] = index_array[sorter]
        return type(self)(*sorted_columns)


@named_tuple('left', 'right', 'pivot_key', 'pivot_value')
class KDTree(object):

    _is_kdtree = True

    @classmethod
    def from_table(cls, table, pivot_keys, max_rows=128, level=0):
        table_class = type(table)
        ndim = len(pivot_keys)
        pivot_key = pivot_keys[level % ndim]
        pivot_column = getattr(table, pivot_key)
        if len(pivot_column) <= max_rows:
            return table

        else:
            table = table.sort_by(pivot_key)
            half = int(len(table.id) / 2)
            pivot_value = [half]
            left = cls.from_table(
                table=table_class(*[column[:half] for column in table]),
                pivot_keys=pivot_keys,
                max_rows=max_rows,
                level=level + 1)

            right = cls.from_table(
                table=table_class(*[column[half:] for column in table]),
                pivot_keys=pivot_keys,
                max_rows=max_rows,
                level=level + 1)

            return KDTree(left, right, pivot_key, pivot_value)

    @staticmethod
    def iter_tree(obj):
        stack = [obj]
        while stack:
            obj = stack.pop()
            if(getattr(obj, '_is_kdtree', False)):
                stack.append(obj.left)
                stack.append(obj.right)

            else:
                yield obj


kdtree_from_table = KDTree.from_table
iter_kdtree = KDTree.iter_tree


@named_tuple('id', 'name')
class RouteTable(BaseTable):

    @classmethod
    def from_zip_file(cls, zip_file):
        columns = read_table(
            zip_file=zip_file, table_name='routes',
            columns=['route_id', 'route_short_name'])
        return cls(*columns).sort_by('id')


read_routes = RouteTable.from_zip_file


@named_tuple('id', 'route_id', 'name')
class TripTable(BaseTable):

    @classmethod
    def from_zip_file(cls, zip_file):
        columns = read_table(
            zip_file=zip_file, table_name='trips',
            columns=['trip_id', 'route_id', 'trip_headsign'])
        return cls(*columns).sort_by('id')


read_trips = TripTable.from_zip_file


@named_tuple('lon', 'lat', 'id', 'name', 'indexes')
class StopTable(BaseTable):

    split_axis = 'lon'

    @classmethod
    def from_zip_file(cls, zip_file):
        columns = read_table(
            zip_file=zip_file, table_name='stops',
            columns=['stop_lon', 'stop_lat', 'stop_id', 'stop_name'],
            dtypes={'stop_lon': float, 'stop_lat': float})
        columns += (numpy.arange(len(columns[0])),)
        return cls(*columns).sort_by('id')


read_stops = StopTable.from_zip_file


@named_tuple('stop_id', 'trip_id', 'departure_minutes')
class StopTimeTable(BaseTable):

    @classmethod
    def from_zip_file(cls, zip_file):
        stop_id, trip_id, departure_time = read_table(
            zip_file=zip_file, table_name='stop_times',
            columns=['stop_id', 'trip_id', 'departure_time'])
        return cls(
            stop_id=stop_id, trip_id=trip_id,
            departure_minutes=timestamp_to_minutes(departure_time))


read_stop_times = StopTimeTable.from_zip_file


def read_table(zip_file, table_name, columns, dtypes=None):
    if not dtypes:
        dtypes = {}

    with zip_file.open(table_name + '.txt', 'r') as csv_stream:
        hearer = csv_stream.readline().strip()

        names = [
            remove_non_ascii(
                name.strip().replace('"', '').replace("'", ''))
            for name in hearer.split(',')]

        table = pandas.read_csv(
            csv_stream, names=names, quotechar='"', quoting=csv.QUOTE_ALL,
            usecols=columns)
        table = [
            numpy.asarray(remove_nans(table[column]), dtype=dtypes.get(column))
            for column in columns]
        return table


def remove_nans(series):
    if series.dtype == object:
        series = series.fillna('')
    return series


def store_column(array, dest_dir, table, column, dtype=None):
    if dtype:
        array = array.astype(dtype)
    packed = msgpack.packb(list(array))
    zipped = zlib.compress(packed, 9)
    dest_file = os.path.join(dest_dir, table) + "." + column + '.gz'
    with open(dest_file, 'wb') as dest_stream:
        dest_stream.write(zipped)
    LOG.info('Column stored:\n'
             '    path: %r\n'
             '    dtype: %s\n'
             '    array size: %d\n'
             '    packet size: %d bytes\n'
             '    zipped size: %d bytes.\n',
             dest_file, array.dtype, array.size, len(packed), len(zipped))


def read_yaml_file(feed_file):
    with open(feed_file, 'rt') as feed_file_stream:
        return yaml.load(feed_file_stream.read())


def remove_non_ascii(text):
    return ''.join(i for i in text if ord(i)<128)


if __name__ == "__main__":
    # This prevents accidental writing to sys.stdout
    sys.stdout = sys.stderr
    main()
