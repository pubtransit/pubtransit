'''
Created on 11 Oct 2016

@author: Federico Ressi
'''

# pylint: disable=missing-docstring

import argparse
import collections
import csv
import json
import logging
import os
import re
import shutil
import sys
import zipfile
import zlib

import jinja2
import msgpack
import numpy
import pandas
import yaml

import pubtransit

LOG = logging.getLogger(__name__)

OUT_STREAM = sys.stdout

TEMPLATE_MANAGER = jinja2.Environment(
    loader=jinja2.PackageLoader(pubtransit.__name__, ''))

TARGET_METHODS = {}

DEFAULT_STOPS_PER_TILE = 128


def main():
    logging.basicConfig(
        level=logging.WARNING, format="%(asctime)-15s | %(message)s")

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
        'files', type=str, default=['site.yml'], nargs='*',
        help='Feed file to extract feed rules from.')

    parser.add_argument(
        '--dest', type=str, help='Destination feed file.')

    args = parser.parse_args()

    if args.logging_level:
        # Raise logging level
        logging.getLogger().setLevel(args.logging_level)

    method = TARGET_METHODS[args.target[0]]

    try:
        for inpute_file in args.files or [None]:
            method(args, inpute_file)

    except Exception as error:  # pylint: disable=broad-except
        if args.logging_level is logging.DEBUG:
            LOG.fatal("Unhandled exception.", exc_info=1)
        else:
            LOG.fatal(str(error) or str(type(error)))
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


@target_method("version")
def print_version(args):
    # pylint: disable=unused-argument
    OUT_STREAM.write(pubtransit.__version__ + '\n')


@target_method("makefile")
def make_makefiles(args, site_file=None):
    feeds_conf = read_yaml_file(site_file or 'site.yml')
    for site in feeds_conf['feed']:
        for feed in site["feeds"]:
            target_path = os.path.join(
                args.build_dir, site["name"], feed["name"])

            if not os.path.isdir(target_path):
                os.makedirs(target_path)

            url = feed.get("url") or (site["url"] + '/' + feed["path"])

            # pylint: disable=unused-argument,no-member
            OUT_STREAM.write(target_path + ".mk ")
            target_template = TEMPLATE_MANAGER.get_template("feed_item.mk")
            target_make = target_template.render(
                install_dir=os.path.join('$(INSTALL_DIR)', 'feed'),
                build_dir=args.build_dir,
                target=os.path.join(site["name"], feed["name"]),
                url=url,
                make_flags="--logging-level " + str(args.logging_level),
                make_me='python -m pubtransit ' + ' '.join(
                    repr(arg) for arg in sys.argv[1:]),
                script_name="pubtransit")
            with open(target_path + ".mk", 'wt') as target_stream:
                target_stream.write(target_make)


@target_method("datastore")
def generate_datastores(args, feed_file):
    dest_dir = os.path.splitext(args.dest or args.source)[0]
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)

    with zipfile.ZipFile(feed_file) as zip_file:
        routes = read_routes(zip_file)
        generate_routes(dest_dir=dest_dir, routes=routes)

        trips = read_trips(zip_file)
        generate_trips(dest_dir=dest_dir, trips=trips, route_id=routes.id)

        stops = read_stops(zip_file)
        tiles = generate_tiled_stops(
            dest_dir=dest_dir, stops=stops, max_rows=args.max_stops)

        stop_times = read_stop_times(zip_file)
        generate_tiled_stop_times(
            dest_dir=dest_dir, stop_times=stop_times, trip_id=trips.id,
            tiles=tiles)

    feed_info = dict(
        west=stops.west, east=stops.east, south=stops.south, north=stops.north)
    store_object(feed_info, dest_dir, 'feed')


@target_method("index")
def make_index(args, feed_file=None):
    feeds_conf = read_yaml_file(feed_file or 'feeds.yaml')
    paths = []
    west = []
    east = []
    south = []
    north = []
    for site in feeds_conf['feed']:
        for feed in site["feeds"]:
            target_path = os.path.join(
                args.build_dir, site["name"], feed["name"])

            if not os.path.isdir(target_path):
                LOG.error('Target feed dir not found: %r', target_path)
                os.makedirs(target_path)

            with open(os.path.join(target_path, 'feed.gz')) as in_stream:
                zipped = in_stream.read()
                packed = zlib.decompress(zipped)
                feed_info = msgpack.unpackb(packed)

            paths.append(os.path.join(site["name"], feed["name"]))
            west.append(feed_info['west'])
            east.append(feed_info['east'])
            south.append(feed_info['south'])
            north.append(feed_info['north'])

    store_column(paths, args.build_dir, 'index', 'path')
    store_column(west, args.build_dir, 'index', 'west', float)
    store_column(east, args.build_dir, 'index', 'east', float)
    store_column(south, args.build_dir, 'index', 'south', float)
    store_column(north, args.build_dir, 'index', 'north', float)


def generate_routes(dest_dir, routes):
    store_column(routes.name, dest_dir, 'routes', 'name')


def generate_trips(dest_dir, trips, route_id):
    trip_route_id = numpy.searchsorted(route_id, trips.route_id)
    store_column(trip_route_id, dest_dir, 'trips', 'route_id', int)
    store_column(trips.name, dest_dir, 'trips', 'name')


def generate_tiled_stops(dest_dir, stops, max_rows=None):
    if not max_rows:
        max_rows = len(stops.id)
    max_rows = max(max_rows, 4)

    tiles_tree, tiles = create_tree(
        stops, index_columns=['lon', 'lat'], max_rows=max_rows)

    tiles_num = len(tiles)
    tiles_shape = tiles_num,
    tiles_id_format = '0' + str(len(str(tiles_num)))
    tiles_west = numpy.zeros(tiles_shape, dtype=float)
    tiles_east = numpy.zeros(tiles_shape, dtype=float)
    tiles_south = numpy.zeros(tiles_shape, dtype=float)
    tiles_north = numpy.zeros(tiles_shape, dtype=float)
    for i, tile in enumerate(tiles):
        tile_dir = os.path.join(dest_dir, format(i, tiles_id_format))
        store_column(tile.name, tile_dir, 'stops', 'name')
        store_column(tile.lon, tile_dir, 'stops', 'lon', float)
        store_column(tile.lat, tile_dir, 'stops', 'lat', float)
        tiles_west[i] = tile.west
        tiles_east[i] = tile.east
        tiles_south[i] = tile.south
        tiles_north[i] = tile.north

    store_object(tiles_tree, os.path.join(dest_dir, 'tiles'), 'tree')
    store_column(tiles_west, dest_dir, 'tiles', 'west')
    store_column(tiles_east, dest_dir, 'tiles', 'east')
    store_column(tiles_south, dest_dir, 'tiles', 'south')
    store_column(tiles_north, dest_dir, 'tiles', 'north')
    return tiles


def generate_tiled_stop_times(dest_dir, stop_times, trip_id, tiles):
    # pylint: disable=too-many-locals
    tiles_num = len(tiles)
    tiles_id_format = '0' + str(len(str(tiles_num)))

    stop_times = stop_times.sort_by('stop_id')
    trip_id_sorter = numpy.argsort(trip_id)

    for tile_id, stops in enumerate(tiles):
        stop_id = stops.id
        stop_id_sorter = numpy.argsort(stop_id)

        tile_start = numpy.searchsorted(
            stop_id, stop_times.stop_id, side='left', sorter=stop_id_sorter)
        tile_stop = numpy.searchsorted(
            stop_id, stop_times.stop_id, side='right', sorter=stop_id_sorter)
        tiled_stop_times = stop_times.select(tile_start != tile_stop)

        tiled_stop_times_stop_id = stop_id_sorter[numpy.searchsorted(
            stop_id, tiled_stop_times.stop_id, sorter=stop_id_sorter)]

        tiled_stop_times_tile_id = trip_id_sorter[numpy.searchsorted(
            trip_id, tiled_stop_times.trip_id,
            sorter=trip_id_sorter)]

        tile_dir = os.path.join(dest_dir, format(tile_id, tiles_id_format))

        tile_dir = os.path.join(dest_dir, format(tile_id, tiles_id_format))
        store_column(
            tiled_stop_times_stop_id, tile_dir, 'stop_times', 'stop_id')
        store_column(
            tiled_stop_times_tile_id, tile_dir, 'stop_times', 'trip_id')
        store_column(
            tiled_stop_times.departure_minutes, tile_dir, 'stop_times',
            'departure_minutes')

        stop_empty = numpy.ones_like(stop_id, dtype=int)
        stop_empty[tiled_stop_times_stop_id] = 0
        store_column(stop_empty, tile_dir, 'stops', 'empty')


def timestamp_to_minutes(timestamp):
    timestamp = numpy.asarray(timestamp, dtype='S8')
    timestamp = numpy.core.defchararray.rjust(timestamp, 8, '0')

    hours = array_from_data(  # pylint: disable=no-member
        data=timestamp.__array_interface__['data'],
        shape=timestamp.shape, typestr='S2', strides=(8,)
        ).astype(int) % 24

    minutes = array_from_data(  # pylint: disable=no-member
        data=timestamp.__array_interface__['data'],
        shape=timestamp.shape, typestr='S2', strides=(8,),
        offset=3).astype(int) % 60

    timestamp = (hours * 60) + minutes
    assert timestamp.max() < 24 * 60
    return timestamp


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
        if sort_index_array:
            index_array[:] = index_array[sorter]
        return self.select(sorter)

    def select(self, item):
        values = [
            column[item] for column in self if column is not None]
        return type(self)(*values)


def create_tree(table, index_columns, max_rows=128):
    # pylint: disable=too-many-locals
    table_class = type(table)
    ndim = len(index_columns)
    tree = {}
    stack = [(tree, table, 0)]
    leaves = []

    while stack:
        node, table, level = stack.pop()
        column_id = index_columns[level % ndim]
        column = getattr(table, column_id)
        if len(column) <= max_rows:
            node['leaf'] = len(leaves)
            leaves.append(table)

        else:
            table = table.sort_by(column_id)
            column = getattr(table, column_id)  # this is another table!!
            mid = int(len(column) / 2)
            node['col'] = column_id
            node['min'] = column[0]
            node['mid'] = column[mid]
            node['max'] = column[-1]
            node['left'] = {}
            node['right'] = {}
            assert node['min'] <= node['max']
            assert node['min'] <= node['mid']
            assert node['mid'] <= node['max']

            left = table_class(*[col[:mid] for col in table])
            right = table_class(*[col[mid:] for col in table])
            stack.append((node['right'], right, level + 1))
            stack.append((node['left'], left, level + 1))

    LOG.debug('Tree generated:\n%s',
              json.dumps(tree, indent=4, sort_keys=True))
    return tree, leaves


@named_tuple('id', 'name')
class RouteTable(BaseTable):

    @classmethod
    def from_zip_file(cls, zip_file):
        columns = read_table(
            zip_file=zip_file, table_name='routes',
            columns=['route_id', 'route_short_name'])
        return cls(*columns).sort_by('id')


read_routes = RouteTable.from_zip_file  # pylint: disable=invalid-name


@named_tuple('id', 'route_id', 'name')
class TripTable(BaseTable):

    @classmethod
    def from_zip_file(cls, zip_file):
        columns = read_table(
            zip_file=zip_file, table_name='trips',
            columns=['trip_id', 'route_id', 'trip_headsign'])
        return cls(*columns).sort_by('id')


read_trips = TripTable.from_zip_file  # pylint: disable=invalid-name


@named_tuple('lon', 'lat', 'id', 'name', 'indexes')
class StopTable(BaseTable):
    # pylint: disable=no-member

    @classmethod
    def from_zip_file(cls, zip_file):
        columns = read_table(
            zip_file=zip_file, table_name='stops',
            columns=['stop_lon', 'stop_lat', 'stop_id', 'stop_name'],
            dtypes={'stop_lon': float, 'stop_lat': float})
        columns += (numpy.arange(len(columns[0])),)
        return cls(*columns).sort_by('id')

    _west = None

    @property
    def west(self):
        west = self._west
        if west is None:
            self._west = west = numpy.amin(self.lon)
        return west

    _east = None

    @property
    def east(self):
        east = self._east
        if east is None:
            self._east = east = numpy.amax(self.lon)
        return east

    _south = None

    @property
    def south(self):
        south = self._south
        if south is None:
            self._south = south = numpy.amin(self.lat)
        return south

    _north = None

    @property
    def north(self):
        north = self._north
        if north is None:
            self._north = north = numpy.amax(self.lat)
        return north


read_stops = StopTable.from_zip_file  # pylint: disable=invalid-name


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

    _left = None


read_stop_times = StopTimeTable.from_zip_file  # pylint: disable=invalid-name

GET_COLUMN_NAME_REGEX = re.compile(b'[^\\w]')


def read_table(zip_file, table_name, columns, dtypes=None):
    if not dtypes:
        dtypes = {}

    with zip_file.open(table_name + '.txt', 'r') as csv_stream:
        hearer = csv_stream.readline().strip()

        names = [
            GET_COLUMN_NAME_REGEX.sub(b'', name).decode('ascii')
            for name in hearer.split(b',')]

        table = pandas.read_csv(
            csv_stream, names=names, quotechar='"', quoting=csv.QUOTE_ALL,
            usecols=[col for col in columns])
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
        array = numpy.asarray(array, dtype=dtype)

    if isinstance(array, list):
        obj = array
    else:
        obj = list(array)
    store_object(obj, os.path.join(dest_dir, table), column)


def store_object(obj, dest_dir, name):
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
    packed = msgpack.packb(obj)
    zipped = zlib.compress(packed, 9)
    dest_file = os.path.join(dest_dir, name + '.gz')
    with open(dest_file, 'wb') as dest_stream:
        dest_stream.write(zipped)
    LOG.info('Object stored:\n'
             '    path: %r\n'
             '    packet size: %d bytes\n'
             '    zipped size: %d bytes.\n',
             dest_file, len(packed), len(zipped))


def read_yaml_file(feed_file):
    with open(feed_file, 'rt') as feed_file_stream:
        return yaml.load(feed_file_stream.read())


def array_from_data(data, shape, typestr, strides, offset=0):
    if offset:
        data = data[0] + offset, data[1],

    # pylint: disable=no-member
    return numpy.array(ArrayInterface(
        shape=shape, typestr=typestr, data=data, strides=strides))


@named_tuple('shape', 'typestr', 'data', 'strides')
class ArrayInterface(object):
    # pylint: disable=too-few-public-methods,no-member

    @property
    def __array_interface__(self):
        return {
            'shape': self.shape,
            'typestr': self.typestr,
            'data': self.data,
            'strides': self.strides,
            'version': 3}
