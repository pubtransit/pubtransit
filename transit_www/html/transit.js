function TransitClient(conf) {
    this.conf = conf;
    this.stopRequest = null;
    this.busRequest = null;
    this.routeRequres = null;
}

TransitClient.prototype.requestStops = function(
        bounds, receiveStops) {
    var request = this.stopRequest;
    if (request) {
        request.stop();
    }
    this.stopRequest = request = new TransitRequest(
        this.getUrl("/api/v1/stops"), {
            bbox: [bounds.west, bounds.south,
                   bounds.east, bounds.north].join(',')
        }
    );
    request.onRensponse = function (response) {
        receiveStops(response.stops);
    }
    return request;
}

TransitClient.prototype.requestBuses = function(
        stopId, receiveBuses) {
    var request = this.busRequest;
    if (request) {
        request.stop();
    }

    this.busRequest = request = new TransitRequest(
        this.getUrl("/api/v1/schedule_stop_pairs"),
        {origin_onestop_id: stopId}
    );
    request.onRensponse = function (response) {
        receiveBuses(response.schedule_stop_pairs);
    }
    return request;
}

TransitClient.prototype.requestRoutes = function(
        stopId, receiveRoutes) {
    var request = this.routeRequest;
    if (request) {
        request.stop();
    }

    this.routeRequest = request = new TransitRequest(
        this.getUrl("/api/v1/route_stop_patterns"),
        {stops_visited: stopId}
    );
    request.onRensponse = function (response) {
        receiveRoutes(response.route_stop_patterns);
    }
    return request;
}

TransitClient.prototype.requestRouteStops = function(
        routeIds, receiveStops) {
    var request = this.stopRequest;
    if (request) {
        request.stop();
    }

    this.stopRequest = request = new TransitRequest(
        this.getUrl("/api/v1/stops"), {
            served_by: routeIds.join(',')
        }
    );
    request.onRensponse = function (response) {
        receiveStops(response.stops);
    }
    return request;
}


TransitClient.prototype.getUrl = function(endPoint) {
    return this.conf[0].url + '/' + endPoint
}

// ----------------------------------------------------------------------------

function TransitRequest(url, parameters) {
    this.url = url;
    this.done = false;
    this._request = null;
    this._responses = [];
    var args = [];
    for(var name in parameters) {
        args.push(
            encodeURIComponent(name) + "=" +
            encodeURIComponent(parameters[name])
        );
    }
    if(args.length > 0){
        url += "?" + args.join('&');
    }

    this.url = url;
    this.done = false;
    this._responses = [];
}

TransitRequest.prototype.onRensponse = function(response){
}

TransitRequest.prototype.onDone = function(responses){
}

TransitRequest.prototype.stop = function() {
    if(!this.done) {
        this.done = true;
        this.onDone(this._responses);
    }
}

TransitRequest.prototype.send = function() {
    var request = new XMLHttpRequest();
    var self = this;
    this._request = request;
    log.debug("Send request:", this.url)
    request.open("GET", this.url);
    request.setRequestHeader('Content-Type', 'application/json');
    request.addEventListener(
        'load', function() {self.parseRensponse(request)}
    );
    request.send();
}

TransitRequest.prototype.parseRensponse = function(request) {
    var response = JSON.parse(request.responseText);
    this._responses.push(response);
    this.onRensponse(response);
    if(!this.done){
        var next = response.meta.next;
        if(request == this._request && next) {
            this.url = response.meta.next;
            this.send();
        } else {
            this.stop();
        }
    }
}
