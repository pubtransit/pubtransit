var model = {
    location: {
        latitude: 53.349721,
        longitude: -6.260192
    },
    stops: [],
}

function getLocation() {
    debug("Get user location...");
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(setLocation, error);
    } else {
        error("Geolocation is not supported by your browser.");
        setLocation(null)
    }
}

function setLocation(location) {
    if (location) {
        model.location = {
            longitude: location.coords.longitude,
            latitude: location.coords.latitude
        }
    }
    debug("Set user location: " + JSON.stringify(model.location));
    getStops(model.location);
}

function getStops(location) {
    debug("Get nearest bus stops near (" +
            JSON.stringify(location.latitude) + ", " +
            JSON.stringify(location.longitude) + ")...");

    var request = new XMLHttpRequest();
    request.open('POST', "get_stops");
    request.setRequestHeader('Content-Type', 'application/json');
    request.addEventListener('load',  function () {
        setBusStops(JSON.parse(request.responseText));
    });
    request.send(JSON.stringify(location));
}

function setBusStops(stops) {
    debug("Set bus stops: " + JSON.stringify(stops));
    model.stops = stops
}
