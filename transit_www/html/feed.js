function FeedClient(conf, handler) {
    this.conf = conf;
    this.handler = handler;
    this.cache = {};
}

FeedClient.prototype.requestStops = function(bounds) {
    log.debug("requestStops:", bounds)
    var self = this;
    this.from('index').select(['path', 'west', 'east', 'south', 'north'])
            .fetch(function(index) {
                self.receiveIndex(index, bounds);
            });
}

FeedClient.prototype.receiveIndex = function(index, bounds) {
    for ( var i in index.path) {
        if (index.west[i] < bounds.east && index.east[i] > bounds.west
                && index.south[i] < bounds.north
                && index.north[i] > bounds.south) {
            this.requestTiles(index.path[i], bounds);
        }
    }
}

FeedClient.prototype.requestTiles = function(path, bounds) {
    log.debug("requestStopTiles:", path, bounds)
    var self = this;
    this.from(path + '/tiles').select(
            ['tree', 'west', 'east', 'south', 'north']).fetch(function(tiles) {
        self.receiveTiles(path, tiles, bounds);
    });
}

FeedClient.prototype.receiveTiles = function(path, tiles, bounds) {
    var nameLength = ("" + tiles.west.length).length;
    var stack = [tiles.tree];
    log.debug('receiveTiles:', path, bounds.west, bounds.east, bounds.south,
            bounds.north);
    while (stack.length > 0) {
        var node = stack.pop();
        if (Number.isInteger(node.leaf)) {
            // Leaf node
            if (tiles.west[node.leaf] <= bounds.east
                    && tiles.east[node.leaf] >= bounds.west
                    && tiles.south[node.leaf] <= bounds.north
                    && tiles.north[node.leaf] >= bounds.south) {
                var tileName = this.getTileName(node.leaf, nameLength);
                this.requestTileStops(path, tileName);
            }
        }
        if (node.left) {
            // Left node
            // log.debug('Left node:', node.col, node.min, node.mid);
            if (node.col == 'lon' && node.min <= bounds.east
                    && node.mid >= bounds.west) {
                stack.push(node.left);
            } else if (node.col == 'lat' && node.min <= bounds.north
                    && node.mid >= bounds.south) {
                stack.push(node.left);
            }
        }
        if (node.right) {
            // Right node
            // log.debug('Right node:', node.col, node.mid, node.max);
            if (node.col == 'lon' && node.mid <= bounds.east
                    && node.max >= bounds.west) {
                stack.push(node.right);
            } else if (node.col == 'lat' && node.mid <= bounds.north
                    && node.max >= bounds.south) {
                stack.push(node.right);
            }
        }
    }
}

FeedClient.prototype.requestTileStops = function(path, tileName) {
    log.debug("requestStopTiles:", path)
    var self = this;
    this.from(path + '/' + tileName + '/stops').select(
            ['lon', 'lat', 'name', 'empty']).fetch(function(stops) {
        self.receiveTileStops(stops, path, tileName);
    });
}

FeedClient.prototype.receiveTileStops = function(stops, path, tileName) {
    log.debug("receiveTileStops:", path)
    var outputStops = [];
    for ( var i in stops.name) {
        if (!stops.empty[i]) {
            outputStops.push({
                stopId: path + '/' + tileName + '#' + i,
                path: path,
                tileName: tileName,
                tileStopId: i,
                lat: stops.lat[i],
                lng: stops.lon[i],
                name: stops.name[i],
                times: {},
            });
        }
    }
    this.handler.receiveStops(outputStops);
}

FeedClient.prototype.requestRoutes = function(stop) {
    var self = this;
    this.from(stop.path + '/routes').select(['name']).fetch(function(routes) {
        self.receiveRoutes(routes, stop.path);
    })
}

FeedClient.prototype.receiveRoutes = function(routes, path) {
    log.debug('Receive routes.');
    outputRoutes = [];
    for ( var i in routes.name) {
        outputRoutes.push({
            name: routes.name[i],
            routeId: path + '#' + i,
        });
    }
    this.handler.receiveRoutes(outputRoutes);
}

FeedClient.prototype.requestTrips = function(stop) {
    var self = this;
    this.from(stop.path + '/trips').select(['name', 'route_id']).fetch(
            function(trips) {
                self.receiveTrips(trips, stop.path);
            });
}

FeedClient.prototype.receiveTrips = function(trips, path) {
    log.debug('Receive trips.');
    outputTrips = [];
    for ( var i in trips.name) {
        outputTrips.push({
            name: trips.name[i],
            tripId: path + '#' + i,
            routeId: path + '#' + trips.route_id[i],
        });
    }
    this.handler.receiveTrips(outputTrips);
}

FeedClient.prototype.requestStopTimes = function(stop) {
    var self = this;
    this.from(stop.path + '/' + stop.tileName + '/stop_times').select(
            ['departure_minutes', 'stop_id', 'trip_id']).fetch(
            function(stop_times) {
                self.receiveStopTimes(stop_times, stop);
            });
}

FeedClient.prototype.receiveStopTimes = function(stopTimes, stop) {
    log.debug('Receive stop times.');
    outputStopTimes = [];
    for ( var i in stopTimes.stop_id) {
        outputStopTimes.push({
            stopTimeId: stop.path + '/' + stop.tileName + '#' + i,
            stopId: stop.path + '/' + stop.tileName + '#'
                    + stopTimes.stop_id[i],
            tripId: stop.path + '#' + stopTimes.trip_id[i],
            departureMinutes: stopTimes.departure_minutes[i],
        });
    }
    this.handler.receiveStopTimes(outputStopTimes);
}

FeedClient.prototype.from = function(path) {
    return new FeedRequest(this.conf[0].url, this.cache).from(path);
}

FeedClient.prototype.getTileName = function(tileId, length) {
    var name = "" + tileId;
    while (name.length < length) {
        name = "0" + name;
    }
    return name;
}

// ----------------------------------------------------------------------------

function FeedRequest(url, cache) {
    this.url = url;
    this.cache = cache;
    this.path = null;
    this.requests = {};
    this.responses = {};
    this.receiveFunc = null;
    this.done = true;
}

FeedRequest.prototype.from = function(path) {
    this.path = path;
    return this;
}

FeedRequest.prototype.select = function(names) {
    if (!this.path) {
        throw new Error('Unspecified path.');
    }
    for ( var i in names) {
        var name = names[i];
        var url = this.url + '/' + this.path + '/' + name + '.gz';
        log.debug("Select object '" + name + "' from:", url);
        this.requests[name] = url;
    }

    return this;
}

FeedRequest.prototype.fetch = function(receiveFunc) {
    this.receiveFunc = receiveFunc;
    this.update();
    if (!this.done) {
        for ( var name in this.requests) {
            if (!(name in this.responses)) {
                this.request(name, this.requests[name])
            }
        }
    }
    return this;
}

FeedRequest.prototype.update = function() {
    for ( var name in this.requests) {
        if (!(name in this.responses)) {
            cached = this.cache[this.requests[name]]
            if (cached) {
                this.responses[name] = cached;
            } else {
                this.done = false;
                return;
            }
        }
    }

    this.done = true;
    this.receiveFunc(this.responses);
}

FeedRequest.prototype.request = function(name, url) {
    log.debug("Fetch '" + name + "' from: ", url)
    var self = this;
    var request = new XMLHttpRequest();
    request.open("GET", url, true);
    request.responseType = 'arraybuffer';
    request.setRequestHeader('Content-Type', 'application/gzip');
    request.addEventListener('load', function() {
        if (request.status != 200) {
            log.error("Unable to request column:", name, url, request.status);
        } else {
            self.receiveResponse(name, url, new Uint8Array(request.response));
        }
    });
    request.send();
}

FeedRequest.prototype.receiveResponse = function(name, url, response) {
    try {
        log.debug("Received response for '" + name + "'.")
        var packed = pako.inflate(response);
        var decoded = msgpack.decode(packed);
        this.responses[name] = decoded;
        this.cache[url] = decoded;
    } catch (error) {
        log
                .error("Error getting rensponse for '" + name + "':",
                        error.message);
        throw error;
    } finally {
        this.update();
    }
}
