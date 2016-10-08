
function Model() {
    this.position = {lat: 56.163357, lng: 10.216666};
    this.radius = 500;
    this.requiredStops = {};
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
        return true;
    }
}

Model.prototype.pushStop = function(stop) {
    var stopId = stop.stopId;
    delete this.requiredStops[stopId];
    this.stops[stop.stopId] = stop;
}

Model.prototype.pushRequiredStop = function(stopId) {
    if (!(stopId in this.stops)){
        this.requiredStops[stopId] = true;
    }
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
            var time1 = bus1.time;
            var time2 = bus2.time;
            for (var i = 0; i < 3; i++) {
                var delta = time1[i] - time2[i];
                if(delta != 0) {
                    return delta;
                }
            }
            return 0;
        }
    );
}
