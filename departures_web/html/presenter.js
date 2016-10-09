
function Presenter(view, model) {
    this.model = model;
    this.view = view;
    this.transit = new TransitClient(model.transit);
    this._stopRequested = false;
    this._updateCurrentStopRequested = false;
}

Presenter.prototype.centerCurrentPosition = function() {
    if (navigator.geolocation) {
        var self = this;
        log.debug("Get user position...");
        navigator.geolocation.getCurrentPosition(
            function (position) {
                self.view.centerPosition({
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

Presenter.prototype.setBounds = function(bounds) {
    if (this.model.setBounds(bounds)) {
        if (this.model.zoom > 13) {
            log.debug("Set bounds:", this.model.bounds);
            if (!this._stopRequested) {
                this._stopRequested = true;
                self = this;
                window.setTimeout(function() {self.requestStops()}, 500.);
            }
        }
        this.view.updateCenter();
    } else {
        log.debug("Same location.");
    }
}

Presenter.prototype.setZoom = function(zoom) {
    this.model.setZoom(zoom);
    this.view.updateZoom(zoom);
}

Presenter.prototype.requestStops = function() {
    log.debug("Get stops:", this.model.bounds);
    var self = this;
    this.transit.requestStops(
        this.model.bounds,
        function(stops) {self.receiveStops(stops)}
    ).send();
    this._stopRequested = false;
}

Presenter.prototype.receiveStops = function(stops) {
    for (var i in stops) {
        var stopEntry = stops[i];
        // log.debug("Parse bus stop:", stopEntry);

        var routes = [];
        for(j in stopEntry.routes_serving_stop) {
            var routeEntry = stopEntry.routes_serving_stop[j];
            route = {
                routeId: routeEntry.route_onestop_id,
                name: routeEntry.route_name
            }
            this.model.pushRoute(route);
            routes.push(route.routeId);
        }

        var stopId = stopEntry.onestop_id;
        var lonLat = stopEntry.geometry.coordinates;
        var stop = {
            stopId: stopId,
            lat: lonLat[1],
            lng: lonLat[0],
            name: stops[i].name,
            routes: routes,
        };
        this.model.pushStop(stop);
        this.view.dropStopMarker(stopId);
    }
}

Presenter.prototype.setCurrentStop = function(stopId) {
    if(this.model.setCurrentStop(stopId)) {
        if(stopId) {
            this.requestBuses();
            this.requestRoutes();
            this.updateCurrentStop();
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
        var now = new Date();
        var timeParts = buses[i].origin_arrival_time.split(':');
        var time = new Date();
        time.setHours(timeParts[0]);
        time.setMinutes(timeParts[1]);
        time.setSeconds(timeParts[2]);
        var deltaTime = time - now;
        if (deltaTime < 0) {
            // increment the time by one day
            time.setDate(time.getDate() + 1);
            deltaTime = time - now;
        }
        var hasService = buses[i].service_days_of_week[time.getDay()];
        if (hasService) {
            var bus = {
                routeId: buses[i].route_onestop_id,
                destinationId: buses[i].destination_onestop_id,
                time: time,
                deltaTime: deltaTime,
            };
            log.debug("Update current buses:", bus);
            this.model.pushBus(bus);
        }
    }
    this.model.sortBuses();
    this.updateCurrentStop();
}

Presenter.prototype.requestRoutes = function(stopId) {
    log.debug("Get routes:", stopId);
    var self = this;
    this.transit.requestRoutes(
        this.model.currentStop,
        function(routes) {self.receiveRoutes(routes)}
    ).send();
}

Presenter.prototype.receiveRoutes = function(routes) {
    var routeIds = [];
    for (var i in routes) {
        var routeEntry = routes[i];
        log.debug("Parse bus route:", routeEntry);

        var stops = [];
        for(i in routeEntry.stop_pattern) {
            stops.push(routeEntry.stop_pattern[i])
        }
        var route = {
            routeId: routeEntry.route_onestop_id,
            stops: stops
        }
        routeIds.push(routeEntry.route_onestop_id);
        this.model.pushRoute(route);
    }
    if(routeIds && routeIds.length > 0) {
        this.requestRouteStops(routeIds);
    }
    this.updateCurrentStop();
}

Presenter.prototype.updateCurrentStop = function(routes) {
    if(this.model.currentStop && !this._updateCurrentStopRequested) {
        this._updateCurrentStopRequested = true;
        var self = this;
        window.setTimeout(
            function() {
                self._updateCurrentStopRequested = false;
                if(self.model.currentStop) {
                    self.view.updateCurrentStop();
                    self.updateCurrentStop();
                }
            },
            1000
        );
    } else {
        this._updateCurrentStopRequested = false;
    }
}

Presenter.prototype.requestRouteStops = function(routeIds) {
    log.debug("Get stops for routes:", this.model.bounds);
    var self = this;
    this.transit.requestRouteStops(
        routeIds,
        function(stops) {self.receiveStops(stops)}
    ).send();
}
