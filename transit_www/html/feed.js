function Feed(conf) {
    this.conf = conf;
}

Feed.prototype.requestStops = function(bounds, receiveStops) {
    log.debug("requestStops:", bounds)
    var self = this;
    this.from('index').select(['path', 'west', 'east', 'south', 'north'])
            .fetch(function(index) {
                self.selectStops(index, bounds, receiveStops)
            });
}

Feed.prototype.selectStops = function(index, bounds, receiveStops) {
    log.debug("TODO: selectStops:", index, bounds);
}

Feed.prototype.from = function(table) {
    return new FeedRequest(this.conf[0].url).from(table);
}

function FeedRequest(url) {
    this.url = url;
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

    for (i in columns) {
        var column = columns[i];
        var url = this.url + this.table + '.' + column + '.gz';
        log.debug("Select '" + column + "' from:", url);
        this.requests[column] = url;
    }
    return this;
}

FeedRequest.prototype.fetch = function(receiveFunc) {
    this.receiveFunc = receiveFunc;
    this.update();
    if (!this.done) {
        for (name in this.requests) {
            if (!(name in this.responses)) {
                this.fetch_column(name, this.requests[name])
            }
        }
    }
    return this;
}

FeedRequest.prototype.fetch_column = function(name, url) {
    log.debug("Fetch '" + name + "' from: ", url)
    var self = this;
    var request = new XMLHttpRequest();
    request.open("GET", url, true);
    request.responseType = 'arraybuffer';
    request.setRequestHeader('Content-Type', 'application/gzip');
    request.addEventListener('load', function() {
        self.receiveRensponse(name, request);
    });
    request.send();
}

FeedRequest.prototype.update = function(name, request) {
    for (name in this.requests) {
        if (!(name in this.responses)) {
            // TODO Get from local storage here
            this.done = false;
            return;
        }
    }

    log.debug('Invoke callback function:', this.receiveFunc)
    this.receiveFunc(this.responses);
    this.done = true;
}

FeedRequest.prototype.receiveRensponse = function(name, request) {
    try {
        if (request.status != 200) {
            throw new Error("invalid request: " + request.status);
        }

        response = new Uint8Array(request.response)
        log.debug("Received response for " + name + "'.")
        var compressed = response;
        var packed = pako.inflate(compressed);
        var decoded = msgpack.decode(packed);
        this.responses[name] = decoded;
        // TODO Update local storage here
    } catch (error) {
        log.error("Error getting rensponse for '" + name + "':",
                error.message);
        throw error;
    } finally {
        this.update();
    }
}
