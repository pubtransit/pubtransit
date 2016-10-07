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
    end_poit = "/api/v1/stops?lon=" + loc.lng + "&lat=" + loc.lat + "&r=10000"
    performRequest("GET", end_poit, null, updateStops);
}

function updateStops(rensponse) {
    stops = []

    for (var i = 0; i < rensponse.stops.length; i++) {
        lonLat = rensponse.stops[i].geometry.coordinates
        stops.push({lat: lonLat[1], lng: lonLat[0]})
    }

    if (rensponse.meta.offset == 0) {
        debug("Clear bus stops.");
        clearStops()
    }

    debug("Push bus stops:\n" + JSON.stringify(stops));
    dropStopMarkers(pushStops(stops));
    next_end_point = rensponse.meta.next
    if (next_end_point) {
        performFullRequest("GET", next_end_point, null, updateStops);
    }
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

function performRequest(method, end_point, data, listener_function) {
    path = getTransitUrl(end_point)
    performFullRequest(method, path, data, listener_function)
}

function performFullRequest(method, path, data, listener_function) {
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
