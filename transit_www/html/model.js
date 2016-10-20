
function Model() {
    this.bounds = {
        south: 52.66449765057875,
        north: 52.66449765057875,
        east: -8.632234899999958,
        west: -8.632234899999958,
    };
    this.stops = {};
    this.currentStop = null;
    this.buses = [];
    this.transit = {{ transit }};
    this.feed = {{ feed }};
    this.zoom = 15;
    this.routes = {};
}

Model.prototype.setBounds = function(bounds) {
    if (
        this.bounds.east == bounds.east &&
        this.bounds.north == bounds.north &&
        this.bounds.west == bounds.west &&
        this.bounds.south == bounds.south
    ) {
        return false;
    } else {
        this.bounds = bounds;
        return true
    }
}

Model.prototype.getCenter = function() {
    return {
        lat: (this.bounds.south + this.bounds.north) * 0.5,
        lng: (this.bounds.east + this.bounds.west) * 0.5
    }
}

Model.prototype.setZoom = function(zoom) {
    this.zoom = zoom
}

Model.prototype.pushStop = function(stop) {
    var stopId = stop.stopId;
    this.stops[stop.stopId] = stop;
}

Model.prototype.setCurrentStop = function(stopId) {
    if (stopId != this.currentStop) {
        this.currentStop = stopId;
        this.buses = [];
        return true;
    }
}

Model.prototype.getCurrentStop = function() {
    return this.stops[this.currentStop];
}

Model.prototype.pushBus = function(bus) {
    this.buses.push(bus);
}

Model.prototype.sortBuses = function() {
    this.buses.sort(
        function(bus1, bus2) {
            return bus1.time - bus2.time;
        }
    );
}

Model.prototype.pushRoute = function(route) {
    var routeId = route.routeId;
    if(route.routeId in this.routes) {
        for(key in route) {
            this.routes[route.routeId][key] = route[key];
        }
    } else {
        this.routes[route.routeId] = route;
    }
}
