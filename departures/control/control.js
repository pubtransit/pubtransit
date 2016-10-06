function refreshLocation() {
    debug("Get user location...");
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (loc) {
                updateLocation(loc.coords.latitude, loc.coords.longitude)
            },
            error);
    } else {
        error("Geolocation is not supported by your browser.");
    }
}

function updateLocation(lat, lng) {
    if (setLocation(lat, lng)) {
        debug("Set user location: " + JSON.stringify(getLocation()));
        showLocation()
        refreshStops();
    } else {
        debug("Same location.");
    }
}

function refreshStops() {
    loc = getLocation();
    debug("Get nearest bus stops near " + JSON.stringify(loc) + "...");
    performRequest("POST", "get_stops", loc, updateStops);
}

function updateStops(stops) {
    debug("Set bus stops: " + JSON.stringify(stops));
    setStops(stops);
    dropStopMarkers();
}

function refreshBuses(stopIndex) {
    closeBusesWindow();
    if(setCurrentStop(stopIndex)) {
        debug("Refresh current buses: " + JSON.stringify(stopIndex) + "...");
        performRequest(
            "POST", "get_buses", getCurrentStopPosition(), updateBuses);
    }
}

function updateBuses(buses) {
    debug("Update current buses: " + JSON.stringify(buses) + "...");
    setBuses(buses);
    showBusesWindow();
}

function performRequest(method, path, data, listener_function) {
    debug("Perform request: " +
          JSON.stringify([method, path, data]));

    var request = new XMLHttpRequest();
    request.open(method, path);
    request.setRequestHeader('Content-Type', 'application/json');

    function onLoad() {
        rensponse = JSON.parse(request.responseText)
        debug("Got rensponse: " +
              JSON.stringify([method, path, data, rensponse]));
        listener_function(rensponse);
    }

    request.addEventListener('load', onLoad);
    request.send(JSON.stringify(data));
}
