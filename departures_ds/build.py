'''
Created on 10 Oct 2016

@author: fressi
'''

import argparse
import csv
import json
import logging
import os
import sys

import numpy
import pandas
import shutil
import urllib
import urllib2
import yaml
import zipfile



from departures_ds.data import (
    DataStore, stop_arrays, route_arrays, trip_arrays, stop_time_arrays)


LOG = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)-15s | %(message)s")

    parser = argparse.ArgumentParser(
        description='Build departures data store from given feeds.')
    parser.add_argument('feed_files', metavar='feeds', type=str, nargs='+',
                        help='Feed files.')
    parser.add_argument('-C', dest='dest_dir', default=os.getcwd(),
                        help='Output directory')
    args = parser.parse_args()
    feeds_dir = os.path.join(args.dest_dir, "feeds")
    if not os.path.isdir(feeds_dir):
        os.makedirs(feeds_dir)

    data_store = DataStore()
    for feed_file in args.feed_files:
        for site in yaml.load(urllib.urlopen(feed_file).read()):
            for end_point in site["end_points"]:
                try:
                    import_feed(
                        data_store=data_store,
                        feed_url=site["site"] + '/' + end_point['path'],
                        feeds_dir=feeds_dir, feed_name=end_point['name'])
                except zipfile.BadZipfile:
                    LOG.exception('Unable to import feed: ')

    tiles_dir = os.path.join(feeds_dir, "tiles")
    if os.path.isdir(tiles_dir):
        shutil.rmtree(tiles_dir)
    os.makedirs(tiles_dir)

    for i, j, tile in data_store.pack_tiles():
        file_name = os.path.join(tiles_dir, "{}.{}.gz".format(i, j))
        with open(file_name, 'wb') as out_stream:
            out_stream.write(tile)


def generate_feed_names():
    i = 1
    while True:
        yield "feed_" + str(i)
        i += 1


def import_feed(data_store, feed_url, feeds_dir, feed_name):
    feed_file = os.path.normpath(os.path.join(feeds_dir, feed_name) + '.zip')
    feed_dir = os.path.join(feeds_dir, feed_name)
    LOG.info("Get feed file:\n"
             "    source: %r\n"
             "    destination: %r", feed_url,  os.path.relpath(feed_file))

    if retrieve_file(feed_url, file_name=feed_file):
        if os.path.isdir(feed_dir):
            shutil.rmtree(feed_dir)
    if not os.path.isdir(feed_dir):
        os.makedirs(feed_dir)

    if not os.path.isfile(feed_file):
        raise RuntimeError('Problems downloading feed: ' + feed_url)

    LOG.debug("Feed retrieved: %r", feed_file)
    with zipfile.ZipFile(feed_file) as zip_file:

        stops = read_csv(
            zip_file=zip_file, feed_dir=feed_dir, file_name='stops.txt')
        routes = read_csv(
            zip_file=zip_file, feed_dir=feed_dir, file_name='routes.txt')
        trips = read_csv(
            zip_file=zip_file, feed_dir=feed_dir, file_name='trips.txt')
        stop_times = read_csv(
            zip_file=zip_file, feed_dir=feed_dir, file_name='stop_times.txt')

        return data_store.put_feed(
            name=feed_name, url=feed_url,
            stops=stop_arrays(
                stop_id=stops['stop_id'], name=stops['stop_name'],
                lon=stops['stop_lon'], lat=stops['stop_lat']),
            routes=route_arrays(
                route_id=routes['route_id'], name=routes['route_short_name']),
            trips=trip_arrays(
                trip_id=trips['trip_id'], route_id=trips['route_id'],
                name=trips['trip_headsign']),
            stop_times=stop_time_arrays(
                trip_id=stop_times['trip_id'], stop_id=stop_times['stop_id'],
                departure_time=stop_times['departure_time']))


def read_csv(zip_file, feed_dir, file_name):
    stops_file = os.path.join(feed_dir, file_name)
    zip_file.extract(file_name, feed_dir)

    with open(stops_file, 'rt') as csv_stream:
        hearer = csv_stream.readline().strip()
    names = [
        remove_non_ascii(
            name.strip().replace('"', '').replace("'", ''))
        for name in hearer.split(',')]

    return pandas.read_csv(
        stops_file, names=names, quotechar='"', quoting=csv.QUOTE_ALL,
        header=0)


def retrieve_file(feed_url, file_name):
    origin = urllib2.urlopen(feed_url)
    destination = None
    try:
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
            message = "Downloading '{file_name}' ({size} bytes) ...".format(
                file_name=os.path.relpath(file_name),
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

    finally:
        origin.close()
        if destination:
            destination.close()

    return True

def parse_meta(meta_string):
    meta = {}
    for line in meta_string.split('\n'):
        line = line.strip()
        if line:
            parts = line.split(':', 1)
            meta[parts[0].strip().lower()] = parts[1:][0] if parts[1:] else ""
    return meta


def remove_non_ascii(text):
    return ''.join(i for i in text if ord(i)<128)


def remove_quotes(obj):
    data_array = numpy.asarray(obj)
    if data_array.dtype == object and data_array[0].startswith("'"):
        data_array = numpy.asarray(
            [s[1:-1] for s in data_array],
            dtype=object)
    return data_array


if __name__ == '__main__':
    main()