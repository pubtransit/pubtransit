var model = {
    location: {
        lat: 53.349721,
        lng: -6.260192
    },
    stops: [],

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
