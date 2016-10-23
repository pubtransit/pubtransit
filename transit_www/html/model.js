
function Model() {
    this.bounds = {
        south: 52.66449765057875,
        north: 52.66449765057875,
        east: -8.632234899999958,
        west: -8.632234899999958,
    };
    this.stops = {};
    this.currentStop = null;
    this.transit = {{ transit }};
    this.feed = {{ feed }};
    this.zoom = 15;
    this.routes = {};
    this.trips = {};
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

Model.prototype.putStop = function(stop) {
    if (!(stop.stopId in this.stops)) {
        this.stops[stop.stopId] = stop;
    }
}

Model.prototype.setCurrentStop = function(stopId) {
    if (stopId != this.currentStop) {
        this.currentStop = stopId;
        return true;
    }
}

Model.prototype.getCurrentStop = function() {
    return this.stops[this.currentStop];
}

Model.prototype.putStopTime = function(stopTime) {
    this.stops[stopTime.stopId].times[stopTime.stopTimeId] = stopTime;
}

Model.prototype.putRoute = function(route) {
    if(route.routeId in this.routes) {
        for(key in route) {
            this.routes[route.routeId][key] = route[key];
        }
    } else {
        this.routes[route.routeId] = route;
    }
}

Model.prototype.putTrip = function(trip) {
    if(trip.tripId in this.trips) {
        for(key in trip) {
            this.trips[trip.tripId][key] = trip[key];
        }
    } else {
        this.trips[trip.tripId] = trip;
    }
}

Model.prototype.getCurrentStopTimes = function() {
    var stopTimes = [];
    var stop = this.getCurrentStop();
    for (var i in stop.times) {
        stopTimes.push(stop.times[i]);
    }

    return stopTimes;
}
