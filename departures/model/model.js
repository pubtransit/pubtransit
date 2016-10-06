var model = {
    location: {
        lat: 53.349721,
        lon: -6.260192
    },
    stops: [],

}

function setLocation(lat, lon) {
    newLoc = {lat: lat, lon: lon}
    oldLoc = model.location
    if (newLoc.lat == oldLoc.lat && newLoc.lon == oldLoc.lon) {
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
