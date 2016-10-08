
function Model() {
    this.position = {lat: 53.349721, lng: -6.260192};
    this.radius = 1000;
    this.stops = {};
    this.currentStop = null;
    this.buses = [];
    this.transit = {{ transit }};
}

Model.prototype.setPosition = function(position) {
    if (this.position.lat == position.lat &&
        this.position.lng == position.lng) {
        return false;
    } else {
        this.position = position;
        return true
    }
}

Model.prototype.setRadius = function(radius) {
    if (this.radius == radius) {
        return false;
    } else {
        this.radius = radius;
        return true
    }
}

Model.prototype.pushStop = function(stop) {
    this.stops[stop.stopId] = stop;
}

Model.prototype.setCurrentStop = function(stopId) {
    if (stopId != this.currentStop) {
        this.currentStop = stopId;
        return true
    }
}

Model.prototype.getCurrentStop = function() {
    return this.stops[this.currentStop];
}
