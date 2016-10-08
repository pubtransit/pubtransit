function TransitClient(conf) {
    this.conf = conf;
    this.stopRequest = null;
}

TransitClient.prototype.requestStops = function(
        position, radius, receiveStops) {
    var request = this.stopRequest;
    if (request) {
        request.stop();
    } 
    this.stopRequest = request = new TransitRequest(
        this.getUrl("/api/v1/stops"),
        {lon: position.lng, lat: position.lat, r: radius}
    );
    request.onRensponse = function (response) {receiveStops(response.stops);}
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
    if(!this.done && request == this._request) {
        var response = JSON.parse(request.responseText );
        this._responses.push(response);
        this.onRensponse(response);
        var next = response.meta.next;
        if(next) {
            this.url = response.meta.next;
            this.send();
        } else {
            this.stop();
        }
    } else {
        log.debug("Throw away response:", request);
    }
}
