var model = {
    location: {
        lat: 53.349721,
        lng: -6.260192
    },
    stops: [],
    currentStop: -1,
    buses: [],
}

function setLocation(lat, lng) {
    newLoc = {lat: lat, lng: lng}
    oldLoc = model.location
    if (newLoc.lat == oldLoc.lat && newLoc.lng == oldLoc.lng) {
        return false;
    } else {
        model.location = newLoc;
        return true
    }
}

function getLocation() {
    return model.location;
}

function setStops(stops) {
    model.stops = stops
}

function getStops() {
    return model.stops
}

function setCurrentStop(stopIndex) {
    if (stopIndex != model.currentStop) {
        model.currentStop = stopIndex;
        return true
    }
}

function getCurrentStop() {
    return model.currentStop
}

function getCurrentStopPosition() {
    if (model.currentStop >= 0) {
        return model.stops[model.currentStop]
    }
}

function setBuses(buses) {
    model.buses = buses
}

function getBuses() {
    return model.buses
}
