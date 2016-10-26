# System Architecture Design

## Data Flow Overview

<img src="https://cdn.rawgit.com/pubtransit/transit/b6e69741bd31762391f199eada34daa1d36fafae/doc/data-flow.svg" width="40%" align="left">

The System Architecture is very simple: the Web page is static and doesn't
rely on any running appliance. This approach was decided to maximize the site
scalability and simplicity. There is no dynamic data.

The public transit data (downloaded as
[GPRS files](https://developers.google.com/transit/gtfs/) .zip files) is
instead split in small compressed binary .gz files (called here feed files)
and made available via HTTP or HTTPS protocol.

The Web browser is in charge of searching by parsing an index and download
those files are required by the user.

## Feed files builder

The Python builder scripts are all included into
[transit_feed package](../transit_feed).
The script is designed to be used from inside the main project
[Makefile](../Makefile) by implementing specified [make goals](../transit_feed/feed.mk).

Public [GPRS files](https://developers.google.com/transit/gtfs/) are dawnloaded
from public web sites and then they are eaten by the feed builder implemented
by [transit_feed.feed](https://github.com/pubtransit/transit/blob/master/transit_feed/feed.py)
Python module.

In directory [transit_feed/tests/sample-feed](transit_feed/tests/sample-feed)
you can fin an example of the contend of a
[GPRS Zip file](https://en.wikipedia.org/wiki/General_Transit_Feed_Specification).

<img src="https://cdn.rawgit.com/pubtransit/transit/a17de82243ca018844837265a49c6be9ff826a44/doc/feeds-building.svg" width="60%" align="right">

GPRS files are zip files containing some CSV file. Every CSV is a relational
table. transit_feed package makes uses of [Pandas](http://pandas.pydata.org/)
to open them and then uses [NumPy](http://www.numpy.org/) to make operations
over the big column arrays.

Original table are converted to a stripped version of original one are saved
by column: every column is saved on a separate file.

To make these files easier to digest from the web browser they are stored using
[MessagePack](http://msgpack.org/index.html) format ant then compressed using
[zlib](http://www.zlib.net/).

Two tables (stops and stop_times) are split into sub table each one represent
a rectangular region in the earth, each including data of up to 128 stops.

A [KD-Tree](https://en.wikipedia.org/wiki/K-d_tree) structure is saved
separately to allow the Web browser to look for the files required for the
region the zone is interested in.

## Outer feed file tree

GTFS files are used to generate feed files inside a local folder called build
folder (the build/feed folder from the project root). During deployment operation
this folder is going to be copied and mounted on the web server as 
https://www.pubtransit.org/feed/

Therefore the structure and the content of this directory is the actual REST API
expose to to the web Browser.

Below how the directory tree should look like:

```
feed/
  index/      # The Index column array table
    path.gz   # Array of strings with all knwon
              # <feed_group_name>/<feed_name> entries.
    west.gz   # Array of floats with minimum longitude
              # of all stops of given feed entries
    east.gz   # Array of floats with maximum longitude
              # of all stops of given feed entries
    south.gz  # Array of floats with minimum latitude
              # of all stops of given feed entries
    north.gz  # Array of floats with maximum latitude
              # of all stops of given feed entries

  <feed-group-name>/  # a name of feed group
    <feed-name>/      # a name of feed
        ...  # the file tree for given feed
```

This directory structure reflects the [site.yaml](../site.yaml) file used to
configure building script.

```yaml
feed:
 - name: <feed-group-name>
   url: <root-url-for-given-group>   # Relative path option
   feeds:
     - name: <feed-name>
       path: <relative-GTFS-endpoint-path>.zip  # Relative path option

     - name: <feed-name>
       url: <absolute-GTFS-url>.zip  # Absolute URL option
```

## Mid feed file tree

For every GTFS zip configured in the site.yaml file, the builder script is going to
generate a file tree like this:

```
feed/
  <feed-group-name>/  # a name of feed group
    <feed-name>/      # a name of feed
      routes/         # Routes column array table
        name.gz       # Array of string with the names of the all routes
      trips/          # Trips column array table
        name.gz       # Array of string with the names of the all trips
        route_id.gz   # Array of integer indexes pointing to a row of routes table
      tiles/          # Tiles column array table. A tile is a rectangular group of stops
        west.gz       # Array of floats with minimum longitude
                      # of all stops of given tile
        east.gz       # Array of floats with maximum longitude
                      # of all stops of given tile
        south.gz      # Array of floats with minimum latitude
                      # of all stops of given tile
        north.gz      # Array of floats with maximum latitude
                      # of all stops of given feed entries
        tree.gz       # An tree node object with reference to tile ids as leafs
      <tile-name>/    # The name of a tile is obtained by the integer value of its
                      # integer index
        ... # the file tree for given tile.
```

## Inner feed file tree

Every tile is a group of stops enclosed inside the same rectangle. Because they
are produced as leafs of a KD-Tree there are any intersection between tiles. This
avoid data replication.

The internal content of a tile is stored inside a file tree like below.
```
feed/
  <feed-group-name>/  # a name of feed group
    <feed-name>/      # a name of feed
      <tile-name>/    # The name of a tile is obtained by the integer value of its
                      # integer index
        stops/
          empty.gz    # array of integers used to specify if a stop is
                      # connected to any trip
          lat.gz      # array of floats specifying stops latitude 
          lon.gz      # array of floats specifying stops longitude
          name.gz     # the name of a stop
```

## KD-Tree node object

The [KD-Tree](https://en.wikipedia.org/wiki/K-d_tree) nodes are JSON like
objects cotaining following fields:
- col: {"lat"|"lon"} string value specifying if the split axis
       is along latitude or longitude  
- min: floating point value specifying the minimum longiture or latitude
- mid: floating point value specifying the split axis longiture or latitude
- max: floating point value specifying the maximum axis longiture or latitude
- left: KD-Tree child node object
- right: KD-Tree child node object
- leaf: an integer value that identifying a tile.

## Binary feed files format

Binary feed files .gz are packed using
[msgpack-python](https://pypi.python.org/pypi/msgpack-python) Python library and then
compressed using [zlib](https://docs.python.org/2/library/zlib.html).

They can contain everthing could be stored inside a JSON object file. In most of the
cases are used to store flat uniform arrays of integers, floats or strings.
These could represent a column of a table named after array file folder.

```
feed/
  <...some other dirs>/
    <table-name>/
      <column-array-name>.gz
```
