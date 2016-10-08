
function Presenter(view, model) {
    this.model = model;
    this.view = view;
    this.transit = new TransitClient(model.transit);
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
        this.view.centerPosition();
        this.requestStops();
    } else {
        log.debug("Same location.");
    }
}

Presenter.prototype.setRadius = function(radius) {
    if (this.model.setRadius(radius)) {
        log.debug("Set user radius:", this.model.radius);
        // this.view.setZoom();
        this.requestStops();
    } else {
        log.debug("Same radius.");
    }
}

Presenter.prototype.requestStops = function() {
    log.debug("Get stops:", this.model.position, this.model.radius);
    var self = this;
    this.transit.requestStops(
        this.model.position, this.model.radius,
        function(stops) {self.receiveStops(stops)
    }).send();
}

Presenter.prototype.receiveStops = function(stops) {
    for (var i in stops) {
        // log.debug("Parse bus stop:", stops[i]);
        var lonLat = stops[i].geometry.coordinates;
        var stop = {
            stopId: lonLat.join(','),
            lat: lonLat[1],
            lng: lonLat[0],
            name: stops[i].name,
        };
        this.model.pushStop(stop);
        this.view.dropStopMarker(stop);
    }
}

Presenter.prototype.refreshBuses = function(stopIndex) {
    closeBusesWindow();
    if(setCurrentStop(stopIndex)) {
        debug("Refresh current buses: " + JSON.stringify(stopIndex) + "...");
        performRequest(
            "POST", "get_buses", getCurrentStopPosition(), updateBuses);
    }
}

Presenter.prototype.updateBuses = function(buses) {
    debug("Update current buses: " + JSON.stringify(buses) + "...");
    setBuses(buses);
    showBusesWindow();
}
