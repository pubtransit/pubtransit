var view = null;

function setView(_view) {
    view = _view;
    getLocation();
}

function setMessage(message) {
    console.log(message);
    // view.message.innerHTML = message;
}

function setError(message) {
    console.log(message);
    // view.message.innerHTML = message;
}

function getLocation() {
    setMessage("Getting your location...");
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            setLocation, setError);
    } else {
        setError("Geolocation is not supported by your browser.");
    }
}

function setLocation(location) {
    // view.location.innerHTML = JSON.stringify(location);
    setMessage("Got your location: " + JSON.stringify(location));
    getStops(location);
}

function getStops(location) {
    setMessage("Getting neares bus stops...");

    var request = new XMLHttpRequest();
    request.open('POST', "control/get_stops");
    request.setRequestHeader('Content-Type', 'application/json');
    request.addEventListener('load',  function () {
        setBusStops(JSON.parse(request.responseText));
    });
    request.send(JSON.stringify({
        latitude: location.coords.latitude,
        longitude: location.coords.longitude
    }));
}

function setBusStops(stops) {
    setMessage("Got bus stops: " + JSON.stringify(stops));
}
