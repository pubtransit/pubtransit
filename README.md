# Project PubTransit.org (source code)

[www.pubtransit.org](https://www.pubtransit.org) is a web page that allow to see te scheduled departure time of pubblic trasps around you.
All the code used to deploy the web page and the HTML/Javascript are hosted here.

## Where to report problems

If you have some problem with the web site please report a [new issue](https://github.com/pubtransit/transit/issues/new).

## Documentation
- [System Achitecture Design](doc/architecture.md)
- [Setup Guide](doc/setup.md)

## Features

### Back-end
- Download GPRS Zip files
- Read Zip files and split to smaller compressed GZ files readable from the Web Browser.
- Build KD-Tree to split divide stops feeds into rectangular areas.
- Create filal HTML parsing jinja templates.
- Tiny flask application to test web page.
- Deploy feed files and HTML data to target web site (using ssh+rsync).

### Front-end
- Decompress and read feed files from the Web site.
- Parse KDTree to obtain the name of the files for the local rectangular area.
- Download missing data when navigating to new zones.
- Swow stop location as pins on top of GoogleMap.
- Show departures times of clicked stop.

### Development tools
- Tox configuration file to validate back-end Python code.
- Vagrantfile provided to create VBox virtual machine almost as identical to target web site.

## Know issues / missing feature
- Remaining time computation doesn't care about time zones.
- It doesn't provide any real time data, only scheduled departures times.
