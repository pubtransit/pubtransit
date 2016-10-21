function Feed(conf) {
    this.conf = conf;
    this.cache = {};
}

Feed.prototype.requestStops = function(bounds, receiveStops) {
    log.debug("requestStops:", bounds)
    var self = this;
    this.at().from('index').select(['path', 'west', 'east', 'south', 'north'])
            .fetch(function(index) {
                self.receiveIndex(index, bounds, receiveStops)
            });
}

Feed.prototype.receiveIndex = function(index, bounds, receiveStops) {
    for ( var i in index.path) {
        if (index.west[i] < bounds.east && index.east[i] > bounds.west
                && index.south[i] < bounds.north
                && index.north[i] > bounds.south) {
            this.requestStopTiles(index.path[i], bounds, receiveStops);
        }
    }
}

Feed.prototype.requestStopTiles = function(path, bounds, receiveStops) {
    log.debug("requestStopTiles:", path, bounds, receiveStops)
    var self = this;
    this.at(path).from('tree').select('*').fetch(function(tree) {
        self.receiveTree(tree, bounds, receiveStops);
    });
}

Feed.prototype.receiveTree = function(tree, bounds, receiveStops) {
    log.debug('Tree received:', tree)
}

Feed.prototype.at = function(path) {
    if (path) {
        var url = this.conf[0].url + '/' + path;
    } else {
        var url = this.conf[0].url;
    }
    log.debug('At:', url)
    return new FeedRequest(url, this.cache);
}

// ----------------------------------------------------------------------------

function FeedRequest(url, cache) {
    this.url = url;
    this.cache = cache;
    this.table = null;
    this.requests = {};
    this.responses = {};
    this.receiveFunc = null;
    this.done = true;
}

FeedRequest.prototype.from = function(table) {
    this.table = table;
    return this;
}

FeedRequest.prototype.select = function(columns) {
    if (!this.from) {
        throw new Error('Unspecified table name.');
    }
    if (columns == '*') {
        var url = this.url + '/' + this.table + '.gz';
        log.debug("Select object from:", url);
        this.requests['*'] = url;
    } else {
        for ( var i in columns) {
            var column = columns[i];
            var url = this.url + '/' + this.table + '.' + column + '.gz';
            log.debug("Select column '" + column + "' from:", url);
            this.requests[column] = url;
        }
    }

    return this;
}

FeedRequest.prototype.fetch = function(receiveFunc) {
    this.receiveFunc = receiveFunc;
    this.update();
    if (!this.done) {
        for ( var name in this.requests) {
            if (!(name in this.responses)) {
                this.requestColumn(name, this.requests[name])
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

    log.debug('Invoke callback function:', this.receiveFunc)
    this.done = true;
    this.receiveFunc(this.responses);
}

FeedRequest.prototype.requestColumn = function(name, url) {
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
