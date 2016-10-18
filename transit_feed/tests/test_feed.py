'''
Created on 13 Oct 2016

@author: fressi
'''

import json
import logging
import os
import sys
import tempfile
import unittest
import zipfile
import zlib

import msgpack
import numpy
import shutil
from six.moves import urllib  # pylint: disable=import-error


from transit_feed.feed import (
    generate_tiled_stops, generate_tiled_stop_times, generate_routes,
    generate_trips, read_stops, read_stop_times, read_routes, read_trips)


SAMPLE_FEED_DIR = os.path.join(os.path.dirname(__file__), 'sample-feed')

LOG = logging.getLogger(__name__)


class TestMake(unittest.TestCase):

    def test_genetarte_routes(self):
        # given
        zip_file = self.open_feed_file(SAMPLE_FEED_DIR)
        dest_dir = self.make_temp_dir()
        routes = read_routes(zip_file)

        # when
        generate_routes(dest_dir, routes)

        # then
        self.assert_array_equal(
            routes.name,
            self.read_column(dest_dir, 'routes.name.gz'))

    def test_genetarte_trips(self):
        # given
        zip_file = self.open_feed_file(SAMPLE_FEED_DIR)
        dest_dir = self.make_temp_dir()
        routes = read_routes(zip_file)
        trips = read_trips(zip_file)

        # when
        generate_trips(dest_dir=dest_dir, trips=trips, route_id=routes.id)

        # then
        self.assert_array_equal(
            trips.name,
            self.read_column(dest_dir, 'trips.name.gz', dtype=object))

        self.assert_array_equal(
            trips.route_id,
            routes.id[self.read_column(dest_dir, 'trips.route_id.gz')])

    def test_generate_stops(self):
        # given
        zip_file = self.open_feed_file(SAMPLE_FEED_DIR)
        dest_dir = self.make_temp_dir()
        stops = read_stops(zip_file)

        # when
        tiles = list(generate_tiled_stops(dest_dir=dest_dir, stops=stops))

        # then
        self.assert_array_equal([stops.id], [tile.id for tile in tiles])
        self.assertEqual(
            [(dest_dir, [],
              ['stops.lat0.gz', 'stops.lon0.gz', 'stops.name0.gz'])],
            list(os.walk(dest_dir)))
        self.assert_array_almost_equal(
            stops.lon, self.read_column(dest_dir, 'stops.lon0.gz'))
        self.assert_array_almost_equal(
            stops.lat, self.read_column(dest_dir, 'stops.lat0.gz'))
        self.assert_array_equal(
            stops.name, self.read_column(dest_dir, 'stops.name0.gz'))

    def test_generate_tiled_stops(self):
        # given
        zip_file = self.open_feed_file(
            "http://www.transportforireland.ie/transitData/"
            "google_transit_buseireann.zip")
        dest_dir = self.make_temp_dir()
        stops = read_stops(zip_file)

        # when
        tiles = list(generate_tiled_stops(dest_dir=dest_dir, stops=stops))

        # then
        try:
            row_numbers = numpy.arange(len(stops.id))

            # all stops has been assigned to one and only one tile
            assigned_stops = 0
            missing = numpy.ones(shape=stops.id.shape, dtype=bool)
            order = numpy.argsort(stops.id)
            for tile in tiles:
                indexes = numpy.searchsorted(stops.id, tile.id, sorter=order)
                missing[indexes] = False
                self.assert_array_almost_equal(stops.lon[indexes], tile.lon)
                self.assert_array_almost_equal(stops.lat[indexes], tile.lat)
                self.assert_array_equal(stops.name[indexes], tile.name)
                self.assert_array_equal(stops.id[indexes], tile.id)
                self.assert_array_equal(row_numbers[indexes], tile.indexes)
                assigned_stops += tile.lon.size
            missing, = missing.nonzero()
            self.assert_array_equal(numpy.asarray([], dtype=int), missing)
            self.assertEqual(assigned_stops, len(stops.id))

            # tile size and tile intersection areas are acceptable
            sizes = numpy.asarray([tile.lon.size for tile in tiles], dtype=int)
            self.assertTrue(sizes.min() > (sizes.max() / 2))

        except AssertionError:
            self.clear_plot()
            self.plot_dots(stops.lon, stops.lat)
            for i in range(len(tiles)):
                self.plot_dots(
                    self.read_column(dest_dir, 'stops.lon' + str(i) + '.gz'),
                    self.read_column(dest_dir, 'stops.lat' + str(i) + '.gz'))
            self.show_plot()
            raise

    def test_generate_stop_times(self):
        # given
        zip_file = self.open_feed_file(SAMPLE_FEED_DIR)
        dest_dir = self.make_temp_dir()
        trips = read_trips(zip_file)
        stops = read_stops(zip_file)
        stop_times = read_stop_times(zip_file)

        # when
        tiles = list(generate_tiled_stops(dest_dir=dest_dir, stops=stops))

        generate_tiled_stop_times(
            dest_dir=dest_dir, stop_times=stop_times, trip_id=trips.id,
            stops_id=stops.id, tiles=tiles)

    def read_column(self, table_dir, name, dtype=None):
        with open(os.path.join(table_dir, name), 'r') as column_file:
            packed = zlib.decompress(column_file.read())
            return numpy.asarray(msgpack.loads(packed), dtype=dtype)

    def make_temp_file(self, suffix=""):
        fd, path = tempfile.mkstemp(suffix=suffix)
        self.addCleanup(os.remove, path)
        os.close(fd)
        return path

    def make_temp_dir(self):
        path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, path)
        return path

    def get_feed_file(self, feed_dir):
        zip_path = self.make_temp_file('.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(feed_dir):
                for file_name in files:
                    if not file_name.startswith('.'):
                        zip_file.write(
                            filename=os.path.join(root, file_name),
                            arcname=file_name)
        return zip_path

    def open_feed_file(self, feed=None):
        if os.path.isdir(feed):
            file_name = self.get_feed_file(feed)
        elif not os.path.isfile(feed):
            feed_url = feed
            file_name = get_cache_file(feed.replace('://', '_'))
            try:
                retrieve_file(feed_url=feed_url, file_name=file_name)
            except urllib.error.URLError as err:
                self.skipTest(str(err))

        zip_file = zipfile.ZipFile(file_name)
        self.addCleanup(zip_file.close)
        return zip_file

    def assert_array_equal(self, expected, actual):
        numpy.testing.assert_equal(actual, expected)

    def assert_array_almost_equal(self, expected, actual, *args, **kwargs):
        numpy.testing.assert_almost_equal(actual, expected, *args, **kwargs)

    _PLOT_COLORS = {
        'b': 'blue',
        'g': 'green',
        'r': 'red',
        'c': 'cyan',
        'm': 'magenta',
        'y': 'yellow',
        'k': 'black',
        'w': 'white'
    }

    PLOT_COLORS = list(_PLOT_COLORS.keys())

    _peek_color = iter([])

    def peek_color(self):
        try:
            return next(self._peek_color)
        except StopIteration:
            self._peek_color = iter(self.PLOT_COLORS)
            return next(self._peek_color)

    def clear_plot(self):
        import matplotlib.pyplot
        matplotlib.pyplot.clf()
        matplotlib.pyplot.close()

    def plot_dots(self, x, y):
        import matplotlib.pyplot
        matplotlib.pyplot.plot(x, y, self.peek_color() + 'o')

    def show_plot(self):
        import matplotlib.pyplot
        matplotlib.pyplot.savefig(
            self.id() + '.png', bbox_inches='tight')
        self.clear_plot()


def get_cache_file(name):
    parts = os.path.split(name)
    chache_file = os.path.join('.', '.cache', *parts)
    cache_dir = os.path.dirname(chache_file)
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)
    return chache_file


def retrieve_file(feed_url, file_name):
    try:
        origin = urllib.request.urlopen(feed_url, timeout=5)
    except urllib.error.URLError:
        if os.path.isfile(file_name):
            return False
        else:
            raise

    destination = None
    try:
        _retrieve_file(origin, feed_url, file_name)

    except BaseException:
        try:
            os.remove(file_name)
        except Exception:  # pylint: disable=broad-except
            LOG.warning('Unable to delete file: %r', file_name)
        raise

    finally:
        origin.close()
        if destination:
            destination.close()

    return True


def _retrieve_file(origin, feed_url, file_name):
    actual_meta = parse_meta(str(origin.info()))
    expected_size = int(actual_meta["content-length"])

    meta_file = file_name + '.meta'
    if os.path.isfile(file_name) and os.path.isfile(meta_file):
        try:
            with open(meta_file, "rt") as meta_stream:
                expected_meta = json.load(meta_stream)
                for key in ["content-length", "content-type",
                            "last-modified", "server"]:
                    if actual_meta.get(key) != expected_meta.get(key):
                        break
                else:
                    statinfo = os.stat(file_name)
                    if statinfo.st_size == expected_size:
                        return False
        except Exception:  # pylint: disable=broad-except
            LOG.exception("Error comparing meta file: %r", meta_file)

        os.remove(meta_file)

    destination = open(file_name, 'wb')

    chunk_size = 64 * 1024
    actual_size = 0
    print_progress = expected_size > chunk_size
    if print_progress:
        expected_progress = 20
        actual_progress = 0
        message = "Downloading '{feed_url}' ({size} bytes) ...".format(
            feed_url=feed_url,
            size=expected_size)
        sys.stderr.write(message)

    while True:
        data = origin.read(chunk_size)
        if not data:
            break

        destination.write(data)
        actual_size += len(data)
        if print_progress:
            progress = actual_size * expected_progress / expected_size
            sys.stderr.write('.' * (progress - actual_progress))
            actual_progress = progress

    sys.stderr.write(" DONE\n")
    if actual_size < expected_size:
        LOG.warning(
            "After downloading %r I expected to have %d bytes but "
            "I got %d.", file_name, expected_size, actual_size)

    with open(meta_file, "wt") as meta_stream:
        json.dump(actual_meta, meta_stream, indent=4, sort_keys=True)


def parse_meta(meta_string):
    meta = {}
    for line in meta_string.split('\n'):
        line = line.strip()
        if line:
            parts = line.split(':', 1)
            meta[parts[0].strip().lower()] = parts[1:][0] if parts[1:] else ""
    return meta


if __name__ == "__main__":
    unittest.main()
