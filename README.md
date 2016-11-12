# Project PubTransit.org (source code)

[www.pubtransit.org](https://www.pubtransit.org) is a web page that allow to
see the scheduled departure time of public transport around.
All the code used to deploy the web page and the HTML/Javascript are hosted
here.

## CI Status
[![Build Status](https://travis-ci.org/FedericoRessi/pubtransit.svg?branch=rename-package)](https://travis-ci.org/FedericoRessi/pubtransit)
[![Coverage Status](https://coveralls.io/repos/github/FedericoRessi/pubtransit/badge.svg?branch=rename-package)](https://coveralls.io/github/FedericoRessi/pubtransit?branch=rename-package)


## Where to report problems

If you have some problem with the web site please report a [new issue](https://github.com/pubtransit/transit/issues/new).

## Documentation
- [Setup Guide](doc/setup.md)
- [Backend System Achitecture Design](doc/backend-architecture.md)
- [Frontend System Achitecture Design](doc/frontend-architecture.md)

## Features

### Back-end
- Download and read [GPRS Zip feed files](https://en.wikipedia.org/wiki/General_Transit_Feed_Specification).
- Split Zip files and generate small compressed GZ files readable from the Web
  browser.
- Build a [KD-Tree](https://en.wikipedia.org/wiki/K-d_tree) to split divide
  stops feeds into rectangular areas.
- Generate target HTML parsing [jinja](http://jinja.pocoo.org/) templates.
- Tiny flask application to test web page.
- Deploy feed files and HTML data to target web site using
  [Ansible](https://www.ansible.com/)(ssh+rsync).

### Front-end
- Decompress and read feed files from the Web site.
- Parse [KD-Tree](https://en.wikipedia.org/wiki/K-d_tree) to obtain the name of
  the files for the local rectangular area.
- Download missing data when navigating to new zones.
- Show stop location and put pin marks on top of
  [GoogleMap](https://developers.google.com/maps/) for near stops.
- Show departures times of clicked stop.

### Development tools
- [Tox](https://tox.readthedocs.io/en/latest/) configuration file to validate
  back-end Python code.
- [Vagrant](https://www.vagrantup.com/) Ruby script provided to create VBox
  virtual machine almost as identical to target Web site.

## Know issues & missing feature
- [#2](https://github.com/pubtransit/transit/issues/2) Remaining time computation doesn't care about time zones.
- [#3](https://github.com/pubtransit/transit/issues/3) It doesn't read calendar table from feed files.
- [#4](https://github.com/pubtransit/transit/issues/4) Stop times feed file building is slow for big GPRS files.
- It doesn't provide any real time data, only scheduled departures times.
