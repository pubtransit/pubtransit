
function Presenter(view, model) {
    this.model = model;
    this.view = view;
    this.transit = new TransitClient(model.transit);
    this._stopRequested = false;
}

Presenter.prototype.centerCurrentPosition = function() {
    if (navigator.geolocation) {
        var presenter = this;
        log.debug("Get user position...");
        navigator.geolocation.getCurrentPosition(
            function (position) {
                presenter.setPosition({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                });
            },
            log.error
        );
    } else {
        log.error("Geolocation is not supported by your browser.");
    }
}

Presenter.prototype.setPosition = function(position) {
    if (this.model.setPosition(position)) {
        log.debug("Center user position:", this.model.position);
        this.view.updatePosition();
        if (!this._stopRequested) {
            this._stopRequested = true;
            self = this;
            window.setTimeout(function() {self.requestStops()}, 500.);
        }
    } else {
        log.debug("Same location.");
    }
}

Presenter.prototype.setRadius = function(radius) {
    if (this.model.setRadius(radius)) {
        log.debug("Set user radius:", this.model.radius);
        this.view.updateRadius();
        if (!this._stopRequested) {
            this._stopRequested = true;
            self = this;
            window.setTimeout(function() {self.requestStops()}, 500.);
        }
    } else {
        log.debug("Same radius.");
    }
}

Presenter.prototype.requestStops = function() {
    this._stopRequested = false;

    if (this.model.radius <= 1000.){
        log.debug("Get stops:", this.model.position, this.model.radius);
        var self = this;
        this.transit.requestStops(
            this.model.position, this.model.radius,
            function(stops) {self.receiveStops(stops)}
        ).send();
    } else {
        log.debug("Don't get stops for radius bigger than 1Km.");
    }
}

Presenter.prototype.receiveStops = function(stops) {
    for (var i in stops) {
        log.debug("Parse bus stop:", stops[i]);
        var stoId = stops[i].onestop_id;
        var lonLat = stops[i].geometry.coordinates;
        var stop = {
            stopId: stoId,
            lat: lonLat[1],
            lng: lonLat[0],
            name: stops[i].name,
        };
        this.model.pushStop(stop);
        this.view.dropStopMarker(stoId);
    }
}

Presenter.prototype.setCurrentStop = function(stopId) {
    if(this.model.setCurrentStop(stopId)) {
        if(stopId) {
            this.requestBuses();
            this.view.updateCurrentStop();
        }
    }
}

Presenter.prototype.requestBuses = function(stopId) {
    log.debug("Get buses:", stopId);
    var self = this;
    this.transit.requestBuses(
        this.model.currentStop,
        function(buses) {self.receiveBuses(buses)}
    ).send();
}

Presenter.prototype.receiveBuses = function(buses) {
    for (var i in buses) {
        var time = buses[i].origin_arrival_time.split(':')
        var bus = {
            routeId: buses[i].route_onestop_id,
            destinationId: buses[i].destination_onestop_id,
            time: [parseInt(time[0]), parseInt(time[1]), parseInt(time[2])]
        };
        log.debug("Update current buses:", bus);
        this.model.pushBus(bus);
        this.model.pushRequiredStop(bus.destinationId);
    }
    this.model.sortBuses();
    this.view.updateCurrentStop();
}
